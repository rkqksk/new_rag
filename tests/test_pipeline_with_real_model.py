#!/usr/bin/env python3
"""
실제 Ollama 모델로 파이프라인 검증
더 복잡한 RAG 컨텍스트로 고품질 데이터 생성 테스트

실행:
    python tests/test_pipeline_with_real_model.py
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.teacher_service import (
    TeacherService,
    TeacherGenerationRequest,
    TrainingDataExporter,
)
from app.services.evaluation_service import RAGASEvaluator, ConsultationType

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RealModelValidator:
    """실제 모델을 사용한 파이프라인 검증"""
    
    def __init__(self):
        self.teacher_service = TeacherService()
        self.evaluator = RAGASEvaluator()
        self.high_quality_samples = []
    
    async def test_multiple_consultations(self):
        """여러 상담 유형으로 테스트"""
        
        # 테스트 데이터: (질문, RAG 컨텍스트, 상담 유형)
        test_cases = [
            {
                "query": "50미리 용기 추천해줘",
                "context": [
                    "50미리 용기는 소량 상품용으로 인기 있는 제품입니다.",
                    "PET 투명(1,000원/개), HDPE 불투명(1,200원/개) 옵션이 있습니다.",
                    "최소주문량: PET 1,000개, HDPE 500개입니다.",
                    "배송: 서울 5일, 지방 7일 이내 배송 가능합니다."
                ],
                "type": "product_recommendation"
            },
            {
                "query": "제품에서 냄새가 나요",
                "context": [
                    "플라스틱 용기에서 나는 냄새는 포장재료의 특성입니다.",
                    "새 제품의 경우 통풍이 잘 되는 곳에서 24-48시간 방치하면 완화됩니다.",
                    "환기 후에도 냄새가 지속되면 교환해드립니다.",
                    "냄새의 원인: 포장재 특성 또는 보관 환경입니다."
                ],
                "type": "defect_inquiry"
            },
            {
                "query": "배송은 어떻게 되나요?",
                "context": [
                    "배송 방법: 택배(CJ, 롯데, GS), 직배송 선택 가능합니다.",
                    "배송료: 1회 주문 30,000원 이상 무료, 이하 2,500원입니다.",
                    "배송 기간: 서울 2-3일, 지방 3-5일입니다.",
                    "야간/공휴일 배송도 가능합니다."
                ],
                "type": "transaction"
            }
        ]
        
        logger.info("=" * 80)
        logger.info("🔄 실제 모델로 파이프라인 검증 시작")
        logger.info("=" * 80)
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"\n[Test {i}/{len(test_cases)}] {test_case['query']}")
            logger.info("-" * 60)
            
            try:
                # Teacher 요청
                request = TeacherGenerationRequest(
                    query=test_case["query"],
                    rag_context=test_case["context"],
                    consultation_type=test_case["type"]
                )
                
                # 데이터 생성
                response, is_high_quality = await self.teacher_service.generate_training_data(request)
                
                logger.info(f"  신뢰도: {response.confidence:.2f} | 품질: {response.quality_score:.2f}")
                
                # RAGAS 평가
                eval_result = self.evaluator.evaluate(
                    query=request.query,
                    response=response.teacher_response,
                    rag_context=request.rag_context,
                    confidence=response.confidence,
                    consultation_type=request.consultation_type
                )
                
                logger.info(f"  평가 스코어: {eval_result.overall_score:.3f}")
                logger.info(f"  고품질: {'✓' if eval_result.is_high_quality else '✗'}")
                
                # 고품질이면 저장
                if eval_result.is_high_quality:
                    self.high_quality_samples.append(response)
                    logger.info(f"  → 훈련 데이터로 추가됨 (누적: {len(self.high_quality_samples)})")
                else:
                    logger.info(f"  → 피드백: {eval_result.feedback}")
                    
            except Exception as e:
                logger.error(f"  ✗ 오류: {e}")
        
        logger.info("\n" + "=" * 80)
        logger.info(f"📊 최종 결과")
        logger.info("=" * 80)
        logger.info(f"  총 테스트: {len(test_cases)}")
        logger.info(f"  고품질 샘플: {len(self.high_quality_samples)}")
        logger.info(f"  통과율: {len(self.high_quality_samples) / len(test_cases) * 100:.1f}%")
        
        # 고품질 데이터 내보내기
        if self.high_quality_samples:
            self._export_training_data()
        else:
            logger.warning("⚠ 고품질 샘플이 없어 내보내기를 건너뜁니다.")
    
    def _export_training_data(self):
        """훈련 데이터 내보내기"""
        logger.info("\n📥 훈련 데이터 내보내기")
        logger.info("-" * 60)
        
        try:
            exporter = TrainingDataExporter()
            
            # JSON 내보내기
            output_file = exporter.export_to_json(
                self.high_quality_samples,
                "./exports/validated_training_data.json"
            )
            
            if output_file:
                logger.info(f"✓ 저장됨: {output_file}")
                
                # 파일 확인
                file_size = Path(output_file).stat().st_size
                logger.info(f"  크기: {file_size / 1024:.2f} KB")
                
                # 내용 검증
                with open(output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"  샘플 수: {len(data)} 개")
                    if data:
                        logger.info(f"  메타데이터: {data[0].get('metadata', {})}")
            
        except Exception as e:
            logger.error(f"✗ 내보내기 실패: {e}")


async def main():
    validator = RealModelValidator()
    await validator.test_multiple_consultations()


if __name__ == "__main__":
    asyncio.run(main())
