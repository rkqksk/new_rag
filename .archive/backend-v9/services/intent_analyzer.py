```python
"""
Phase 3 의도 분석 엔진

비동기 NLP 처리를 통한 사용자 의도 분석 및 키워드 추출.
Haiku와 Sonnet 모델을 활용한 다층적 분석 제공.

Author: NLP Team
Version: 1.0.0
"""

import asyncio
import json
import logging
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """의도 타입 분류"""
    QUESTION = "question"
    COMMAND = "command"
    STATEMENT = "statement"
    REQUEST = "request"
    COMPLAINT = "complaint"
    FEEDBACK = "feedback"
    UNKNOWN = "unknown"


class ConfidenceLevel(Enum):
    """신뢰도 레벨"""
    VERY_HIGH = 0.9
    HIGH = 0.7
    MEDIUM = 0.5
    LOW = 0.3
    VERY_LOW = 0.1


@dataclass
class Keyword:
    """키워드 데이터 클래스"""
    text: str
    weight: float
    category: str
    frequency: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)


@dataclass
class IntentResult:
    """의도 분석 결과 데이터 클래스"""
    intent_type: str
    confidence: float
    keywords: List[Dict[str, Any]]
    entities: List[Dict[str, str]]
    sentiment: str
    summary: str
    analysis_time_ms: float
    model_used: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "intent_type": self.intent_type,
            "confidence": self.confidence,
            "keywords": self.keywords,
            "entities": self.entities,
            "sentiment": self.sentiment,
            "summary": self.summary,
            "analysis_time_ms": self.analysis_time_ms,
            "model_used": self.model_used,
            "metadata": self.metadata,
        }


class IntentAnalyzer:
    """Phase 3 의도 분석 엔진"""

    def __init__(
        self,
        api_server_url: str = "http://localhost:8000",
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        의도 분석 엔진 초기화.

        Args:
            api_server_url: Claude API 서버 URL
            timeout: 요청 타임아웃 (초)
            max_retries: 최대 재시도 횟수

        Raises:
            ValueError: 유효하지 않은 URL 형식
        """
        if not api_server_url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid API server URL: {api_server_url}")

        self.api_server_url = api_server_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.session: Optional[aiohttp.ClientSession] = None

        logger.info(
            f"IntentAnalyzer initialized with server: {api_server_url}"
        )

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.session:
            await self.session.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(aiohttp.ClientError),
    )
    async def _call_claude_api(
        self,
        model: str,
        prompt: str,
        max_tokens: int = 1024,
    ) -> str:
        """
        Claude API 호출 (재시도 로직 포함).

        Args:
            model: 사용할 모델 (haiku, sonnet)
            prompt: 프롬프트 텍스트
            max_tokens: 최대 토큰 수

        Returns:
            API 응답 텍스트

        Raises:
            aiohttp.ClientError: API 호출 실패
            asyncio.TimeoutError: 타임아웃
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")

        payload = {
            "model": model,
            "prompt": prompt,
            "max_tokens": max_tokens,
        }

        try:
            async with self.session.post(
                f"{self.api_server_url}/api/v1/analyze",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(
                        f"API error (status={response.status}): {error_text}"
                    )
                    raise aiohttp.ClientError(
                        f"API returned status {response.status}"
                    )

                data = await response.json()
                logger.debug(f"API response received for model: {model}")
                return data.get("response", "")

        except asyncio.TimeoutError:
            logger.error(f"API timeout for model: {model}")
            raise
        except aiohttp.ClientError as e:
            logger.error(f"API client error: {str(e)}")
            raise

    def _parse_keywords_response(self, response: str) -> List[Keyword]:
        """
        키워드 추출 응답 파싱.

        Args:
            response: API 응답 텍스트

        Returns:
            Keyword 객체 리스트
        """
        keywords = []
        try:
            # JSON 형식 파싱 시도
            if response.startswith("[") or response.startswith("{"):
                data = json.loads(response)
                if isinstance(data, list):
                    for item in data:
                        keywords.append(
                            Keyword(
                                text=item.get("text", ""),
                                weight=float(item.get("weight", 0.5)),
                                category=item.get("category", "general"),
                                frequency=int(item.get("frequency", 1)),
                            )
                        )
            else:
                # 텍스트 파싱
                lines = response.strip().split("\n")
                for line in lines:
                    if line.strip():
                        parts = line.split("|")
                        if len(parts) >= 2:
                            keywords.append(
                                Keyword(
                                    text=parts[0].strip(),
                                    weight=float(parts[1].strip()),
                                    category=parts[2].strip()
                                    if len(parts) > 2
                                    else "general",
                                )
                            )

            logger.debug(f"Parsed {len(keywords)} keywords")
            return keywords

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse keywords response: {str(e)}")
            return []

    def _parse_intent_response(
        self, response: str
    ) -> Tuple[str, float, List[Dict[str, str]], str]:
        """
        의도 분석 응답 파싱.

        Args:
            response: API 응답 텍스트

        Returns:
            (의도타입, 신뢰도, 엔티티, 감정) 튜플
        """
        try:
            if response.startswith("{"):
                data = json.loads(response)
            else:
                # 텍스트 파싱
                data = self._parse_text_response(response)

            intent_type = data.get("intent_type", IntentType.UNKNOWN.value)
            confidence = float(data.get("confidence", 0.5))
            entities = data.get("entities", [])
            sentiment = data.get("sentiment", "neutral")

            # 신뢰도 범위 검증
            confidence = max(0.0, min(1.0, confidence))

            logger.debug(
                f"Parsed intent: {intent_type} (confidence: {confidence})"
            )
            return intent_type, confidence, entities, sentiment

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse intent response: {str(e)}")
            return IntentType.UNKNOWN.value, 0.5, [], "neutral"

    def _parse_text_response(self, text: str) -> Dict[str, Any]:
        """
        텍스트 형식 응답 파싱.

        Args:
            text: 파싱할 텍스트

        Returns:
            파싱된 데이터 딕셔너리
        """
        data = {
            "intent_type": IntentType.UNKNOWN.value,
            "confidence": 0.5,
            "entities": [],
            "sentiment": "neutral",
        }

        lines = text.strip().split("\n")
        for line in lines:
            if "intent:" in line.lower():
                intent = line.split(":", 1)[1].strip().lower()
                data["intent_type"] = intent
            elif "confidence:" in line.lower():
                try:
                    conf = float(
                        re.search(r"[\d.]+", line.split(":", 1)[1]).group()
                    )
                    data["confidence"] = conf
                except (AttributeError, ValueError):
                    pass
            elif "sentiment:" in line.lower():
                sentiment = line.split(":", 1)[1].strip().lower()
                data["sentiment"] = sentiment

        return data

    async def extract_keywords_haiku(
        self, text: str, top_k: int = 10
    ) -> List[Keyword]:
        """
        Haiku를 사용한 빠른 키워드 추출 (200ms).

        Args:
            text: 분석할 텍스트
            top_k: 추출할 상위 키워드 개수

        Returns:
            Keyword 객체 리스트

        Example:
            >>> analyzer = IntentAnalyzer()
            >>> async with analyzer:
            ...     keywords = await analyzer.extract_keywords_haiku(
            ...         "좋은 상품이지만 배송이 느려요"
            ...     )
            ...     for kw in keywords:
            ...         print(f"{kw.text}: {kw.weight}")
        """
        logger.info(f"Extracting keywords from text (length: {len(text)})")

        prompt = f"""다음 텍스트에서 상위 {top_k}개의 중요 키워드를 추출하세요.
각 키워드는 다음 형식으로 반환하세요:
[{{"text": "키워드", "weight": 0.9, "category": "카테고리"}}]

텍스트: {text}

JSON 형식으로만 응답하세요."""

        try:
            response = await self._call_claude_api(
                model="haiku",
                prompt=prompt,
                max_tokens=512,
            )
            keywords = self._parse_keywords_response(response)
            logger.info(f"Successfully extracted {len(keywords)} keywords")
            return keywords[:top_k]

        except Exception as e:
            logger.error(f"Keyword extraction failed: {str(e)}")
            return []

    async def preprocess_haiku(self, text: str) -> Dict[str, Any]:
        """
        Haiku를 사용한 텍스트 전처리 (200ms).

        Args:
            text: 전처리할 텍스트

        Returns:
            전처리 결과 딕셔너리

        Raises:
            ValueError: 빈 텍스트 입력
        """
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty")

        logger.info("Starting text preprocessing with Haiku")

        prompt = f"""다음 텍스트를 전처리하세요:
1. 정규화 (띄어쓰기, 특수문자)
2. 토큰화
3. 불용어 제거
4. 텍스트 길이 및 품질 평가

텍스트: {text}

JSON 형식으로 다음 구조로 응답하세요:
{{
    "normalized_text": "정규화된 텍스트",
    "tokens": ["토큰1", "토큰2"],
    "token_count": 숫자,
    "quality_score": 0.0-1.0,
    "language": "언어코드",
    "has_special_chars": boolean
}}"""

        try:
            response = await self._call_claude_api(
                model="haiku",
                prompt=prompt,
                max_tokens=512,
            )

            # JSON 추출
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                logger.info("Text preprocessing completed successfully")
                return result
            else:
                logger.warning("Could not extract JSON from preprocessing response")
                return {
                    "normalized_text": text,
                    "tokens": text.split(),
                    "token_count": len(text.split()),
                    "quality_score": 0.7,
                    "language": "ko",
                    "has_special_chars": bool(re.search(r"[^\w\s]", text)),
                }

        except Exception as e:
            logger.error(f"Preprocessing failed: {str(e)}")
            raise

    async def analyze_intent_sonnet(self, text: str) -> IntentResult:
        """
        Sonnet을 사용한 의도 분석 (1500ms).

        Args:
            text: 분석할 텍스트

        Returns:
            IntentResult 객체

        Example:
            >>> async with IntentAnalyzer() as analyzer:
            ...     result = await analyzer.analyze_intent_sonnet(
            ...         "이 제품을 구매하고 싶어요"
            ...     )
            ...     print(f"Intent: {result.intent_type}")
            ...     print(f"Confidence: {result.confidence}")
        """
        start_time = datetime.now()
        logger.info(f"Starting intent analysis with Sonnet")

        prompt = f"""다음 텍스트의 사용자 의도를 분석하세요:

텍스트: {text}

다음 항목을 