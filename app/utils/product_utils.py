"""
Product utility functions for RAG system
제품 데이터 처리 및 무결성 검증 유틸리티
"""

import os
import re
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


def generate_image_urls(
    product_id: str,
    category: str,
    base_path: str = "/Users/oypnus/Project/rag-enterprise/data/crawled_products_final",
    max_images: int = 3
) -> List[str]:
    """
    제품 ID와 카테고리를 기반으로 이미지 URL 목록 생성

    Args:
        product_id: 제품 ID (예: "idx_123")
        category: 카테고리 경로 (예: "Bottle/PET")
        base_path: 데이터 루트 경로
        max_images: 최대 이미지 개수

    Returns:
        존재하는 이미지 URL 목록 (검증된 경로만 반환)

    Example:
        >>> generate_image_urls("idx_123", "Bottle/PET")
        ['/data/.../Bottle/PET/images/idx_123_main_1.jpg', ...]
    """
    image_urls = []

    # Extract idx number from product_id (idx_123 → 123)
    idx_match = re.search(r'idx_(\d+)', product_id)
    if not idx_match:
        logger.warning(f"Invalid product_id format: {product_id}")
        return image_urls

    idx = idx_match.group(1)

    # Build image directory path
    images_dir = Path(base_path) / category / "images"

    if not images_dir.exists():
        logger.debug(f"Image directory not found: {images_dir}")
        return image_urls

    # Check for main images (idx_123_main_1.jpg, idx_123_main_2.jpg, ...)
    for i in range(1, max_images + 1):
        image_filename = f"idx_{idx}_main_{i}.jpg"
        image_path = images_dir / image_filename

        if image_path.exists():
            # Return relative URL for API response
            relative_url = f"/data/crawled_products_final/{category}/images/{image_filename}"
            image_urls.append(relative_url)

    if not image_urls:
        logger.debug(f"No images found for product: {product_id} in {category}")

    return image_urls


def validate_product_integrity(
    product: Dict[str, Any],
    require_images: bool = True,
    require_specs: bool = True
) -> Dict[str, Any]:
    """
    제품 데이터 무결성 검증 및 보완

    Args:
        product: 제품 데이터 딕셔너리
        require_images: 이미지 필수 여부
        require_specs: 스펙 필수 여부

    Returns:
        검증 및 보완된 제품 데이터

    Raises:
        ValueError: 필수 필드가 없을 경우
    """
    # 1. 필수 필드 검증
    required_fields = ["product_id", "product_name", "category"]
    missing_fields = [field for field in required_fields if not product.get(field)]

    if missing_fields:
        raise ValueError(f"Missing required fields: {missing_fields}")

    # 2. 이미지 URL 생성 및 추가
    if "image_urls" not in product or not product["image_urls"]:
        product["image_urls"] = generate_image_urls(
            product["product_id"],
            product["category"]
        )

    # 3. 이미지 무결성 검증
    if require_images and not product["image_urls"]:
        logger.warning(
            f"⚠️ No images found for product: {product['product_id']} "
            f"({product['product_name']})"
        )
        product["has_images"] = False
    else:
        product["has_images"] = bool(product["image_urls"])

    # 4. 스펙 무결성 검증
    if "specifications" not in product:
        product["specifications"] = {}

    if require_specs and not product["specifications"]:
        logger.warning(
            f"⚠️ No specifications for product: {product['product_id']} "
            f"({product['product_name']})"
        )
        product["has_specs"] = False
    else:
        product["has_specs"] = bool(product["specifications"])

    # 5. print_area_url 기본값 설정
    if "print_area_url" not in product:
        product["print_area_url"] = None

    # 6. 무결성 점수 계산
    integrity_score = 0.0
    integrity_score += 0.4 if product.get("has_images") else 0.0
    integrity_score += 0.4 if product.get("has_specs") else 0.0
    integrity_score += 0.2 if product.get("print_area_url") else 0.0

    product["integrity_score"] = round(integrity_score, 2)

    # 7. 완전성 플래그
    product["is_complete"] = (
        product["has_images"] and
        product["has_specs"] and
        product["print_area_url"] is not None
    )

    return product


def batch_validate_products(
    products: List[Dict[str, Any]],
    require_images: bool = False,  # 대량 검증 시 경고만 발생
    require_specs: bool = False,
    min_integrity_score: float = 0.0
) -> List[Dict[str, Any]]:
    """
    여러 제품 데이터 일괄 검증 및 필터링

    Args:
        products: 제품 데이터 리스트
        require_images: 이미지 필수 여부 (False면 경고만)
        require_specs: 스펙 필수 여부 (False면 경고만)
        min_integrity_score: 최소 무결성 점수 (0.0~1.0)

    Returns:
        검증된 제품 리스트 (무결성 점수 기준 정렬)
    """
    validated_products = []

    for product in products:
        try:
            validated = validate_product_integrity(
                product,
                require_images=require_images,
                require_specs=require_specs
            )

            # 무결성 점수 필터링
            if validated["integrity_score"] >= min_integrity_score:
                validated_products.append(validated)
            else:
                logger.debug(
                    f"Product filtered due to low integrity score: "
                    f"{validated['product_id']} (score: {validated['integrity_score']})"
                )

        except ValueError as e:
            logger.error(f"Product validation failed: {e}")
            continue

    # 무결성 점수 기준 정렬 (높은 순)
    validated_products.sort(
        key=lambda x: x["integrity_score"],
        reverse=True
    )

    # 통계 로깅
    total = len(products)
    validated = len(validated_products)
    complete = sum(1 for p in validated_products if p["is_complete"])

    logger.info(
        f"📊 Batch validation: {validated}/{total} products validated, "
        f"{complete} complete (integrity ≥ 1.0)"
    )

    return validated_products


def enrich_product_with_metadata(
    product: Dict[str, Any],
    include_image_count: bool = True,
    include_spec_count: bool = True
) -> Dict[str, Any]:
    """
    제품 데이터에 추가 메타데이터 보강

    Args:
        product: 제품 데이터
        include_image_count: 이미지 개수 추가
        include_spec_count: 스펙 필드 개수 추가

    Returns:
        메타데이터가 추가된 제품 데이터
    """
    if include_image_count:
        product["image_count"] = len(product.get("image_urls", []))

    if include_spec_count:
        specs = product.get("specifications", {})
        product["spec_field_count"] = len(specs) if isinstance(specs, dict) else 0

    return product


def extract_capacity_from_name(product_name: str) -> Optional[str]:
    """
    제품명에서 용량 추출 (ml 또는 g)

    Args:
        product_name: 제품명

    Returns:
        추출된 용량 (예: "50ml", "100g") 또는 None

    Example:
        >>> extract_capacity_from_name("50ml 헤비브로우용기")
        "50ml"
    """
    # ml 우선 검색
    ml_pattern = re.compile(r'(\d+)\s*ml', re.IGNORECASE)
    match = ml_pattern.search(product_name)
    if match:
        return match.group(1) + 'ml'

    # g 검색
    g_pattern = re.compile(r'(\d+)\s*g\b', re.IGNORECASE)
    match = g_pattern.search(product_name)
    if match:
        return match.group(1) + 'g'

    return None


def extract_material_from_category(category: str) -> Optional[str]:
    """
    카테고리 경로에서 재질 추출

    Args:
        category: 카테고리 경로 (예: "Bottle/PET")

    Returns:
        재질 (PET, PE, PP, PETG, Other) 또는 None

    Example:
        >>> extract_material_from_category("Bottle/PET")
        "PET"
    """
    if '/' in category:
        material = category.split('/')[-1]
        if material in ["PET", "PE", "PP", "PETG", "Other"]:
            return material

    return None
