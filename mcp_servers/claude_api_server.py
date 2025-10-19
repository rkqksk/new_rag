#!/usr/bin/env python3
"""
Claude API MCP Server v3.0
Unified server for Haiku 4.5 + Sonnet 4.5 with intelligent routing

Features:
- Haiku 4.5 (claude-haiku-4-5): Fast, cheap code execution
- Sonnet 4.5 (claude-sonnet-4-5-20250929): Complex reasoning, planning
- Automatic model selection based on complexity
- API credit tracking and usage monitoring
- Fallback to Claude Code when API quota exceeded
"""

import asyncio
import json
import sys
import os
import logging
import hashlib
from typing import Any, Dict, List, Optional, Literal
from datetime import datetime, timedelta
from functools import lru_cache

import anthropic
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 모델 정의
HAIKU_MODEL = "claude-haiku-4-5"
SONNET_MODEL = "claude-sonnet-4-5-20250929"


class APIQuotaManager:
    """API 크레딧 및 사용량 관리"""

    def __init__(self):
        """초기화"""
        self.daily_limit = int(os.getenv("ANTHROPIC_DAILY_LIMIT", "1000000"))  # 1M tokens/day
        self.usage_today = {
            "haiku": {"tokens": 0, "requests": 0, "cost": 0.0},
            "sonnet": {"tokens": 0, "requests": 0, "cost": 0.0}
        }
        self.last_reset = datetime.now().date()

        # 가격 (per 1M tokens, input)
        self.pricing = {
            "haiku": {"input": 0.25, "output": 1.25},
            "sonnet": {"input": 3.0, "output": 15.0}
        }

    def _check_reset(self):
        """일일 리셋 확인"""
        today = datetime.now().date()
        if today > self.last_reset:
            logger.info(f"Daily quota reset. Previous usage: {self.get_usage_summary()}")
            self.usage_today = {
                "haiku": {"tokens": 0, "requests": 0, "cost": 0.0},
                "sonnet": {"tokens": 0, "requests": 0, "cost": 0.0}
            }
            self.last_reset = today

    def track_usage(
        self,
        model_type: Literal["haiku", "sonnet"],
        input_tokens: int,
        output_tokens: int
    ):
        """사용량 추적"""
        self._check_reset()

        total_tokens = input_tokens + output_tokens

        # 비용 계산
        cost = (
            (input_tokens / 1_000_000) * self.pricing[model_type]["input"] +
            (output_tokens / 1_000_000) * self.pricing[model_type]["output"]
        )

        self.usage_today[model_type]["tokens"] += total_tokens
        self.usage_today[model_type]["requests"] += 1
        self.usage_today[model_type]["cost"] += cost

        logger.info(
            f"Usage: {model_type.upper()} | "
            f"Tokens: {total_tokens} | Cost: ${cost:.6f} | "
            f"Daily total: ${self.get_total_cost():.4f}"
        )

    def get_total_tokens(self) -> int:
        """오늘 총 토큰 사용량"""
        self._check_reset()
        return (
            self.usage_today["haiku"]["tokens"] +
            self.usage_today["sonnet"]["tokens"]
        )

    def get_total_cost(self) -> float:
        """오늘 총 비용"""
        self._check_reset()
        return (
            self.usage_today["haiku"]["cost"] +
            self.usage_today["sonnet"]["cost"]
        )

    def has_quota_remaining(self) -> bool:
        """API 할당량 남았는지 확인"""
        return self.get_total_tokens() < self.daily_limit

    def get_usage_summary(self) -> Dict[str, Any]:
        """사용량 요약"""
        self._check_reset()
        total_tokens = self.get_total_tokens()
        total_cost = self.get_total_cost()

        return {
            "date": self.last_reset.isoformat(),
            "haiku": self.usage_today["haiku"],
            "sonnet": self.usage_today["sonnet"],
            "total_tokens": total_tokens,
            "total_cost": round(total_cost, 4),
            "daily_limit": self.daily_limit,
            "remaining_tokens": self.daily_limit - total_tokens,
            "quota_used_percent": round((total_tokens / self.daily_limit) * 100, 2)
        }


class ComplexityAnalyzer:
    """작업 복잡도 분석기"""

    @staticmethod
    def estimate_complexity(prompt: str, system: Optional[str] = None) -> float:
        """
        프롬프트 복잡도 추정 (0.0 - 1.0)

        Returns:
            0.0-0.3: Simple (Haiku 적합)
            0.3-0.7: Medium (Haiku/Sonnet 둘 다 가능)
            0.7-1.0: Complex (Sonnet 권장)
        """
        score = 0.0

        # 길이 기반
        if len(prompt) > 500:
            score += 0.2
        elif len(prompt) > 200:
            score += 0.1

        # 복잡한 키워드
        complex_keywords = [
            "analyze", "compare", "explain", "design", "architecture",
            "strategy", "plan", "reasoning", "understand", "comprehensive",
            "detailed", "multi-step", "complex", "advanced"
        ]
        keyword_count = sum(1 for kw in complex_keywords if kw in prompt.lower())
        score += min(keyword_count * 0.1, 0.3)

        # 코드 작업 (Haiku 선호)
        code_keywords = ["write code", "implement", "function", "class", "script", "fix bug"]
        if any(kw in prompt.lower() for kw in code_keywords):
            score -= 0.2

        # System 프롬프트 존재 시 복잡도 증가
        if system and len(system) > 100:
            score += 0.1

        return max(0.0, min(1.0, score))

    @staticmethod
    def should_use_sonnet(prompt: str, system: Optional[str] = None, force_model: Optional[str] = None) -> bool:
        """Sonnet 사용 여부 결정"""
        if force_model:
            return force_model == "sonnet"

        complexity = ComplexityAnalyzer.estimate_complexity(prompt, system)
        return complexity >= 0.7


class ClaudeAPIServer:
    """통합 Claude API MCP 서버"""

    def __init__(self):
        """서버 초기화"""
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be set in environment")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.quota_manager = APIQuotaManager()
        self.complexity_analyzer = ComplexityAnalyzer()

        self.retry_attempts = 3
        self.retry_delay = 1

        logger.info("✓ Claude API Server initialized (Haiku 4.5 + Sonnet 4.5)")

    async def call_api(
        self,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        system: Optional[str] = None,
        model: Optional[Literal["haiku", "sonnet", "auto"]] = "auto"
    ) -> Dict[str, Any]:
        """
        Claude API 호출 (자동 모델 선택)

        Args:
            prompt: 사용자 프롬프트
            max_tokens: 최대 토큰 수
            temperature: 온도 (0-1)
            system: 시스템 프롬프트
            model: 모델 선택 ("haiku", "sonnet", "auto")

        Returns:
            생성된 텍스트 및 메타데이터
        """
        # API 할당량 확인
        if not self.quota_manager.has_quota_remaining():
            return {
                "text": "⚠️ API quota exceeded. Please use Claude Code subscription instead.",
                "model": None,
                "error": "quota_exceeded",
                "suggestion": "Use Claude Code (subscription) for unlimited requests",
                "tokens": {"input": 0, "output": 0, "total": 0}
            }

        # 모델 선택
        if model == "auto":
            use_sonnet = self.complexity_analyzer.should_use_sonnet(prompt, system)
            selected_model = SONNET_MODEL if use_sonnet else HAIKU_MODEL
            model_type = "sonnet" if use_sonnet else "haiku"
        elif model == "sonnet":
            selected_model = SONNET_MODEL
            model_type = "sonnet"
        else:  # haiku
            selected_model = HAIKU_MODEL
            model_type = "haiku"

        # 재시도 로직
        for attempt in range(self.retry_attempts):
            try:
                messages = [{"role": "user", "content": prompt}]
                kwargs = {
                    "model": selected_model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": messages
                }

                if system:
                    kwargs["system"] = system

                response = self.client.messages.create(**kwargs)

                result_text = response.content[0].text
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens
                total_tokens = input_tokens + output_tokens

                # 사용량 추적
                self.quota_manager.track_usage(model_type, input_tokens, output_tokens)

                logger.info(
                    f"✓ API call succeeded ({model_type.upper()}, attempt {attempt + 1}): "
                    f"{input_tokens}+{output_tokens}={total_tokens} tokens"
                )

                return {
                    "text": result_text,
                    "model": selected_model,
                    "model_type": model_type,
                    "tokens": {
                        "input": input_tokens,
                        "output": output_tokens,
                        "total": total_tokens
                    },
                    "cost": {
                        "this_request": round(
                            (input_tokens / 1_000_000) * self.quota_manager.pricing[model_type]["input"] +
                            (output_tokens / 1_000_000) * self.quota_manager.pricing[model_type]["output"],
                            6
                        ),
                        "daily_total": round(self.quota_manager.get_total_cost(), 4)
                    },
                    "quota": {
                        "remaining": self.quota_manager.daily_limit - self.quota_manager.get_total_tokens(),
                        "percent_used": round(
                            (self.quota_manager.get_total_tokens() / self.quota_manager.daily_limit) * 100, 2
                        )
                    }
                }

            except anthropic.APIConnectionError as e:
                logger.warning(f"Connection error (attempt {attempt + 1}/{self.retry_attempts}): {e}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                continue

            except anthropic.RateLimitError as e:
                logger.warning(f"Rate limit error (attempt {attempt + 1}/{self.retry_attempts}): {e}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1) * 2)
                continue

            except anthropic.APIStatusError as e:
                logger.error(f"API Status error {e.status_code}: {e.message}")
                break

            except Exception as e:
                logger.error(f"Unexpected error (attempt {attempt + 1}/{self.retry_attempts}): {e}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)
                continue

        # 모든 재시도 실패
        return {
            "text": f"❌ Error: Failed to call {model_type.upper()} after {self.retry_attempts} attempts",
            "model": selected_model,
            "error": True,
            "tokens": {"input": 0, "output": 0, "total": 0}
        }

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """MCP 요청 처리"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        try:
            if method == "initialize":
                return self._handle_initialize(request_id)

            elif method == "generate":
                result = await self._handle_generate(params)
                return self._format_response(request_id, result)

            elif method == "health":
                result = self._handle_health()
                return self._format_response(request_id, result)

            elif method == "usage_stats":
                result = self.quota_manager.get_usage_summary()
                return self._format_response(request_id, result)

            elif method == "estimate_complexity":
                prompt = params.get("prompt", "")
                system = params.get("system")
                complexity = self.complexity_analyzer.estimate_complexity(prompt, system)
                recommended = "sonnet" if complexity >= 0.7 else "haiku"
                return self._format_response(request_id, {
                    "complexity": round(complexity, 2),
                    "recommended_model": recommended,
                    "description": (
                        "Simple task - Haiku recommended" if complexity < 0.3 else
                        "Medium task - Both models suitable" if complexity < 0.7 else
                        "Complex task - Sonnet recommended"
                    )
                })

            else:
                return self._format_error(request_id, -32601, f"Method not found: {method}")

        except Exception as e:
            logger.error(f"Request handling error: {e}")
            return self._format_error(request_id, -32603, f"Internal error: {str(e)}")

    def _handle_initialize(self, request_id: Optional[int]) -> Dict[str, Any]:
        """초기화 요청 처리"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {
                        "generate": {
                            "description": "Generate text using Claude Haiku 4.5 or Sonnet 4.5"
                        },
                        "estimate_complexity": {
                            "description": "Estimate task complexity and recommend model"
                        }
                    }
                },
                "serverInfo": {
                    "name": "claude-api-mcp-server",
                    "version": "3.0.0",
                    "features": [
                        "haiku_4_5",
                        "sonnet_4_5",
                        "auto_model_selection",
                        "quota_tracking",
                        "cost_monitoring"
                    ],
                    "models": {
                        "haiku": HAIKU_MODEL,
                        "sonnet": SONNET_MODEL
                    }
                }
            }
        }

    async def _handle_generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """텍스트 생성 요청 처리"""
        prompt = params.get("prompt", "")
        max_tokens = params.get("max_tokens", 4096)
        temperature = params.get("temperature", 0.3)
        system = params.get("system")
        model = params.get("model", "auto")

        result = await self.call_api(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            model=model
        )

        return result

    def _handle_health(self) -> Dict[str, Any]:
        """상태 확인 처리"""
        usage = self.quota_manager.get_usage_summary()

        return {
            "status": "healthy",
            "models": {
                "haiku": HAIKU_MODEL,
                "sonnet": SONNET_MODEL
            },
            "quota": {
                "daily_limit": usage["daily_limit"],
                "total_used": usage["total_tokens"],
                "remaining": usage["remaining_tokens"],
                "percent_used": usage["quota_used_percent"]
            },
            "cost": {
                "today": usage["total_cost"],
                "haiku": usage["haiku"]["cost"],
                "sonnet": usage["sonnet"]["cost"]
            },
            "requests": {
                "haiku": usage["haiku"]["requests"],
                "sonnet": usage["sonnet"]["requests"]
            }
        }

    @staticmethod
    def _format_response(request_id: Optional[int], result: Dict[str, Any]) -> Dict[str, Any]:
        """MCP 응답 포맷"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }

    @staticmethod
    def _format_error(request_id: Optional[int], code: int, message: str) -> Dict[str, Any]:
        """MCP 에러 응답 포맷"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }

    async def run(self):
        """서버 실행 (stdin/stdout 통신)"""
        logger.info("Claude API MCP Server started (Haiku 4.5 + Sonnet 4.5)")

        while True:
            try:
                # stdin에서 요청 읽기
                line = sys.stdin.readline()
                if not line:
                    break

                request = json.loads(line.strip())
                logger.debug(f"Received request: {request.get('method')}")

                # 요청 처리
                response = await self.handle_request(request)

                # stdout으로 응답 전송
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

            except json.JSONDecodeError as e:
                error_response = self._format_error(None, -32700, f"Parse error: {str(e)}")
                sys.stdout.write(json.dumps(error_response) + "\n")
                sys.stdout.flush()

            except Exception as e:
                logger.error(f"Server error: {e}")
                error_response = self._format_error(None, -32603, f"Internal error: {str(e)}")
                sys.stdout.write(json.dumps(error_response) + "\n")
                sys.stdout.flush()


async def main():
    """메인 함수"""
    server = ClaudeAPIServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
