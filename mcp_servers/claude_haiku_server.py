#!/usr/bin/env python3
"""
Claude Haiku 4.5 MCP Server v2.0
API 키 라우팅, 비동기 처리, 캐싱 및 에러 복구 개선
"""

import asyncio
import json
import sys
import os
import logging
import hashlib
from typing import Any, Dict, List, Optional
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


class APIKeyRouter:
    """API 키 라우팅 및 관리"""

    def __init__(self):
        """라우터 초기화"""
        self.primary_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        self.backup_key = os.getenv("ANTHROPIC_API_KEY_BACKUP", "").strip()
        self.key_usage = {}
        self.last_rotation = datetime.now()

        # Validate at least one API key is configured
        if not self.primary_key and not self.backup_key:
            raise ValueError(
                "ANTHROPIC_API_KEY must be set in environment variables. "
                "Optionally set ANTHROPIC_API_KEY_BACKUP for failover."
            )

    def get_current_key(self) -> str:
        """현재 사용할 API 키 반환"""
        if not self.primary_key:
            raise ValueError("No API keys configured")
        return self.primary_key

    def rotate_key(self) -> str:
        """백업 키로 전환 (에러 복구용)"""
        if not self.backup_key:
            logger.warning("No backup API key available")
            return self.primary_key
        
        logger.info("Rotating to backup API key")
        self.primary_key, self.backup_key = self.backup_key, self.primary_key
        self.last_rotation = datetime.now()
        return self.primary_key

    def track_usage(self, key: str, tokens: int, status: str = "success"):
        """API 키 사용량 추적"""
        if key not in self.key_usage:
            self.key_usage[key] = {
                "total_tokens": 0,
                "request_count": 0,
                "success_count": 0,
                "error_count": 0
            }
        
        self.key_usage[key]["total_tokens"] += tokens
        self.key_usage[key]["request_count"] += 1
        
        if status == "success":
            self.key_usage[key]["success_count"] += 1
        else:
            self.key_usage[key]["error_count"] += 1

    def get_usage_stats(self) -> Dict[str, Any]:
        """사용량 통계 반환"""
        return {
            "key_usage": self.key_usage,
            "last_rotation": self.last_rotation.isoformat(),
            "rotation_count": len(self.key_usage)
        }


class ResponseCache:
    """응답 캐싱"""

    def __init__(self, ttl_seconds: int = 300):
        """캐시 초기화"""
        self.cache = {}
        self.ttl = timedelta(seconds=ttl_seconds)

    def _generate_key(self, prompt: str, system: Optional[str]) -> str:
        """캐시 키 생성"""
        cache_input = f"{prompt}:{system}"
        return hashlib.md5(cache_input.encode()).hexdigest()

    def get(self, prompt: str, system: Optional[str]) -> Optional[str]:
        """캐시에서 응답 가져오기"""
        key = self._generate_key(prompt, system)
        
        if key in self.cache:
            cached_item = self.cache[key]
            if datetime.now() < cached_item["expires"]:
                logger.debug(f"Cache hit for prompt: {prompt[:50]}...")
                return cached_item["response"]
            else:
                del self.cache[key]
        
        return None

    def set(self, prompt: str, system: Optional[str], response: str):
        """캐시에 응답 저장"""
        key = self._generate_key(prompt, system)
        self.cache[key] = {
            "response": response,
            "expires": datetime.now() + self.ttl,
            "created": datetime.now()
        }

    def clear_expired(self):
        """만료된 캐시 정리"""
        now = datetime.now()
        expired_keys = [
            k for k, v in self.cache.items()
            if now > v["expires"]
        ]
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.debug(f"Cleared {len(expired_keys)} expired cache entries")


class ClaudeHaikuServer:
    """Claude Haiku 4.5 MCP Server v2.0"""

    def __init__(self):
        """서버 초기화"""
        self.api_router = APIKeyRouter()
        self.cache = ResponseCache(ttl_seconds=300)
        self.retry_attempts = 3
        self.retry_delay = 1
        
        self._init_client()

    def _init_client(self):
        """클라이언트 초기화"""
        try:
            api_key = self.api_router.get_current_key()
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = "claude-haiku-4-5-20251001"
            logger.info("✓ Anthropic client initialized successfully")
        except ValueError as e:
            logger.error(f"✗ Failed to initialize client: {e}")
            self.client = None

    async def call_haiku(
        self,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        system: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Haiku API 호출 (재시도 로직 포함)

        Args:
            prompt: 사용자 프롬프트
            max_tokens: 최대 토큰 수
            temperature: 온도 (0-1)
            system: 시스템 프롬프트 (선택)
            use_cache: 캐싱 사용 여부

        Returns:
            생성된 텍스트 및 메타데이터
        """
        # 캐시 확인
        if use_cache:
            cached_response = self.cache.get(prompt, system)
            if cached_response:
                return {
                    "text": cached_response,
                    "model": self.model,
                    "cached": True,
                    "tokens": 0
                }

        # 재시도 로직
        for attempt in range(self.retry_attempts):
            try:
                if not self.client:
                    raise ValueError("Client not initialized")

                messages = [{"role": "user", "content": prompt}]
                kwargs = {
                    "model": self.model,
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
                api_key = self.api_router.get_current_key()
                self.api_router.track_usage(api_key, total_tokens, "success")

                # 캐시 저장
                if use_cache:
                    self.cache.set(prompt, system, result_text)

                logger.info(f"✓ Haiku call succeeded (attempt {attempt + 1})")

                return {
                    "text": result_text,
                    "model": self.model,
                    "tokens": {
                        "input": input_tokens,
                        "output": output_tokens,
                        "total": total_tokens
                    },
                    "cached": False
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
                if e.status_code == 401:  # Unauthorized - try rotating key
                    logger.warning(f"API key error, rotating to backup key")
                    self.api_router.rotate_key()
                    self._init_client()
                    if attempt < self.retry_attempts - 1:
                        continue
                
                logger.error(f"API Status error {e.status_code}: {e.message}")
                break

            except Exception as e:
                logger.error(f"Unexpected error (attempt {attempt + 1}/{self.retry_attempts}): {e}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)
                continue

        # 모든 재시도 실패
        api_key = self.api_router.get_current_key()
        self.api_router.track_usage(api_key, 0, "error")

        return {
            "text": f"Error: Failed to call Haiku after {self.retry_attempts} attempts",
            "model": self.model,
            "error": True,
            "tokens": {"input": 0, "output": 0, "total": 0}
        }

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        MCP 요청 처리

        Args:
            request: MCP 요청 JSON

        Returns:
            MCP 응답 JSON
        """
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
                result = self.api_router.get_usage_stats()
                return self._format_response(request_id, result)

            elif method == "clear_cache":
                self.cache.clear_expired()
                return self._format_response(request_id, {"message": "Cache cleared"})

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
                            "description": "Generate text using Claude Haiku"
                        }
                    }
                },
                "serverInfo": {
                    "name": "claude-haiku-mcp-server",
                    "version": "2.0.0",
                    "features": ["api_routing", "caching", "retry_logic", "usage_tracking"]
                }
            }
        }

    async def _handle_generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """텍스트 생성 요청 처리"""
        prompt = params.get("prompt", "")
        max_tokens = params.get("max_tokens", 4096)
        temperature = params.get("temperature", 0.3)
        system = params.get("system")
        use_cache = params.get("use_cache", True)

        result = await self.call_haiku(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            use_cache=use_cache
        )

        return result

    def _handle_health(self) -> Dict[str, Any]:
        """상태 확인 처리"""
        is_healthy = self.client is not None
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "model": self.model if is_healthy else None,
            "api_router": {
                "has_primary": bool(self.api_router.primary_key),
                "has_backup": bool(self.api_router.backup_key),
                "usage": self.api_router.get_usage_stats()
            },
            "cache": {
                "size": len(self.cache.cache),
                "ttl_seconds": self.cache.ttl.total_seconds()
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
        logger.info("Claude Haiku MCP Server started")
        
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
    server = ClaudeHaikuServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
