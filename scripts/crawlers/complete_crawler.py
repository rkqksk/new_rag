#!/usr/bin/env python3
"""
완전 크롤링 - 남김없이 전체 제품 크롤링

구조: Category/Material/{products, images, print_area}
범위: idx 13 ~ 970 (전체 958개)
라벨: bottle, jar, cappump, special

Usage:
    python scripts/crawlers/complete_crawler.py
    python scripts/crawlers/complete_crawler.py --start 13 --end 970 --delay 2.0
"""

import asyncio
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
import sys
import shutil

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from chungjin_crawler import ChungjinCrawler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('complete_crawl.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CompleteCrawler:
    """완전 크롤링 - Category/Material 구조"""

    def __init__(self, base_dir: str = "data/crawled_products_final"):
        self.base_dir = Path(base_dir)
        self.categories = ["Bottle", "CapPump", "Jar"]
        self.materials = ["PE", "PET", "PETG", "PP", "Other"]
        self.subdirs = ["products", "images", "print_area"]

        # 카테고리 라벨
        self.category_labels = {
            "Bottle": "bottle",
            "CapPump": "cappump",
            "Jar": "jar",
            None: "special"
        }

        # 통계
        self.stats = {
            "total_attempted": 0,
            "already_exists": 0,
            "newly_crawled": 0,
            "failed": 0,
            "by_category": {cat: 0 for cat in self.categories},
            "by_category_new": {cat: 0 for cat in self.categories},
            "special_folder": 0
        }

        # 진행 상황 파일
        self.progress_file = Path("complete_crawl_progress.json")
        self.load_progress()

    def load_progress(self):
        """진행 상황 로드"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                self.progress = json.load(f)
        else:
            self.progress = {
                "last_idx": 0,
                "completed_indices": [],
                "failed_indices": [],
                "started_at": None,
                "updated_at": None
            }

    def save_progress(self, idx: int, success: bool):
        """진행 상황 저장"""
        if success:
            if idx not in self.progress["completed_indices"]:
                self.progress["completed_indices"].append(idx)
        else:
            if idx not in self.progress["failed_indices"]:
                self.progress["failed_indices"].append(idx)

        self.progress["last_idx"] = idx
        self.progress["updated_at"] = datetime.now().isoformat()

        if not self.progress["started_at"]:
            self.progress["started_at"] = datetime.now().isoformat()

        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)

    def detect_category(self, product_data: dict) -> str:
        """카테고리 자동 감지"""
        product_name = product_data.get("product_name", "").lower()

        # CapPump (가장 구체적)
        if any(kw in product_name for kw in ["펌프", "pump", "캡", "cap"]):
            return "CapPump"

        # Jar
        if any(kw in product_name for kw in ["크림", "jar", "cream"]):
            return "Jar"

        # Bottle
        if any(kw in product_name for kw in ["용기", "병", "브로우", "bottle", "ml"]):
            return "Bottle"

        return None  # 특별폴더

    def extract_material(self, product_data: dict) -> str:
        """재질 추출"""
        specs = product_data.get("specifications", {})

        for key, value in specs.items():
            if '재질' in key or 'Material' in key.lower() or '원료' in key:
                material_value = str(value).upper()

                if 'PETG' in material_value:
                    return "PETG"
                elif 'PET' in material_value:
                    return "PET"
                elif 'PE' in material_value:
                    return "PE"
                elif 'PP' in material_value:
                    return "PP"

        return "Other"

    def get_target_path(self, category: str, material: str) -> Path:
        """타겟 경로 가져오기"""
        if category is None:
            # 특별폴더
            return self.base_dir / "특별폴더" / "Other"
        else:
            return self.base_dir / category / material

    def check_if_exists(self, idx: int) -> tuple:
        """제품이 이미 존재하는지 확인 (category, material 반환)"""
        # 모든 가능한 위치 확인
        for category in self.categories + [None]:
            for material in self.materials:
                if category is None:
                    check_path = self.base_dir / "특별폴더" / "Other" / "products" / f"idx_{idx}.json"
                else:
                    check_path = self.base_dir / category / material / "products" / f"idx_{idx}.json"

                if check_path.exists():
                    return (category, material)

        return (None, None)

    async def crawl_and_organize(
        self,
        start_idx: int,
        end_idx: int,
        delay: float = 2.0
    ):
        """완전 크롤링 실행"""

        start_time = datetime.now()

        logger.info("=" * 80)
        logger.info("완전 크롤링 - 남김없이 전체 제품")
        logger.info("=" * 80)
        logger.info(f"범위: idx {start_idx} ~ {end_idx}")
        logger.info(f"총 개수: {end_idx - start_idx + 1}개")
        logger.info(f"구조: Category/Material/{{products, images, print_area}}")
        logger.info(f"지연: {delay}초")
        logger.info("=" * 80)

        # 임시 크롤 폴더
        temp_dir = self.base_dir / "temp_complete_crawl"
        temp_dir.mkdir(exist_ok=True)

        # 크롤러 초기화
        crawler = ChungjinCrawler(
            output_dir=str(temp_dir),
            browser_type="webkit",
            use_playwright=False
        )

        # 전체 범위 크롤링
        for idx in range(start_idx, end_idx + 1):
            self.stats["total_attempted"] += 1

            # 이미 존재 확인
            existing_category, existing_material = self.check_if_exists(idx)

            if existing_category is not None:
                logger.info(f"⏭️  idx {idx}: 이미 존재 ({existing_category}/{existing_material})")
                self.stats["already_exists"] += 1
                continue

            url = f"http://chungjinkorea.com/kr/product/view.php?idx={idx}"

            try:
                logger.info(f"\n[{self.stats['total_attempted']}/{end_idx - start_idx + 1}] 크롤링 idx {idx}...")

                # 크롤링
                crawl_result = await crawler.crawl_product(url)

                # 실제 데이터 추출
                product_data = crawl_result.get("data", {})

                # 유효성 확인
                product_name = product_data.get("product_name", "")
                if not product_name or product_name == "Unknown Product":
                    logger.warning(f"⚠️  idx {idx}: 제품 없음")
                    self.stats["failed"] += 1
                    self.save_progress(idx, success=False)
                    await asyncio.sleep(delay)
                    continue

                # 카테고리 감지
                category = self.detect_category(product_data)
                material = self.extract_material(product_data)

                # 라벨 추가
                if category is None:
                    product_data["category_label"] = "special"
                else:
                    product_data["category_label"] = self.category_labels[category]

                # 타겟 경로
                target_dir = self.get_target_path(category, material)

                # 폴더 구조 생성
                for subdir in self.subdirs:
                    (target_dir / subdir).mkdir(parents=True, exist_ok=True)

                # JSON 저장
                json_path = target_dir / "products" / f"idx_{idx}.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(product_data, f, ensure_ascii=False, indent=2)

                # 이미지 이동
                if product_data.get("downloaded_images"):
                    await self._move_images(product_data, idx, target_dir, temp_dir)

                # Print area 이동
                if product_data.get("print_area_local_path"):
                    await self._move_print_area(product_data, idx, target_dir, temp_dir)

                category_name = category if category else "특별폴더"
                logger.info(f"✅ idx {idx}: {product_data.get('product_name')} → {category_name}/{material}")

                self.stats["newly_crawled"] += 1

                if category:
                    self.stats["by_category"][category] += 1
                    self.stats["by_category_new"][category] += 1
                else:
                    self.stats["special_folder"] += 1

                self.save_progress(idx, success=True)

                # Rate limiting
                if idx < end_idx:
                    await asyncio.sleep(delay)

            except Exception as e:
                logger.error(f"❌ idx {idx}: {e}")
                self.stats["failed"] += 1
                self.save_progress(idx, success=False)
                await asyncio.sleep(delay)

        # 크롤러 정리
        await crawler.automation.close_browser()

        # 임시 폴더 정리
        if temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
            except:
                pass

        # 최종 보고서
        self._print_final_report(start_time)

    async def _move_images(self, product_data: dict, idx: int, target_dir: Path, temp_dir: Path):
        """이미지 이동"""
        images_target = target_dir / "images"
        images_target.mkdir(exist_ok=True)

        for img_info in product_data.get("downloaded_images", []):
            local_path = img_info.get("local_path")
            if local_path and Path(local_path).exists():
                try:
                    target_file = images_target / Path(local_path).name
                    shutil.move(str(local_path), str(target_file))
                    img_info["local_path"] = str(target_file)
                except Exception as e:
                    logger.warning(f"이미지 이동 실패 idx {idx}: {e}")

    async def _move_print_area(self, product_data: dict, idx: int, target_dir: Path, temp_dir: Path):
        """Print area PDF 이동"""
        print_area_target = target_dir / "print_area"
        print_area_target.mkdir(exist_ok=True)

        local_path = product_data.get("print_area_local_path")
        if local_path and Path(local_path).exists():
            try:
                target_file = print_area_target / Path(local_path).name
                shutil.move(str(local_path), str(target_file))
                product_data["print_area_local_path"] = str(target_file)
            except Exception as e:
                logger.warning(f"Print area 이동 실패 idx {idx}: {e}")

    def _print_final_report(self, start_time: datetime):
        """최종 보고서"""
        duration = (datetime.now() - start_time).total_seconds()

        logger.info("\n" + "=" * 80)
        logger.info("완전 크롤링 최종 보고서")
        logger.info("=" * 80)
        logger.info(f"시도: {self.stats['total_attempted']}개")
        logger.info(f"이미 존재: {self.stats['already_exists']}개")
        logger.info(f"새로 크롤링: {self.stats['newly_crawled']}개")
        logger.info(f"실패: {self.stats['failed']}개")
        logger.info(f"소요 시간: {duration/60:.1f}분")

        logger.info("\n📊 새로 크롤링된 제품 (카테고리별):")
        for category in self.categories:
            new_count = self.stats["by_category_new"][category]
            if new_count > 0:
                logger.info(f"  {category}: {new_count}개")

        if self.stats["special_folder"] > 0:
            logger.info(f"  특별폴더: {self.stats['special_folder']}개")

        # 전체 집계
        logger.info("\n📦 전체 제품 수량 (현재 데이터):")
        total_all = 0

        for category in self.categories:
            category_total = 0
            for material in self.materials:
                products_dir = self.base_dir / category / material / "products"
                if products_dir.exists():
                    count = len(list(products_dir.glob("idx_*.json")))
                    category_total += count

            if category_total > 0:
                logger.info(f"  {category}: {category_total}개")
                total_all += category_total

        # 특별폴더
        special_dir = self.base_dir / "특별폴더" / "Other" / "products"
        if special_dir.exists():
            special_count = len(list(special_dir.glob("idx_*.json")))
            if special_count > 0:
                logger.info(f"  특별폴더: {special_count}개")
                total_all += special_count

        logger.info(f"\n✅ 전체 총합: {total_all}개 제품")
        logger.info("=" * 80)


async def main():
    parser = argparse.ArgumentParser(description="완전 크롤링")
    parser.add_argument("--start", type=int, default=13, help="시작 인덱스")
    parser.add_argument("--end", type=int, default=970, help="종료 인덱스")
    parser.add_argument("--delay", type=float, default=2.0, help="요청 간 지연(초)")

    args = parser.parse_args()

    crawler = CompleteCrawler()
    await crawler.crawl_and_organize(
        start_idx=args.start,
        end_idx=args.end,
        delay=args.delay
    )


if __name__ == "__main__":
    asyncio.run(main())
