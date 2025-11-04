#!/usr/bin/env python3
"""
Enrich legacy product data with expert knowledge from packaging/manufacturing plugins
"""
import json
import yaml
from pathlib import Path
from typing import Dict, Any

class ProductEnricher:
    def __init__(self):
        self.base_dir = Path('/Users/oypnus/Project/rag-enterprise')
        self.plugins_dir = self.base_dir / 'plugins'
        self.crawled_dir = self.base_dir / 'data' / 'crawled_products_final'

        # Load expert knowledge
        self.materials_db = self._load_yaml(self.plugins_dir / 'packaging_expert' / 'config' / 'materials.yaml')
        self.standards_db = self._load_yaml(self.plugins_dir / 'packaging_expert' / 'config' / 'standards.yaml')
        self.patterns_db = self._load_yaml(self.plugins_dir / 'packaging_expert' / 'config' / 'patterns.yaml')

    def _load_yaml(self, path: Path) -> Dict:
        """Load YAML configuration file"""
        if not path.exists():
            print(f"⚠️  Warning: {path} not found")
            return {}

        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}

    def get_material_info(self, material: str) -> Dict[str, Any]:
        """Get detailed information about a material"""
        material_lower = material.lower()

        # Check plastics
        plastics = self.materials_db.get('plastics', {})
        for key, info in plastics.items():
            if key in material_lower or material_lower in key:
                return {
                    'category': 'plastic',
                    'type': key.upper(),
                    'full_name': info.get('full_name', ''),
                    'resin_code': info.get('resin_code', ''),
                    'properties': info.get('properties', []),
                    'common_uses': info.get('common_uses', []),
                    'barrier_properties': info.get('barrier_properties', {}),
                    'certifications': info.get('certifications', [])
                }

        return {}

    def get_regulatory_info(self, material: str) -> Dict[str, Any]:
        """Get regulatory information for a material"""
        material_info = self.get_material_info(material)
        material_type = material_info.get('type', material).lower()

        regulatory = {
            'fda': {},
            'eu': {},
            'korea': {},
            'reach': {}
        }

        # FDA regulations
        fda = self.standards_db.get('fda', {})
        if 'food_contact' in fda:
            food_contact = fda['food_contact']
            if 'cfr_21_177' in food_contact:
                regulatory['fda']['cfr_21_177'] = food_contact['cfr_21_177']

        # EU regulations
        eu = self.standards_db.get('eu', {})
        if 'plastics_regulation' in eu:
            regulatory['eu']['reg_10_2011'] = eu['plastics_regulation'].get('reg_10_2011', {})

        # Korea regulations (KFDA)
        korea = self.standards_db.get('korea', {})
        regulatory['korea'] = korea

        # REACH
        reach = self.standards_db.get('reach', {})
        regulatory['reach'] = reach

        return regulatory

    def enrich_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich a single product with expert knowledge"""
        specs = product.get('specifications', {})
        material = specs.get('재질(원료)', '')

        if not material:
            return product

        # Add expert enrichment section
        if 'expert_enrichment' not in product:
            product['expert_enrichment'] = {}

        # Add material information
        material_info = self.get_material_info(material)
        if material_info:
            product['expert_enrichment']['material_details'] = material_info

        # Add regulatory information
        regulatory_info = self.get_regulatory_info(material)
        if regulatory_info:
            product['expert_enrichment']['regulatory_compliance'] = regulatory_info

        # Add capacity category
        capacity = specs.get('capacity', '')
        if capacity:
            capacity_category = self._categorize_capacity(capacity)
            product['expert_enrichment']['capacity_category'] = capacity_category

        # Add product type category
        product_name = product.get('product_name', '').lower()
        product_category = self._categorize_product_type(product_name)
        if product_category:
            product['expert_enrichment']['product_category'] = product_category

        return product

    def _categorize_capacity(self, capacity: str) -> Dict[str, str]:
        """Categorize capacity into size categories"""
        try:
            value = int(''.join(filter(str.isdigit, capacity)))
            unit = ''.join(filter(str.isalpha, capacity)).lower()

            if 'ml' in unit:
                if value < 30:
                    return {'size': 'small', 'range': '< 30ml', 'use_case': 'sample/travel'}
                elif value < 100:
                    return {'size': 'medium', 'range': '30-100ml', 'use_case': 'personal care/cosmetics'}
                elif value < 300:
                    return {'size': 'large', 'range': '100-300ml', 'use_case': 'daily use'}
                else:
                    return {'size': 'extra_large', 'range': '> 300ml', 'use_case': 'bulk/refill'}
        except:
            pass

        return {}

    def _categorize_product_type(self, product_name: str) -> str:
        """Categorize product type based on name"""
        if 'bottle' in product_name or '브로우' in product_name or 'bt' in product_name:
            return 'bottle'
        elif 'jar' in product_name or '자' in product_name:
            return 'jar'
        elif 'cap' in product_name or '캡' in product_name:
            return 'cap'
        elif 'pump' in product_name or '펌프' in product_name:
            return 'pump'
        else:
            return 'other'

    def process_all_products(self):
        """Process all products in crawled_products_final"""
        stats = {
            'total': 0,
            'enriched': 0,
            'skipped': 0,
            'errors': 0
        }

        categories = ['Bottle', 'Jar', 'Cap', 'Pump']

        for category in categories:
            category_dir = self.crawled_dir / category
            if not category_dir.exists():
                print(f"⚠️  {category} directory not found")
                continue

            print(f"\nProcessing {category}...")
            category_count = 0

            for material_dir in category_dir.iterdir():
                if not material_dir.is_dir() or material_dir.name.startswith('.'):
                    continue

                products_dir = material_dir / 'products'
                if not products_dir.exists():
                    continue

                for json_file in products_dir.glob('*.json'):
                    stats['total'] += 1

                    try:
                        # Load product
                        with open(json_file, 'r', encoding='utf-8') as f:
                            product = json.load(f)

                        # Enrich product
                        enriched_product = self.enrich_product(product)

                        # Save enriched product
                        with open(json_file, 'w', encoding='utf-8') as f:
                            json.dump(enriched_product, f, ensure_ascii=False, indent=2)

                        stats['enriched'] += 1
                        category_count += 1

                    except Exception as e:
                        print(f"❌ Error processing {json_file}: {e}")
                        stats['errors'] += 1

            print(f"  ✅ Enriched {category_count} {category} products")

        return stats

def main():
    print("=" * 60)
    print("Product Enrichment with Expert Knowledge")
    print("=" * 60)

    enricher = ProductEnricher()
    stats = enricher.process_all_products()

    print(f"\n{'=' * 60}")
    print("Enrichment Complete")
    print(f"{'=' * 60}")
    print(f"Total products: {stats['total']}")
    print(f"Enriched: {stats['enriched']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"Errors: {stats['errors']}")
    print(f"Success rate: {stats['enriched']/stats['total']*100:.1f}%")

if __name__ == '__main__':
    main()
