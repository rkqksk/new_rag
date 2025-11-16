"""
RAGAS 기반 평가 시스템
답변 품질, 신뢰도, 정확성을 평가하여 학습 데이터 필터링
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ConsultationType(str, Enum):
    """상담 타입"""

    PRODUCT_RECOMMENDATION = "product_recommendation"
    DEFECT_INQUIRY = "defect_inquiry"
    TRANSACTION = "transaction"


@dataclass
class RAGASMetrics:
    """RAGAS 평가 메트릭"""

    faithfulness: float  # 원본 문서와의 일관성 (0-1)
    answer_relevancy: float  # 질문과의 관련성 (0-1)
    context_recall: float  # 컨텍스트 회수율 (0-1)
    context_precision: float  # 컨텍스트 정밀도 (0-1)
    overall_score: float  # 종합 점수 (0-1)


@dataclass
class ManufacturingMetrics:
    """제조업 특화 메트릭"""

    product_accuracy: float  # 제품 정보 정확성
    defect_diagnosis_quality: float  # 불량 진단 정확성
    recommendation_relevance: float  # 추천 적합성
    safety_compliance: float  # 안전 규정 준수


@dataclass
class QualityMetrics:
    """응답 품질 메트릭"""

    length_appropriate: bool  # 길이 적절성
    grammar_correct: bool  # 문법 정확성
    sources_cited: bool  # 출처 인용 여부
    confidence_calibrated: float  # 신뢰도 교정


@dataclass
class EvaluationResult:
    """평가 결과"""

    ragas_metrics: RAGASMetrics
    manufacturing_metrics: ManufacturingMetrics
    quality_metrics: QualityMetrics
    overall_score: float
    is_high_quality: bool  # True if score >= 0.80
    feedback: str


class RAGASEvaluator:
    """RAGAS 기반 평가기"""

    # 품질 필터링 임계값
    QUALITY_THRESHOLD = 0.80
    MIN_CONFIDENCE = 0.75
    MAX_RETRIES = 2

    def __init__(self):
        """초기화"""
        self.evaluation_count = 0
        self.high_quality_count = 0

    def evaluate(
        self,
        query: str,
        response: str,
        rag_context: List[str],
        confidence: float,
        consultation_type: str = ConsultationType.PRODUCT_RECOMMENDATION,
    ) -> EvaluationResult:
        """
        답변 평가

        Args:
            query: 사용자 질문
            response: 모델 응답
            rag_context: RAG 검색 결과
            confidence: 모델 신뢰도
            consultation_type: 상담 타입

        Returns:
            EvaluationResult: 평가 결과
        """
        self.evaluation_count += 1

        logger.info(f"[평가] 평가 시작 #{self.evaluation_count}: {query[:50]}...")

        # 1. RAGAS 메트릭 계산
        ragas_metrics = self._calculate_ragas_metrics(query, response, rag_context)

        # 2. 제조업 특화 메트릭 계산
        manufacturing_metrics = self._calculate_manufacturing_metrics(response, consultation_type)

        # 3. 품질 메트릭 계산
        quality_metrics = self._calculate_quality_metrics(response)

        # 4. 종합 점수 계산
        overall_score = self._calculate_overall_score(
            ragas_metrics, manufacturing_metrics, quality_metrics, confidence
        )

        # 5. 고품질 판정
        is_high_quality = overall_score >= self.QUALITY_THRESHOLD

        # 6. 피드백 생성
        feedback = self._generate_evaluation_feedback(
            overall_score, ragas_metrics, manufacturing_metrics, is_high_quality
        )

        if is_high_quality:
            self.high_quality_count += 1

        result = EvaluationResult(
            ragas_metrics=ragas_metrics,
            manufacturing_metrics=manufacturing_metrics,
            quality_metrics=quality_metrics,
            overall_score=overall_score,
            is_high_quality=is_high_quality,
            feedback=feedback,
        )

        logger.info(
            f"[평가] 평가 완료 #{self.evaluation_count}: "
            f"overall_score={overall_score:.3f}, "
            f"is_high_quality={is_high_quality}, "
            f"pass_rate={self.high_quality_count}/{self.evaluation_count}"
        )

        return result

    def _calculate_ragas_metrics(
        self, query: str, response: str, rag_context: List[str]
    ) -> RAGASMetrics:
        """RAGAS 메트릭 계산"""

        # 1. Faithfulness: 응답이 원본 문서에 충실한가?
        faithfulness = self._calculate_faithfulness(response, rag_context)

        # 2. Answer Relevancy: 응답이 질문과 관련 있는가?
        answer_relevancy = self._calculate_answer_relevancy(query, response)

        # 3. Context Recall: 필요한 컨텍스트가 검색되었는가?
        context_recall = self._calculate_context_recall(rag_context)

        # 4. Context Precision: 검색된 컨텍스트가 정확한가?
        context_precision = self._calculate_context_precision(query, response, rag_context)

        # 종합 점수
        overall_score = (
            faithfulness * 0.25
            + answer_relevancy * 0.35
            + context_recall * 0.2
            + context_precision * 0.2
        )

        return RAGASMetrics(
            faithfulness=min(1.0, max(0.0, faithfulness)),
            answer_relevancy=min(1.0, max(0.0, answer_relevancy)),
            context_recall=min(1.0, max(0.0, context_recall)),
            context_precision=min(1.0, max(0.0, context_precision)),
            overall_score=min(1.0, max(0.0, overall_score)),
        )

    def _calculate_faithfulness(self, response: str, rag_context: List[str]) -> float:
        """
        Faithfulness: 응답이 원본 문서에 충실한가?
        - 응답에 나온 구체적 정보가 RAG 결과에 있는가?
        """
        if not rag_context or not response:
            return 0.5

        # 응답에서 명사 추출 (간단한 휴리스틱)
        response_words = set(response.split())
        context_words = set()
        for context in rag_context:
            context_words.update(context.split())

        # 겹치는 단어 비율
        overlap = len(response_words & context_words)
        total = len(response_words)

        if total == 0:
            return 0.5

        overlap_ratio = overlap / total
        faithfulness = 0.4 + (overlap_ratio * 0.6)  # 0.4-1.0 범위

        return min(1.0, max(0.3, faithfulness))

    def _calculate_answer_relevancy(self, query: str, response: str) -> float:
        """
        Answer Relevancy: 응답이 질문과 관련 있는가?
        - 질문에 나온 단어가 응답에도 나타나는가?
        """
        query_words = set(w.lower() for w in query.split() if len(w) > 2)
        response_words = set(w.lower() for w in response.split() if len(w) > 2)

        if not query_words:
            return 0.7

        overlap = len(query_words & response_words)
        relevancy = overlap / len(query_words)

        # 0.5-1.0 범위로 정규화
        score = 0.5 + (relevancy * 0.5)

        return min(1.0, max(0.3, score))

    def _calculate_context_recall(self, rag_context: List[str]) -> float:
        """
        Context Recall: 충분한 컨텍스트가 검색되었는가?
        - RAG 결과의 개수와 품질
        """
        if not rag_context:
            return 0.3

        context_count = len(rag_context)
        optimal_count = 5

        # 5개가 최적이고, 많을수록 가점
        if context_count >= optimal_count:
            recall = 0.9
        elif context_count >= 3:
            recall = 0.7 + (context_count / optimal_count) * 0.2
        else:
            recall = 0.5 + (context_count / 3) * 0.2

        return min(0.95, max(0.3, recall))

    def _calculate_context_precision(
        self, query: str, response: str, rag_context: List[str]
    ) -> float:
        """
        Context Precision: 검색된 컨텍스트가 정확한가?
        - 응답에서 실제로 사용된 컨텍스트의 비율
        """
        if not rag_context:
            return 0.5

        response_lower = response.lower()
        used_context_count = 0

        for context in rag_context[:3]:  # 상위 3개만 확인
            # 컨텍스트의 주요 단어가 응답에 나타나는지 확인
            context_words = context.lower().split()[:5]
            if any(word in response_lower for word in context_words):
                used_context_count += 1

        precision = used_context_count / min(3, len(rag_context))

        # 0.6-0.95 범위
        score = 0.6 + (precision * 0.35)

        return min(0.95, max(0.4, score))

    def _calculate_manufacturing_metrics(
        self, response: str, consultation_type: str
    ) -> ManufacturingMetrics:
        """제조업 특화 메트릭 계산"""

        # 1. Product Accuracy: 제품 정보 정확성
        product_accuracy = self._evaluate_product_accuracy(response)

        # 2. Defect Diagnosis Quality: 불량 진단 정확성
        defect_quality = self._evaluate_defect_diagnosis(response)

        # 3. Recommendation Relevance: 추천 적합성
        recommendation_relevance = self._evaluate_recommendation(response)

        # 4. Safety Compliance: 안전 규정 준수
        safety_compliance = self._evaluate_safety_compliance(response)

        return ManufacturingMetrics(
            product_accuracy=product_accuracy,
            defect_diagnosis_quality=defect_quality,
            recommendation_relevance=recommendation_relevance,
            safety_compliance=safety_compliance,
        )

    def _evaluate_product_accuracy(self, response: str) -> float:
        """제품 정보 정확성 평가"""
        # 제품 관련 키워드 확인
        product_keywords = ["용기", "제품", "모델", "사양", "규격", "크기"]
        keyword_count = sum(1 for kw in product_keywords if kw in response)

        accuracy = 0.5 + (min(keyword_count, 3) / 3) * 0.45
        return min(1.0, accuracy)

    def _evaluate_defect_diagnosis(self, response: str) -> float:
        """불량 진단 정확성 평가"""
        # 진단 관련 키워드 확인
        diagnosis_keywords = ["원인", "불량", "결함", "손상", "파손", "확인"]
        keyword_count = sum(1 for kw in diagnosis_keywords if kw in response)

        quality = 0.5 + (min(keyword_count, 3) / 3) * 0.45
        return min(1.0, quality)

    def _evaluate_recommendation(self, response: str) -> float:
        """추천 적합성 평가"""
        # 추천 관련 키워드 확인
        recommendation_keywords = ["추천", "추천드립니다", "드립니다", "좋습니다", "적합"]
        keyword_count = sum(1 for kw in recommendation_keywords if kw in response)

        # 응답 길이 확인 (너무 짧으면 감점)
        length_factor = 1.0 if len(response) > 50 else 0.6

        relevance = (0.5 + (min(keyword_count, 2) / 2) * 0.45) * length_factor
        return min(1.0, relevance)

    def _evaluate_safety_compliance(self, response: str) -> float:
        """안전 규정 준수 평가"""
        # 안전 관련 부정적 표현이 없는지 확인
        unsafe_keywords = ["위험", "주의", "금지", "사용금지"]
        unsafe_count = sum(1 for kw in unsafe_keywords if kw in response)

        # 안전 관련 긍정적 표현 확인
        safe_keywords = ["안전", "규정", "기준", "준수"]
        safe_count = sum(1 for kw in safe_keywords if kw in response)

        compliance = 0.7 + (safe_count * 0.1) - (unsafe_count * 0.15)
        return min(1.0, max(0.5, compliance))

    def _calculate_quality_metrics(self, response: str) -> QualityMetrics:
        """응답 품질 메트릭 계산"""

        # 1. Length Appropriate: 길이 적절성
        length_appropriate = 50 < len(response) < 1000

        # 2. Grammar Correct: 문법 정확성 (간단한 휴리스틱)
        grammar_correct = self._check_grammar(response)

        # 3. Sources Cited: 출처 인용
        sources_cited = "출처" in response or "[" in response

        # 4. Confidence Calibrated: 신뢰도 교정
        confidence_calibrated = 0.85  # 기본값

        return QualityMetrics(
            length_appropriate=length_appropriate,
            grammar_correct=grammar_correct,
            sources_cited=sources_cited,
            confidence_calibrated=confidence_calibrated,
        )

    def _check_grammar(self, response: str) -> bool:
        """기본 문법 검사"""
        # 매우 간단한 휴리스틱
        if len(response) < 10:
            return False

        # 문장 끝 확인
        sentence_endings = ["。", ".", "다", "요", "습니다"]
        has_proper_ending = any(response.rstrip().endswith(end) for end in sentence_endings)

        return has_proper_ending

    def _calculate_overall_score(
        self,
        ragas_metrics: RAGASMetrics,
        manufacturing_metrics: ManufacturingMetrics,
        quality_metrics: QualityMetrics,
        confidence: float,
    ) -> float:
        """종합 점수 계산"""

        # RAGAS 스코어: 50% 가중치
        ragas_score = ragas_metrics.overall_score

        # 제조업 메트릭 평균: 30% 가중치
        manufacturing_score = (
            manufacturing_metrics.product_accuracy
            + manufacturing_metrics.defect_diagnosis_quality
            + manufacturing_metrics.recommendation_relevance
            + manufacturing_metrics.safety_compliance
        ) / 4

        # 품질 메트릭: 15% 가중치
        quality_score = (
            sum(
                [
                    1.0 if quality_metrics.length_appropriate else 0.5,
                    1.0 if quality_metrics.grammar_correct else 0.7,
                    1.0 if quality_metrics.sources_cited else 0.8,
                    quality_metrics.confidence_calibrated,
                ]
            )
            / 4
        )

        # 신뢰도: 5% 가중치
        confidence_weight = confidence

        overall = (
            ragas_score * 0.5
            + manufacturing_score * 0.3
            + quality_score * 0.15
            + confidence_weight * 0.05
        )

        return min(1.0, max(0.0, overall))

    def _generate_evaluation_feedback(
        self,
        overall_score: float,
        ragas_metrics: RAGASMetrics,
        manufacturing_metrics: ManufacturingMetrics,
        is_high_quality: bool,
    ) -> str:
        """평가 피드백 생성"""

        feedback_parts = []

        # 종합 평가
        if overall_score >= 0.90:
            feedback_parts.append("✅ 매우 우수한 응답 - 즉시 훈련 데이터로 사용 가능")
        elif overall_score >= 0.80:
            feedback_parts.append("✅ 좋은 응답 - 훈련 데이터로 적합")
        elif overall_score >= 0.70:
            feedback_parts.append("⚠️ 보통 수준 - 검토 후 사용 여부 결정")
        else:
            feedback_parts.append("❌ 개선 필요 - 재생성 권장")

        # 약점 지적
        weaknesses = []
        if ragas_metrics.faithfulness < 0.7:
            weaknesses.append("원본 문서와의 일관성 개선 필요")
        if ragas_metrics.answer_relevancy < 0.7:
            weaknesses.append("질문과의 관련성 개선 필요")
        if manufacturing_metrics.product_accuracy < 0.7:
            weaknesses.append("제품 정보 정확성 개선 필요")

        if weaknesses:
            feedback_parts.append("개선 영역: " + ", ".join(weaknesses))

        return " | ".join(feedback_parts)

    def get_statistics(self) -> Dict[str, Any]:
        """평가 통계 반환"""
        pass_rate = (
            self.high_quality_count / self.evaluation_count * 100
            if self.evaluation_count > 0
            else 0
        )

        return {
            "total_evaluations": self.evaluation_count,
            "high_quality_count": self.high_quality_count,
            "pass_rate": f"{pass_rate:.1f}%",
            "quality_threshold": self.QUALITY_THRESHOLD,
        }
