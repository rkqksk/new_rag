#!/usr/bin/env python3
"""
End-to-End 파이프라인 검증 스크립트
Colima 환경에서 Teacher-Student 전체 워크플로우 테스트

실행:
    python -m pytest tests/test_pipeline_e2e.py -v -s
또는
    python tests/test_pipeline_e2e.py
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
import logging

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.teacher_service import (
    TeacherService,
    TeacherGenerationRequest,
    TrainingDataExporter,
)
from app.services.evaluation_service import RAGASEvaluator, ConsultationType

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PipelineValidator:
    """End-to-End 파이프라인 검증"""
    
    def __init__(self):
        """초기화"""
        self.teacher_service = TeacherService(ollama_host="http://localhost:11434")
        self.evaluator = RAGASEvaluator()
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "stages": {},
            "summary": {}
        }
    
    async def test_teacher_service(self):
        """Stage 1: Teacher 서비스 테스트"""
        logger.info("=" * 80)
        logger.info("Stage 1: Teacher 서비스 테스트")
        logger.info("=" * 80)
        
        try:
            # 샘플 RAG 검색 결과
            rag_context = [
                "50미리 용기는 소량 상품용으로 적합합니다. PET 투명 또는 HDPE 불투명 옵션이 있습니다.",
                "제품 규격: 직경 50mm, 높이 80mm, 용량 약 100ml입니다.",
                "단가: 1,000원/개 (최소주문 1,000개) 또는 1,200원/개 (최소주문 500개)"
            ]
            
            # 테스트 요청
            request = TeacherGenerationRequest(
                query="50미리 용기 추천해줘",
                rag_context=rag_context,
                consultation_type=ConsultationType.PRODUCT_RECOMMENDATION,
                metadata={"test": True}
            )
            
            logger.info(f"[Teacher] 요청: {request.query}")
            logger.info(f"[RAG] 컨텍스트: {len(rag_context)}개 항목")
            
            # Teacher 호출
            response, is_high_quality = await self.teacher_service.generate_training_data(request)
            
            logger.info(f"✓ Teacher 응답 생성 완료")
            logger.info(f"  - 신뢰도: {response.confidence:.2f}")
            logger.info(f"  - 품질 스코어: {response.quality_score:.2f}")
            logger.info(f"  - 고품질 판정: {is_high_quality}")
            logger.info(f"  - 피드백: {response.feedback}")
            logger.info(f"  - 응답 길이: {len(response.teacher_response)} chars")
            
            self.results["stages"]["teacher"] = {
                "status": "✓ 성공",
                "confidence": response.confidence,
                "quality_score": response.quality_score,
                "is_high_quality": is_high_quality,
                "response_length": len(response.teacher_response)
            }
            
            return response, is_high_quality
            
        except Exception as e:
            logger.error(f"✗ Teacher 서비스 실패: {e}")
            self.results["stages"]["teacher"] = {"status": "✗ 실패", "error": str(e)}
            raise
    
    async def test_ragas_evaluation(self, response):
        """Stage 2: RAGAS 평가 테스트"""
        logger.info("\n" + "=" * 80)
        logger.info("Stage 2: RAGAS 평가 시스템 테스트")
        logger.info("=" * 80)
        
        try:
            rag_context = [
                "50미리 용기는 소량 상품용으로 적합합니다.",
                "제품 규격: 직경 50mm, 높이 80mm, 용량 약 100ml입니다.",
                "단가: 1,000원/개"
            ]
            
            eval_result = self.evaluator.evaluate(
                query="50미리 용기 추천해줘",
                response=response.teacher_response,
                rag_context=rag_context,
                confidence=response.confidence,
                consultation_type=ConsultationType.PRODUCT_RECOMMENDATION
            )
            
            logger.info(f"✓ RAGAS 평가 완료")
            logger.info(f"  - 종합 점수: {eval_result.overall_score:.3f}")
            logger.info(f"  - Faithfulness: {eval_result.ragas_metrics.faithfulness:.2f}")
            logger.info(f"  - Answer Relevancy: {eval_result.ragas_metrics.answer_relevancy:.2f}")
            logger.info(f"  - Context Recall: {eval_result.ragas_metrics.context_recall:.2f}")
            logger.info(f"  - Context Precision: {eval_result.ragas_metrics.context_precision:.2f}")
            logger.info(f"  - 고품질 판정: {eval_result.is_high_quality} (threshold: 0.80)")
            logger.info(f"  - 피드백: {eval_result.feedback}")
            
            self.results["stages"]["ragas"] = {
                "status": "✓ 성공",
                "overall_score": eval_result.overall_score,
                "is_high_quality": eval_result.is_high_quality,
                "metrics": {
                    "faithfulness": eval_result.ragas_metrics.faithfulness,
                    "answer_relevancy": eval_result.ragas_metrics.answer_relevancy,
                    "context_recall": eval_result.ragas_metrics.context_recall,
                    "context_precision": eval_result.ragas_metrics.context_precision
                }
            }
            
            return eval_result
            
        except Exception as e:
            logger.error(f"✗ RAGAS 평가 실패: {e}")
            self.results["stages"]["ragas"] = {"status": "✗ 실패", "error": str(e)}
            raise
    
    async def test_data_export(self, response):
        """Stage 3: 데이터 내보내기 테스트"""
        logger.info("\n" + "=" * 80)
        logger.info("Stage 3: 데이터 내보내기 테스트")
        logger.info("=" * 80)
        
        try:
            exporter = TrainingDataExporter()
            
            # 샘플 데이터 생성
            samples = [response] * 3  # 3개 샘플
            
            logger.info(f"[Export] {len(samples)}개 샘플 내보내기 시작")
            
            # JSON 내보내기
            output_file = exporter.export_to_json(samples, "./exports/test_training_data.json")
            
            if output_file:
                logger.info(f"✓ 데이터 내보내기 완료")
                logger.info(f"  - 파일: {output_file}")
                
                # 파일 크기 확인
                file_size = Path(output_file).stat().st_size
                logger.info(f"  - 파일 크기: {file_size / 1024:.2f} KB")
                
                # 내용 확인
                with open(output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"  - 데이터 샘플: {len(data)} 개")
                
                self.results["stages"]["export"] = {
                    "status": "✓ 성공",
                    "file": str(output_file),
                    "file_size_kb": file_size / 1024,
                    "sample_count": len(data)
                }
                
                return output_file
            else:
                raise Exception("내보내기 실패")
                
        except Exception as e:
            logger.error(f"✗ 데이터 내보내기 실패: {e}")
            self.results["stages"]["export"] = {"status": "✗ 실패", "error": str(e)}
            raise
    
    async def run_full_pipeline(self):
        """전체 파이프라인 실행"""
        logger.info("\n" + "=" * 80)
        logger.info("🚀 End-to-End 파이프라인 검증 시작")
        logger.info("=" * 80)
        
        try:
            # Stage 1: Teacher 서비스
            response, is_high_quality = await self.test_teacher_service()
            
            # Stage 2: RAGAS 평가
            eval_result = await self.test_ragas_evaluation(response)
            
            # Stage 3: 데이터 내보내기
            if eval_result.is_high_quality:
                output_file = await self.test_data_export(response)
            else:
                logger.warning("⚠ 품질 부족으로 내보내기 스킵")
                output_file = None
            
            # 결과 요약
            self._print_summary(output_file)
            
            return True
            
        except Exception as e:
            logger.error(f"\n✗ 파이프라인 실패: {e}")
            self._print_summary(None)
            return False
    
    def _print_summary(self, output_file):
        """결과 요약 출력"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 파이프라인 검증 결과")
        logger.info("=" * 80)
        
        # 각 단계 결과
        for stage_name, stage_result in self.results["stages"].items():
            status = stage_result.get("status", "알 수 없음")
            logger.info(f"  {stage_name.upper()}: {status}")
        
        # 최종 결과
        all_passed = all(
            "성공" in str(r.get("status", "")) 
            for r in self.results["stages"].values()
        )
        
        if all_passed:
            logger.info("\n✅ 모든 단계 통과!")
            if output_file:
                logger.info(f"📄 생성된 훈련 데이터: {output_file}")
        else:
            logger.error("\n❌ 일부 단계 실패")
        
        # 통계
        evaluator_stats = self.evaluator.get_statistics()
        logger.info(f"\n📈 평가 통계:")
        logger.info(f"  - 총 평가: {evaluator_stats['total_evaluations']}")
        logger.info(f"  - 고품질: {evaluator_stats['high_quality_count']}")
        logger.info(f"  - 통과율: {evaluator_stats['pass_rate']}")
        
        # 결과 저장
        self._save_results()
    
    def _save_results(self):
        """결과를 JSON으로 저장"""
        try:
            output_path = Path("./exports/pipeline_validation_results.json")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"\n💾 결과 저장됨: {output_path}")
        except Exception as e:
            logger.error(f"결과 저장 실패: {e}")


async def main():
    """메인 함수"""
    validator = PipelineValidator()
    success = await validator.run_full_pipeline()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
