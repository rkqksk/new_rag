"""
Product Loader Service
Handles loading products from crawled_products_final directory
"""

import json
from pathlib import Path
from typing import Any, Dict, List


def load_products(categories: List[str] = None, base_dir: Path = None) -> Dict[str, Any]:
    """Load all products from crawled_products_final directory

    Args:
        categories: List of category names to load. Defaults to ['Bottle', 'Jar', 'Cap', 'Pump']
        base_dir: Base directory path. If None, uses default path

    Returns:
        Dictionary of products with product_id as key
    """
    if categories is None:
        categories = ["Bottle", "Jar", "Cap", "Pump"]

    if base_dir is None:
        base_dir = Path(__file__).parent.parent.parent  # Go up to project root

    DATA_DIR = base_dir / "data"
    products = {}

    # Load from all specified categories
    for category in categories:
        category_dir = DATA_DIR / "chungjinkorea" / "crawled_products_final" / category
        if not category_dir.exists():
            print(f"⚠️  Category directory not found: {category}")
            continue

        for material_dir in category_dir.iterdir():
            if not material_dir.is_dir() or material_dir.name.startswith("."):
                continue

            # Get material from directory name (PE, PET, PP, PETG, Other, etc.)
            material_from_dir = material_dir.name

            products_dir = material_dir / "products"
            if not products_dir.exists():
                continue

            for json_file in products_dir.glob("*.json"):
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        product = json.load(f)

                    # Extract product_id from filename (idx_13.json -> idx_13)
                    product_id = json_file.stem

                    # Normalize product structure
                    specs = product.get("specifications", {})
                    enrichment = product.get("expert_enrichment", {})
                    pricing = product.get("pricing", {})

                    # Add print_area_url to specifications if exists
                    if "print_area_url" in product:
                        specs["print_area_url"] = product["print_area_url"]

                    # Get material: priority is specs, fallback to directory name
                    material = specs.get("재질(원료)", "") or material_from_dir

                    # Get spec: priority is 사양 (full spec), fallback to dimensions (neck size only)
                    spec = specs.get("사양", "")
                    if not spec or "Ø" not in spec:
                        dimensions = specs.get("dimensions", "")
                        if dimensions and "Ø" in dimensions:
                            spec = dimensions

                    # Get category_type from product
                    category_type = product.get("category_type", category.upper())

                    products[product_id] = {
                        "product_id": product_id,
                        "product_name": product.get("product_name", ""),
                        "product_code": specs.get("제품 코드", "N/A"),
                        "capacity": specs.get("capacity", ""),
                        "material": material,
                        "moq": specs.get("moq", ""),
                        "spec": spec,
                        "dimensions": specs.get("사양", ""),
                        "neck_size": specs.get("neck_size", ""),
                        "images": product.get("images", []),
                        "specifications": specs,
                        "pricing": pricing,
                        "print_area_url": product.get("print_area_url", ""),
                        "category": category,
                        "category_type": category_type,
                        "tags": product.get("tags", []),
                        "source": product.get("source", ""),
                        "material_details": enrichment.get("material_details", {}),
                        "regulatory_compliance": enrichment.get("regulatory_compliance", {}),
                        "capacity_category": enrichment.get("capacity_category", {}),
                        "product_category": enrichment.get("product_category", ""),
                    }
                except Exception as e:
                    print(f"Error loading {json_file}: {e}")
                    continue

    return products
