#!/usr/bin/env python3
"""
Product Catalog Generator
Generates CSV catalogs for both crawled and Excel products, organized by material
"""

import sys
import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.excel_parser_service import ExcelParserService

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class ProductCatalogGenerator:
    """Generate organized CSV catalogs from crawled and Excel data"""

    def __init__(self):
        self.crawled_base = Path("data/crawled_products_final")
        self.excel_base = Path("data/excel_uploads")
        self.excel_processed = self.excel_base / "processed"

        # CSV columns
        self.csv_columns = [
            "product_code", "product_name", "material", "spec", "dimensions",
            "category", "packaging", "mold", "cost", "price", "production",
            "note", "images_count", "image_files", "has_print_area",
            "source_file", "source_type"
        ]

    def generate_crawled_catalogs(self):
        """Generate CSV catalogs for crawled products"""
        logger.info("🔍 Generating catalogs for crawled products...")

        all_products = []
        material_products = defaultdict(list)

        # Walk through crawled_products_final structure
        for category_dir in self.crawled_base.iterdir():
            if not category_dir.is_dir() or category_dir.name.startswith('.'):
                continue

            category_name = category_dir.name  # Bottle, Jar, CapPump

            for material_dir in category_dir.iterdir():
                if not material_dir.is_dir() or material_dir.name.startswith('.'):
                    continue

                material_name = material_dir.name  # PET, PE, PP, etc.
                products_dir = material_dir / "products"

                if not products_dir.exists():
                    continue

                # Process all JSON files
                for json_file in products_dir.glob("*.json"):
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                        product = self._parse_crawled_product(
                            data, category_name, material_name, json_file.name
                        )
                        all_products.append(product)
                        material_products[material_name].append(product)

                    except Exception as e:
                        logger.warning(f"Error parsing {json_file}: {e}")

        # Write material-specific CSVs
        for material, products in material_products.items():
            self._write_material_csv_crawled(material, products)

        # Write master catalog
        master_file = self.crawled_base / "master_catalog.csv"
        self._write_csv(master_file, all_products)

        logger.info(f"✅ Crawled catalogs: {len(all_products)} products, "
                   f"{len(material_products)} materials")

        return all_products

    def _parse_crawled_product(self, data: Dict, category: str, material: str, source_file: str) -> Dict:
        """Parse crawled JSON to CSV row"""
        specs = data.get("specifications", {})
        images = data.get("images", [])

        # Check for print_area
        has_print_area = any('print_area' in img.get('filename', '') for img in images)

        return {
            "product_code": specs.get("제품 코드", "N/A"),
            "product_name": data.get("product_name", ""),
            "material": material,
            "spec": specs.get("사양", ""),
            "dimensions": specs.get("치수", ""),
            "category": f"{category}/{material}",
            "packaging": specs.get("포장", ""),
            "mold": specs.get("금형", ""),
            "cost": "",
            "price": "",
            "production": "",
            "note": specs.get("기타사항", ""),
            "images_count": len(images),
            "image_files": "|".join([img.get("filename", "") for img in images]),
            "has_print_area": str(has_print_area).lower(),
            "source_file": source_file,
            "source_type": "crawled"
        }

    def _write_material_csv_crawled(self, material: str, products: List[Dict]):
        """Write material-specific CSV for crawled products"""
        # Find first product's category to determine path
        if not products:
            return

        category = products[0]["category"].split("/")[0]  # Bottle, Jar, CapPump
        output_dir = self.crawled_base / category / material
        output_file = output_dir / "products_list.csv"

        self._write_csv(output_file, products)
        logger.info(f"  📄 {output_file}: {len(products)} products")

    def generate_excel_catalogs(self):
        """Generate CSV catalogs for Excel products"""
        logger.info("\n📊 Generating catalogs for Excel products...")

        parser = ExcelParserService()
        all_products = []
        material_products = defaultdict(list)

        # Parse all Excel files
        excel_files = list(parser.raw_dir.glob("*.xlsx"))

        for excel_file in excel_files:
            try:
                logger.info(f"  Parsing: {excel_file.name}")
                products_list = parser.parse_excel(excel_file.name)

                for product in products_list:
                    # Extract material from spec or filename
                    material = self._extract_material_from_excel(
                        product.spec, excel_file.name
                    )

                    csv_row = self._parse_excel_product(product, material, excel_file.name)
                    all_products.append(csv_row)
                    material_products[material].append(csv_row)

                logger.info(f"    ✅ {len(products_list)} products extracted")

            except Exception as e:
                logger.error(f"Error parsing {excel_file.name}: {e}")

        # Create organized structure
        for material, products in material_products.items():
            self._write_material_csv_excel(material, products)

        # Write master catalog
        master_file = self.excel_base / "master_catalog.csv"
        self._write_csv(master_file, all_products)

        logger.info(f"\n✅ Excel catalogs: {len(all_products)} products, "
                   f"{len(material_products)} materials")

        return all_products

    def _extract_material_from_excel(self, spec: str, filename: str) -> str:
        """Extract material from spec or filename"""
        spec_upper = spec.upper()
        filename_upper = filename.upper()

        # Check spec first
        if 'PET' in spec_upper and 'PETG' not in spec_upper:
            return 'PET'
        elif 'PETG' in spec_upper:
            return 'PETG'
        elif 'PE' in spec_upper and 'PET' not in spec_upper:
            return 'PE'
        elif 'PP' in spec_upper:
            return 'PP'

        # Check filename
        if 'PET' in filename_upper and 'PETG' not in filename_upper:
            return 'PET'
        elif 'PETG' in filename_upper:
            return 'PETG'
        elif 'PE' in filename_upper and 'PET' not in filename_upper:
            return 'PE'
        elif 'PP' in filename_upper or 'PS' in filename_upper or 'ABS' in filename_upper:
            return 'PP'

        return 'Other'

    def _parse_excel_product(self, product, material: str, source_file: str) -> Dict:
        """Parse ExcelProduct to CSV row"""
        return {
            "product_code": product.code,
            "product_name": f"{product.code} {product.spec}",  # Combine code + spec
            "material": material,
            "spec": product.spec,
            "dimensions": "",  # Not in Excel layout
            "category": f"Unknown/{material}",  # Can't determine category from Excel
            "packaging": product.packaging,
            "mold": product.mold,
            "cost": str(product.cost) if product.cost else "",
            "price": str(product.price) if product.price else "",
            "production": product.production,
            "note": product.note,
            "images_count": len(product.images),
            "image_files": "|".join(product.images),
            "has_print_area": "false",
            "source_file": source_file,
            "source_type": "excel"
        }

    def _write_material_csv_excel(self, material: str, products: List[Dict]):
        """Write material-specific CSV for Excel products"""
        output_dir = self.excel_processed / material
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "products_list.csv"
        self._write_csv(output_file, products)
        logger.info(f"  📄 {output_file}: {len(products)} products")

    def _write_csv(self, filepath: Path, products: List[Dict]):
        """Write products to CSV file"""
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.csv_columns)
            writer.writeheader()
            writer.writerows(products)

    def generate_comparison_report(self, crawled_products: List[Dict], excel_products: List[Dict]):
        """Generate comparison report between Excel and Crawled data"""
        logger.info("\n📊 Generating comparison report...")

        # Index by product code
        crawled_map = {p["product_code"]: p for p in crawled_products if p["product_code"] != "N/A"}
        excel_map = {p["product_code"]: p for p in excel_products}

        # Compare
        missing_in_crawled = [code for code in excel_map if code not in crawled_map]
        missing_in_excel = [code for code in crawled_map if code not in excel_map]
        common_codes = set(crawled_map.keys()) & set(excel_map.keys())

        spec_mismatches = []
        for code in common_codes:
            crawled_spec = crawled_map[code]["spec"]
            excel_spec = excel_map[code]["spec"]
            if crawled_spec != excel_spec:
                spec_mismatches.append({
                    "code": code,
                    "crawled_spec": crawled_spec,
                    "excel_spec": excel_spec
                })

        report = {
            "summary": {
                "total_crawled": len(crawled_products),
                "total_excel": len(excel_products),
                "crawled_with_codes": len(crawled_map),
                "excel_with_codes": len(excel_map),
                "common_codes": len(common_codes),
                "missing_in_crawled": len(missing_in_crawled),
                "missing_in_excel": len(missing_in_excel),
                "spec_mismatches": len(spec_mismatches)
            },
            "details": {
                "missing_in_crawled": missing_in_crawled[:50],  # First 50
                "missing_in_excel": missing_in_excel[:50],
                "spec_mismatches": spec_mismatches[:50]
            }
        }

        # Write report
        report_file = self.excel_processed / "comparison_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ Comparison report saved: {report_file}")
        logger.info(f"   Total crawled: {report['summary']['total_crawled']}")
        logger.info(f"   Total Excel: {report['summary']['total_excel']}")
        logger.info(f"   Missing in crawled: {report['summary']['missing_in_crawled']}")
        logger.info(f"   Missing in Excel: {report['summary']['missing_in_excel']}")
        logger.info(f"   Spec mismatches: {report['summary']['spec_mismatches']}")

        return report


def main():
    """Main execution"""
    generator = ProductCatalogGenerator()

    # Generate catalogs
    crawled_products = generator.generate_crawled_catalogs()
    excel_products = generator.generate_excel_catalogs()

    # Generate comparison report
    generator.generate_comparison_report(crawled_products, excel_products)

    logger.info("\n🎉 All catalogs generated successfully!")


if __name__ == "__main__":
    main()
