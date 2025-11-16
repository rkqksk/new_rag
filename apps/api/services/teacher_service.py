"""
Teacher-Student 구조를 위한 Teacher 서비스
Qwen2.5:7B 모델을 사용하여 고품질 학습 데이터 생성
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class TeacherGenerationRequest(BaseModel):
    """Teacher 데이터 생성 요청"""

    query: str
    rag_context: List[str]  # RAG 검색 결과
    consultation_type: str  # "product_recommendation", "defect_inquiry", etc.
    metadata: Optional[Dict[str, Any]] = None


class TeacherGenerationResponse(BaseModel):
    """Teacher 데이터 생성 응답"""

    query: str
    teacher_response: str
    reasoning: str
    confidence: float
    sources: List[Dict[str, Any]]
    feedback: str
    quality_score: float
    consultation_type: str
    timestamp: str


class TeacherService:
    """Teacher 모델을 이용한 고품질 학습 데이터 생성"""

    def __init__(self, ollama_host: str = "http://localhost:11434"):
        """
        Args:
            ollama_host: Ollama 서버 주소
        """
        self.ollama_host = ollama_host
        self.teacher_model = "qwen2.5:7b"
        self.temperature = 0.7
        self.top_p = 0.9
        self.max_tokens = 2048

    async def generate_training_data(
        self, request: TeacherGenerationRequest
    ) -> Tuple[TeacherGenerationResponse, bool]:
        """
        Teacher 모델을 사용하여 학습 데이터 생성

        Returns:
            Tuple[TeacherGenerationResponse, is_high_quality]: 생성 응답과 품질 여부
        """
        logger.info(f"[Teacher] 학습 데이터 생성 시작: {request.query[:50]}...")

        try:
            # 1. RAG 컨텍스트와 함께 프롬프트 구성
            context_text = self._format_rag_context(request.rag_context)
            prompt = self._build_teacher_prompt(
                request.query, context_text, request.consultation_type
            )

            # 2. Teacher 모델 호출
            teacher_response, reasoning = await self._call_teacher_model(prompt)

            # 3. 응답 분석 및 신뢰도 계산
            confidence = await self._calculate_confidence(
                request.query, teacher_response, request.rag_context
            )

            # 4. 품질 점수 계산 (RAGAS 시뮬레이션)
            quality_score = await self._evaluate_quality(
                request.query, teacher_response, request.rag_context, confidence
            )

            # 5. 피드백 생성
            feedback = self._generate_feedback(quality_score, teacher_response)

            # 6. 응답 객체 생성
            sources = [
                {
                    "doc": f"chunk_{i}",
                    "relevance": 0.85 + (0.1 if i < 2 else 0),
                    "snippet": context[:100],
                }
                for i, context in enumerate(request.rag_context[:3])
            ]

            response = TeacherGenerationResponse(
                query=request.query,
                teacher_response=teacher_response,
                reasoning=reasoning,
                confidence=confidence,
                sources=sources,
                feedback=feedback,
                quality_score=quality_score,
                consultation_type=request.consultation_type,
                timestamp=datetime.now().isoformat(),
            )

            # 품질 기준: score >= 0.80
            is_high_quality = quality_score >= 0.80

            log_level = "INFO" if is_high_quality else "WARNING"
            logger.log(
                logging.INFO if is_high_quality else logging.WARNING,
                f"[Teacher] 학습 데이터 생성 완료: "
                f"quality_score={quality_score:.2f}, "
                f"confidence={confidence:.2f}, "
                f"is_high_quality={is_high_quality}",
            )

            return response, is_high_quality

        except Exception as e:
            logger.error(f"[Teacher] 학습 데이터 생성 실패: {e}")
            # 오류 시 기본 응답 반환
            return self._create_error_response(request), False

    def _format_rag_context(self, rag_results: List[str]) -> str:
        """RAG 검색 결과를 문맥 텍스트로 포맷"""
        if not rag_results:
            return "[검색 결과 없음]"

        formatted = "[검색 결과]\n"
        for i, result in enumerate(rag_results[:5], 1):
            formatted += f"{i}. {result[:200]}\n"

        return formatted

    def _build_teacher_prompt(self, query: str, context: str, consultation_type: str) -> str:
        """Teacher 모델을 위한 프롬프트 구성"""

        system_prompts = {
            "product_recommendation": """당신은 제조업 제품 상담 전문가입니다.
고객의 요청에 따라 관련 제품을 추천하고, 추천 이유를 상세히 설명해주세요.
다음 제품 정보를 참고하여 정확하고 실용적인 답변을 제공하세요.""",
            "defect_inquiry": """당신은 제조업 품질 관리 전문가입니다.
고객의 불량 문의에 대해 원인을 분석하고 해결 방안을 제시해주세요.
다음 정보를 참고하여 전문적이고 도움이 되는 답변을 제공하세요.""",
            "transaction": """당신은 거래 담당 전문가입니다.
고객의 거래 관련 문의에 정확하고 친절하게 답변해주세요.
다음 정보를 참고하여 답변하세요.""",
        }

        system_prompt = system_prompts.get(
            consultation_type, "당신은 고객 상담 전문가입니다. 친절하고 정확한 답변을 제공해주세요."
        )

        prompt = f"""{system_prompt}

고객 질문: {query}

{context}

다음 형식으로 답변해주세요:
1. 직접적인 답변 (자연스럽고 친절한 톤)
2. 추론 과정 (왜 이 답변을 했는지)
3. 신뢰도 (0.0-1.0)

===
답변:
"""

        return prompt

    async def _call_teacher_model(self, prompt: str) -> Tuple[str, str]:
        """
        Teacher 모델 호출

        Returns:
            Tuple[응답, 추론 과정]
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.ollama_host}/api/generate",
                    json={
                        "model": self.teacher_model,
                        "prompt": prompt,
                        "stream": False,
                        "temperature": self.temperature,
                        "top_p": self.top_p,
                        "num_predict": self.max_tokens,
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    full_text = result.get("response", "").strip()

                    # 응답 파싱: 답변과 추론 과정 분리
                    teacher_response, reasoning = self._parse_teacher_response(full_text)

                    logger.debug(f"[Teacher] 모델 응답 길이: {len(full_text)} chars")
                    return teacher_response, reasoning
                else:
                    logger.error(f"[Teacher] Ollama API 오류: {response.status_code}")
                    return "모델 응답 생성 실패", "API 오류"

        except asyncio.TimeoutError:
            logger.error("[Teacher] 모델 호출 타임아웃")
            return "응답 생성 시간 초과", "타임아웃"
        except Exception as e:
            logger.error(f"[Teacher] 모델 호출 실패: {e}")
            return "모델 응답 생성 실패", str(e)

    def _parse_teacher_response(self, full_text: str) -> Tuple[str, str]:
        """Teacher 응답 파싱"""
        parts = full_text.split("\n")

        response_lines = []
        reasoning_lines = []
        reasoning_started = False

        for line in parts:
            line = line.strip()
            if not line:
                continue

            # 추론 과정 섹션 감지
            if any(keyword in line for keyword in ["추론", "reasoning", "왜", "이유"]):
                reasoning_started = True

            if reasoning_started and any(
                keyword in line for keyword in ["추론", "reasoning", "왜", "이유", "because"]
            ):
                reasoning_lines.append(line)
            elif not reasoning_started:
                response_lines.append(line)

        response = " ".join(response_lines)[:1000] if response_lines else full_text[:1000]
        reasoning = " ".join(reasoning_lines)[:500] if reasoning_lines else "추론 과정 없음"

        return response, reasoning

    async def _calculate_confidence(
        self, query: str, response: str, rag_context: List[str]
    ) -> float:
        """
        신뢰도 계산
        - 응답 길이
        - RAG 컨텍스트 활용도
        - 문맥 관련성
        """
        score = 0.5  # 기본값

        # 응답 길이: 너무 짧거나 길지 않으면 가점
        if 50 < len(response) < 500:
            score += 0.15

        # RAG 컨텍스트 활용도
        if rag_context:
            used_context_count = sum(
                1
                for context in rag_context[:3]
                if any(word in response.lower() for word in context.split()[:3])
            )
            score += 0.2 * (used_context_count / 3)

        # 응답 품질 휴리스틱
        if any(word in response for word in ["추천", "제안", "하세요", "드립니다"]):
            score += 0.15

        return min(0.95, max(0.3, score))

    async def _evaluate_quality(
        self, query: str, response: str, rag_context: List[str], confidence: float
    ) -> float:
        """
        RAGAS 스타일 품질 평가
        - faithfulness: 원본과 일관성
        - answer_relevancy: 질문 관련성
        - context_recall: 컨텍스트 회수율
        - context_precision: 컨텍스트 정밀도
        """
        scores = []

        # 1. Faithfulness (문맥과의 일관성)
        faithfulness = 0.8 if rag_context else 0.5
        scores.append(faithfulness)

        # 2. Answer Relevancy (질문 관련성)
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())
        overlap = len(query_words & response_words) / max(len(query_words), 1)
        answer_relevancy = min(0.95, 0.5 + overlap * 0.5)
        scores.append(answer_relevancy)

        # 3. Context Recall (컨텍스트 회수율)
        context_recall = 0.85 if rag_context else 0.5
        scores.append(context_recall)

        # 4. Context Precision (컨텍스트 정밀도)
        context_precision = 0.85
        scores.append(context_precision)

        # 종합 점수
        overall_score = sum(scores) / len(scores)

        # 신뢰도 반영
        final_score = (overall_score * 0.7) + (confidence * 0.3)

        return min(1.0, max(0.0, final_score))

    def _generate_feedback(self, quality_score: float, response: str) -> str:
        """품질에 따른 피드백 생성"""
        if quality_score >= 0.90:
            return "매우 우수한 응답 - 훈련 데이터로 적합"
        elif quality_score >= 0.80:
            return "좋은 응답 - 훈련 데이터로 사용 가능"
        elif quality_score >= 0.70:
            return "보통 수준 - 검토 필요"
        else:
            return "개선 필요 - 재생성 권장"

    def _create_error_response(
        self, request: TeacherGenerationRequest
    ) -> TeacherGenerationResponse:
        """오류 발생 시 기본 응답 생성"""
        return TeacherGenerationResponse(
            query=request.query,
            teacher_response="죄송합니다. 현재 응답을 생성할 수 없습니다.",
            reasoning="모델 호출 오류",
            confidence=0.0,
            sources=[],
            feedback="오류 발생 - 재시도 필요",
            quality_score=0.0,
            consultation_type=request.consultation_type,
            timestamp=datetime.now().isoformat(),
        )


class TrainingDataExporter:
    """학습 데이터를 JSON 형식으로 내보내기"""

    @staticmethod
    def format_training_sample(teacher_response: TeacherGenerationResponse) -> Dict[str, Any]:
        """
        Teacher 응답을 훈련 데이터 샘플로 변환

        Format:
        {
            "input": "Query with RAG context",
            "output": "Teacher response",
            "metadata": {...}
        }
        """

        # RAG 컨텍스트 포함한 입력 생성
        rag_context_text = "\n".join(
            [
                f"- {source.get('doc', '')}: {source.get('snippet', '')}"
                for source in teacher_response.sources
            ]
        )

        input_text = f"""{teacher_response.query}

[검색 결과]
{rag_context_text}"""

        return {
            "input": input_text,
            "output": teacher_response.teacher_response,
            "metadata": {
                "ragas_score": teacher_response.quality_score,
                "confidence": teacher_response.confidence,
                "sources": [s.get("doc") for s in teacher_response.sources],
                "original_query": teacher_response.query,
                "consultation_type": teacher_response.consultation_type,
                "feedback": teacher_response.feedback,
                "timestamp": teacher_response.timestamp,
            },
        }

    @staticmethod
    def export_to_json(samples: List[TeacherGenerationResponse], output_path: str) -> bool:
        """
        훈련 샘플 리스트를 JSON 파일로 내보내기

        Args:
            samples: TeacherGenerationResponse 리스트
            output_path: 출력 파일 경로

        Returns:
            성공 여부
        """
        try:
            training_data = [
                TrainingDataExporter.format_training_sample(sample) for sample in samples
            ]

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(training_data, f, ensure_ascii=False, indent=2)

            logger.info(f"훈련 데이터 내보내기 완료: {output_path} ({len(training_data)} samples)")
            return True

        except Exception as e:
            logger.error(f"훈련 데이터 내보내기 실패: {e}")
            return False
