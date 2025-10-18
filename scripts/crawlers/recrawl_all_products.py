#!/usr/bin/env python3
"""
전체 제품 재크롤링 스크립트
총 398개 제품 (Bottle: 68페이지, Jar: 4페이지, Cap&Pump: 14페이지)

실행:
    python scripts/crawlers/recrawl_all_products.py

결과:
    - data/crawled_products_updated/ 디렉토리에 저장
    - 완료 후 검증 리포트 생성
"""

import asyncio
import json
import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from chungjin_crawler import ChungjinCrawler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('recrawl_all_products.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RecrawlManager:
    """전체 제품 재크롤링 관리자"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.old_data_dir = self.project_root / "data" / "crawled_products_organized"
        self.new_data_dir = self.project_root / "data" / "crawled_products_updated"
        self.backup_dir = self.project_root / "data" / "crawled_products_backup"

        # 카테고리 정보
        self.categories = {
            "Bottle": {
                "url": "http://chungjinkorea.com/kr/product/list.php?part_idx=1",
                "pages": 68,
                "expected_products": 340  # 추정치
            },
            "Jar": {
                "url": "http://chungjinkorea.com/kr/product/list.php?part_idx=2",
                "pages": 4,
                "expected_products": 20  # 추정치
            },
            "Cap&Pump": {
                "url": "http://chungjinkorea.com/kr/product/list.php?part_idx=3",
                "pages": 14,
                "expected_products": 38  # 추정치
            }
        }

    async def run_full_recrawl(self, delay: int = 2):
        """전체 재크롤링 실행"""
        start_time = datetime.now()

        logger.info("="*80)
        logger.info("청진코리아 전체 제품 재크롤링 시작")
        logger.info("="*80)
        logger.info(f"시작 시간: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"목표 디렉토리: {self.new_data_dir}")
        logger.info(f"카테고리: {len(self.categories)}개")
        logger.info(f"예상 제품: {sum(cat['expected_products'] for cat in self.categories.values())}개")
        logger.info(f"Delay 설정: {delay}초")
        logger.info("="*80)

        # 새 디렉토리 준비
        if self.new_data_dir.exists():
            logger.warning(f"기존 {self.new_data_dir} 삭제 중...")
            shutil.rmtree(self.new_data_dir)

        self.new_data_dir.mkdir(parents=True, exist_ok=True)

        # 크롤러 초기화
        crawler = ChungjinCrawler(
            output_dir=str(self.new_data_dir),
            browser_type="webkit",  # macOS 최적화
            use_playwright=False
        )

        # 전체 카테고리 크롤링
        try:
            summary = await crawler.crawl_all_categories(delay=delay)

            end_time = datetime.now()
            duration = end_time - start_time

            # 결과 분석
            total_products = summary['total_products']
            total_success = summary['total_success']
            total_error = summary['total_error']
            success_rate = (total_success / total_products * 100) if total_products > 0 else 0

            logger.info("")
            logger.info("="*80)
            logger.info("재크롤링 완료!")
            logger.info("="*80)
            logger.info(f"종료 시간: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"소요 시간: {duration}")
            logger.info(f"총 제품: {total_products}개")
            logger.info(f"성공: {total_success}개 ({success_rate:.1f}%)")
            logger.info(f"실패: {total_error}개")
            logger.info("="*80)

            # 검증 리포트 생성
            await self._generate_validation_report(summary, duration)

            # 샘플 데이터 검증
            await self._validate_sample_data()

            # 데이터 비교 분석
            await self._compare_with_old_data()

            return summary

        except Exception as e:
            logger.error(f"재크롤링 실패: {e}", exc_info=True)
            raise

    async def _generate_validation_report(self, summary: dict, duration):
        """검증 리포트 생성"""
        logger.info("\n" + "="*80)
        logger.info("검증 리포트 생성 중...")
        logger.info("="*80)

        report = {
            "crawl_info": {
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": duration.total_seconds(),
                "duration_formatted": str(duration)
            },
            "categories": {},
            "overall_stats": {
                "total_products": summary['total_products'],
                "total_success": summary['total_success'],
                "total_error": summary['total_error'],
                "success_rate": summary['total_success'] / summary['total_products'] * 100
            },
            "data_quality": {}
        }

        # 카테고리별 통계
        for cat_summary in summary['categories']:
            cat_name = cat_summary['category']

            report['categories'][cat_name] = {
                "total_products": cat_summary['total_products'],
                "success": cat_summary['success'],
                "error": cat_summary['error'],
                "success_rate": cat_summary['success'] / cat_summary['total_products'] * 100
            }

        # 데이터 품질 검사
        quality_checks = await self._check_data_quality()
        report['data_quality'] = quality_checks

        # 리포트 저장
        report_path = self.new_data_dir / "validation_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"✓ 검증 리포트 저장: {report_path}")

        # 콘솔 출력
        logger.info("\n--- 데이터 품질 요약 ---")
        logger.info(f"재질 정보 추출률: {quality_checks['material_extraction_rate']:.1f}%")
        logger.info(f"제품코드 추출률: {quality_checks['product_code_extraction_rate']:.1f}%")
        logger.info(f"사양 정보 추출률: {quality_checks['specification_extraction_rate']:.1f}%")
        logger.info(f"이미지 수집률: {quality_checks['image_extraction_rate']:.1f}%")

        return report

    async def _check_data_quality(self) -> dict:
        """데이터 품질 검사"""
        json_files = list(self.new_data_dir.glob("idx_*.json"))

        if not json_files:
            logger.warning("JSON 파일을 찾을 수 없습니다!")
            return {
                "total_files": 0,
                "material_extraction_rate": 0,
                "product_code_extraction_rate": 0,
                "specification_extraction_rate": 0,
                "image_extraction_rate": 0
            }

        total = len(json_files)
        material_count = 0
        product_code_count = 0
        spec_count = 0
        image_count = 0

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                specs = data.get('specifications', {})

                # 재질 정보 확인
                if any('재질' in key or 'Material' in key for key in specs.keys()):
                    material_count += 1

                # 제품코드 확인
                if any('코드' in key or 'Code' in key or '제품명' in key or 'Product' in key for key in specs.keys()):
                    product_code_count += 1

                # 사양 정보 확인 (최소 1개 이상의 스펙 항목)
                if len(specs) > 0:
                    spec_count += 1

                # 이미지 확인
                if len(data.get('images', [])) > 0:
                    image_count += 1

            except Exception as e:
                logger.warning(f"품질 검사 실패: {json_file.name} - {e}")

        return {
            "total_files": total,
            "material_extraction_rate": (material_count / total * 100) if total > 0 else 0,
            "product_code_extraction_rate": (product_code_count / total * 100) if total > 0 else 0,
            "specification_extraction_rate": (spec_count / total * 100) if total > 0 else 0,
            "image_extraction_rate": (image_count / total * 100) if total > 0 else 0,
            "files_with_material": material_count,
            "files_with_product_code": product_code_count,
            "files_with_specifications": spec_count,
            "files_with_images": image_count
        }

    async def _validate_sample_data(self):
        """샘플 데이터 검증"""
        logger.info("\n" + "="*80)
        logger.info("샘플 데이터 검증 중...")
        logger.info("="*80)

        # 랜덤 샘플 5개 선택
        json_files = list(self.new_data_dir.glob("idx_*.json"))

        if not json_files:
            logger.warning("검증할 JSON 파일이 없습니다!")
            return

        import random
        sample_files = random.sample(json_files, min(5, len(json_files)))

        for json_file in sample_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                logger.info(f"\n--- {json_file.name} ---")
                logger.info(f"제품명: {data.get('product_name', 'N/A')}")
                logger.info(f"이미지 개수: {len(data.get('images', []))}개")
                logger.info(f"스펙 항목:")

                for key, value in data.get('specifications', {}).items():
                    logger.info(f"  - {key}: {value}")

                if data.get('print_area_local_path'):
                    logger.info(f"인쇄영역 PDF: 있음")
                else:
                    logger.info(f"인쇄영역 PDF: 없음")

            except Exception as e:
                logger.warning(f"샘플 검증 실패: {json_file.name} - {e}")

    async def _compare_with_old_data(self):
        """기존 데이터와 비교 분석"""
        logger.info("\n" + "="*80)
        logger.info("기존 데이터와 비교 분석 중...")
        logger.info("="*80)

        if not self.old_data_dir.exists():
            logger.warning(f"기존 데이터 디렉토리 없음: {self.old_data_dir}")
            return

        # 기존 JSON 파일 개수
        old_json_files = list(self.old_data_dir.rglob("idx_*.json"))
        new_json_files = list(self.new_data_dir.glob("idx_*.json"))

        old_count = len(old_json_files)
        new_count = len(new_json_files)

        logger.info(f"기존 데이터: {old_count}개 JSON 파일")
        logger.info(f"새 데이터: {new_count}개 JSON 파일")
        logger.info(f"증감: {new_count - old_count:+d}개")

        # 샘플 비교 (같은 idx가 있는 경우)
        comparison_samples = []

        for new_json in new_json_files[:5]:  # 처음 5개만 비교
            idx = new_json.stem.replace('idx_', '')

            # 기존 데이터에서 같은 idx 찾기
            old_matches = [f for f in old_json_files if f.stem == f"idx_{idx}"]

            if old_matches:
                try:
                    with open(new_json, 'r', encoding='utf-8') as f:
                        new_data = json.load(f)
                    with open(old_matches[0], 'r', encoding='utf-8') as f:
                        old_data = json.load(f)

                    comparison = {
                        "idx": idx,
                        "old_specs_count": len(old_data.get('specifications', {})),
                        "new_specs_count": len(new_data.get('specifications', {})),
                        "old_images_count": len(old_data.get('images', [])),
                        "new_images_count": len(new_data.get('images', [])),
                        "improvement": len(new_data.get('specifications', {})) > len(old_data.get('specifications', {}))
                    }

                    comparison_samples.append(comparison)

                except Exception as e:
                    logger.warning(f"비교 실패: idx_{idx} - {e}")

        if comparison_samples:
            logger.info("\n--- 샘플 비교 결과 ---")
            for comp in comparison_samples:
                logger.info(f"\nidx_{comp['idx']}:")
                logger.info(f"  스펙: {comp['old_specs_count']}개 → {comp['new_specs_count']}개")
                logger.info(f"  이미지: {comp['old_images_count']}개 → {comp['new_images_count']}개")
                logger.info(f"  개선: {'✓' if comp['improvement'] else '-'}")

    async def backup_and_migrate(self):
        """기존 데이터 백업 및 새 데이터로 교체"""
        logger.info("\n" + "="*80)
        logger.info("데이터 마이그레이션 시작...")
        logger.info("="*80)

        if not self.new_data_dir.exists():
            logger.error(f"새 데이터 디렉토리 없음: {self.new_data_dir}")
            return False

        # 기존 데이터 백업
        if self.old_data_dir.exists():
            logger.info(f"기존 데이터 백업 중: {self.old_data_dir} → {self.backup_dir}")

            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)

            shutil.copytree(self.old_data_dir, self.backup_dir)
            logger.info(f"✓ 백업 완료: {self.backup_dir}")

            # 기존 데이터 삭제
            logger.info(f"기존 데이터 삭제 중: {self.old_data_dir}")
            shutil.rmtree(self.old_data_dir)

        # 새 데이터를 organized 디렉토리로 이동
        logger.info(f"새 데이터 이동 중: {self.new_data_dir} → {self.old_data_dir}")
        shutil.copytree(self.new_data_dir, self.old_data_dir)

        logger.info("="*80)
        logger.info("✅ 마이그레이션 완료!")
        logger.info("="*80)
        logger.info(f"백업: {self.backup_dir}")
        logger.info(f"현재 데이터: {self.old_data_dir}")
        logger.info(f"임시 데이터: {self.new_data_dir} (필요시 삭제 가능)")

        return True


async def main():
    """메인 실행 함수"""
    manager = RecrawlManager()

    print("\n" + "="*80)
    print("청진코리아 전체 제품 재크롤링")
    print("="*80)
    print(f"예상 소요 시간: 30-60분")
    print(f"예상 제품 수: 약 398개")
    print(f"결과 저장 위치: {manager.new_data_dir}")
    print("="*80)

    # 사용자 확인
    response = input("\n재크롤링을 시작하시겠습니까? (y/n): ")

    if response.lower() != 'y':
        print("재크롤링 취소됨.")
        return

    try:
        # 재크롤링 실행
        summary = await manager.run_full_recrawl(delay=2)

        # 마이그레이션 여부 확인
        print("\n" + "="*80)
        print("재크롤링이 완료되었습니다!")
        print("="*80)

        migrate_response = input("\n기존 데이터를 백업하고 새 데이터로 교체하시겠습니까? (y/n): ")

        if migrate_response.lower() == 'y':
            await manager.backup_and_migrate()
        else:
            print(f"\n새 데이터는 {manager.new_data_dir}에 보관됩니다.")
            print(f"나중에 수동으로 마이그레이션할 수 있습니다.")

        print("\n✅ 모든 작업이 완료되었습니다!")

    except KeyboardInterrupt:
        print("\n\n재크롤링이 중단되었습니다.")
    except Exception as e:
        logger.error(f"재크롤링 실패: {e}", exc_info=True)
        print(f"\n❌ 재크롤링 실패: {e}")


if __name__ == "__main__":
    asyncio.run(main())
