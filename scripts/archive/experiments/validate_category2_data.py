#!/usr/bin/env python3
"""
Validate category 2 (packaging) product data quality before image download
"""
import json
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, List, Set

# Configuration
PHASE2_OUTPUT_DIR = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/products_text_only')
VALIDATION_REPORT_PATH = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/validation_reports')
TARGET_CATEGORY = 2

# Validation rules
REQUIRED_FIELDS = [
    'product_id', 'product_url', 'category_id', 'product_name',
    'specifications', 'company_info', 'image_urls', 'image_count',
    'detail_crawled', 'detail_crawled_at'
]

REQUIRED_SPEC_FIELDS = ['코드', '용량', '사이즈', 'MOQ', '재질', '원산지']
REQUIRED_COMPANY_FIELDS = ['제조사', '담당']

# Quality thresholds
MIN_IMAGE_COUNT = 1
MAX_IMAGE_COUNT = 50
MIN_PRODUCT_NAME_LENGTH = 5
MAX_PRODUCT_NAME_LENGTH = 200

class ValidationIssue:
    """Track validation issues"""
    def __init__(self, severity: str, category: str, message: str, product_id: str = None):
        self.severity = severity  # CRITICAL, WARNING, INFO
        self.category = category  # STRUCTURE, DATA_QUALITY, PACKAGING_SPECIFIC
        self.message = message
        self.product_id = product_id
        self.timestamp = datetime.now().isoformat()

class DataValidator:
    def __init__(self):
        self.issues: List[ValidationIssue] = []
        self.stats = defaultdict(int)
        self.products_validated = 0
        self.valid_products = 0
        self.invalid_products = 0

        # Packaging-specific tracking
        self.material_types = Counter()
        self.capacity_formats = Counter()
        self.origin_countries = Counter()
        self.manufacturers = Counter()

    def add_issue(self, severity: str, category: str, message: str, product_id: str = None):
        """Add validation issue"""
        issue = ValidationIssue(severity, category, message, product_id)
        self.issues.append(issue)
        self.stats[f"{severity}_{category}"] += 1

    def validate_structure(self, product: Dict, product_id: str) -> bool:
        """Validate data structure matches batch_00232.jsonl format"""
        is_valid = True

        # Check required fields exist
        for field in REQUIRED_FIELDS:
            if field not in product:
                self.add_issue('CRITICAL', 'STRUCTURE',
                             f"Missing required field: {field}", product_id)
                is_valid = False

        # Validate nested structures
        if 'specifications' in product:
            if not isinstance(product['specifications'], dict):
                self.add_issue('CRITICAL', 'STRUCTURE',
                             "specifications must be a dict", product_id)
                is_valid = False
            else:
                # Check for required spec fields (allow some to be missing)
                present_specs = sum(1 for field in REQUIRED_SPEC_FIELDS
                                  if field in product['specifications'])
                if present_specs < 3:  # At least 3 of 6 required fields
                    self.add_issue('WARNING', 'STRUCTURE',
                                 f"Only {present_specs}/6 specification fields present",
                                 product_id)

        if 'company_info' in product:
            if not isinstance(product['company_info'], dict):
                self.add_issue('CRITICAL', 'STRUCTURE',
                             "company_info must be a dict", product_id)
                is_valid = False
            else:
                # Check for required company fields
                present_company = sum(1 for field in REQUIRED_COMPANY_FIELDS
                                    if field in product['company_info'])
                if present_company == 0:
                    self.add_issue('WARNING', 'STRUCTURE',
                                 "No company_info fields present", product_id)

        if 'image_urls' in product:
            if not isinstance(product['image_urls'], list):
                self.add_issue('CRITICAL', 'STRUCTURE',
                             "image_urls must be a list", product_id)
                is_valid = False

        return is_valid

    def validate_data_quality(self, product: Dict, product_id: str) -> bool:
        """Validate data quality and completeness"""
        is_valid = True

        # Product name validation
        product_name = product.get('product_name', '')
        if not product_name:
            self.add_issue('CRITICAL', 'DATA_QUALITY',
                         "Empty product name", product_id)
            is_valid = False
        elif len(product_name) < MIN_PRODUCT_NAME_LENGTH:
            self.add_issue('WARNING', 'DATA_QUALITY',
                         f"Product name too short: {len(product_name)} chars", product_id)
        elif len(product_name) > MAX_PRODUCT_NAME_LENGTH:
            self.add_issue('WARNING', 'DATA_QUALITY',
                         f"Product name too long: {len(product_name)} chars", product_id)

        # Image validation
        image_urls = product.get('image_urls', [])
        image_count = product.get('image_count', 0)

        if len(image_urls) != image_count:
            self.add_issue('WARNING', 'DATA_QUALITY',
                         f"image_count mismatch: {image_count} vs {len(image_urls)}",
                         product_id)

        if len(image_urls) == 0:
            self.add_issue('WARNING', 'DATA_QUALITY',
                         "No product images", product_id)
        elif len(image_urls) > MAX_IMAGE_COUNT:
            self.add_issue('WARNING', 'DATA_QUALITY',
                         f"Excessive images: {len(image_urls)}", product_id)

        # Validate image URLs
        for idx, url in enumerate(image_urls):
            if not url.startswith('http'):
                self.add_issue('CRITICAL', 'DATA_QUALITY',
                             f"Invalid image URL at index {idx}: {url}", product_id)
                is_valid = False
            elif 'productImages' not in url:
                self.add_issue('WARNING', 'DATA_QUALITY',
                             f"Unexpected image URL pattern: {url}", product_id)

        # Check for duplicate image URLs
        if len(image_urls) != len(set(image_urls)):
            duplicates = len(image_urls) - len(set(image_urls))
            self.add_issue('INFO', 'DATA_QUALITY',
                         f"Duplicate image URLs: {duplicates}", product_id)

        # Validate category
        if product.get('category_id') != TARGET_CATEGORY:
            self.add_issue('CRITICAL', 'DATA_QUALITY',
                         f"Wrong category: {product.get('category_id')}", product_id)
            is_valid = False

        return is_valid

    def validate_packaging_data(self, product: Dict, product_id: str) -> bool:
        """Validate packaging-specific data quality"""
        is_valid = True

        specs = product.get('specifications', {})

        # Extract and validate packaging-specific fields
        material = specs.get('재질', '')
        capacity = specs.get('용량', '')
        size = specs.get('사이즈', '')
        moq = specs.get('MOQ', '')
        origin = specs.get('원산지', '')

        # Material validation (재질)
        if material:
            self.material_types[material] += 1
            # Common packaging materials
            common_materials = ['PET', 'HDPE', 'PP', 'PE', 'PVC', 'PS', 'PETG',
                              'Glass', 'Aluminum', 'Paper']
            has_common = any(mat.upper() in material.upper() for mat in common_materials)
            if not has_common and len(material) > 1:
                self.add_issue('INFO', 'PACKAGING_SPECIFIC',
                             f"Uncommon material: {material}", product_id)
        else:
            self.add_issue('WARNING', 'PACKAGING_SPECIFIC',
                         "Missing material (재질)", product_id)

        # Capacity validation (용량)
        if capacity:
            self.capacity_formats[capacity] += 1
            # Check for capacity format (should contain ml, L, g, kg, etc.)
            has_unit = any(unit in capacity.lower() for unit in ['ml', 'l', 'g', 'kg', 'cc'])
            if not has_unit:
                self.add_issue('WARNING', 'PACKAGING_SPECIFIC',
                             f"Capacity missing unit: {capacity}", product_id)
        else:
            self.add_issue('WARNING', 'PACKAGING_SPECIFIC',
                         "Missing capacity (용량)", product_id)

        # Size validation (사이즈)
        if not size:
            self.add_issue('INFO', 'PACKAGING_SPECIFIC',
                         "Missing size (사이즈)", product_id)

        # MOQ validation
        if moq:
            # Should be a number or number with comma
            if not any(char.isdigit() for char in moq):
                self.add_issue('WARNING', 'PACKAGING_SPECIFIC',
                             f"Invalid MOQ format: {moq}", product_id)
        else:
            self.add_issue('INFO', 'PACKAGING_SPECIFIC',
                         "Missing MOQ", product_id)

        # Origin validation (원산지)
        if origin:
            self.origin_countries[origin] += 1
            common_origins = ['한국', '중국', '일본', 'Korea', 'China', 'Japan']
            if not any(org in origin for org in common_origins):
                self.add_issue('INFO', 'PACKAGING_SPECIFIC',
                             f"Uncommon origin: {origin}", product_id)
        else:
            self.add_issue('INFO', 'PACKAGING_SPECIFIC',
                         "Missing origin (원산지)", product_id)

        # Company info validation
        company_info = product.get('company_info', {})
        manufacturer = company_info.get('제조사', '')

        if manufacturer:
            self.manufacturers[manufacturer] += 1
        else:
            self.add_issue('WARNING', 'PACKAGING_SPECIFIC',
                         "Missing manufacturer (제조사)", product_id)

        return is_valid

    def validate_product(self, product: Dict) -> bool:
        """Run all validations on a product"""
        self.products_validated += 1
        product_id = product.get('product_id', 'UNKNOWN')

        # Skip if not category 2
        if product.get('category_id') != TARGET_CATEGORY:
            return False

        # Run all validations
        structure_valid = self.validate_structure(product, product_id)
        quality_valid = self.validate_data_quality(product, product_id)
        packaging_valid = self.validate_packaging_data(product, product_id)

        is_valid = structure_valid and quality_valid and packaging_valid

        if is_valid:
            self.valid_products += 1
        else:
            self.invalid_products += 1

        return is_valid

def find_phase2_files():
    """Find all Phase 2 output files"""
    files = []
    files.extend(PHASE2_OUTPUT_DIR.glob('worker_*_output.jsonl'))
    files.extend(PHASE2_OUTPUT_DIR.glob('batch_*.jsonl'))
    return sorted(files)

def generate_validation_report(validator: DataValidator) -> str:
    """Generate comprehensive validation report"""
    report_lines = []

    report_lines.append("=" * 80)
    report_lines.append("ONEHAGO CATEGORY 2 (PACKAGING) DATA VALIDATION REPORT")
    report_lines.append("=" * 80)
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")

    # Overall statistics
    report_lines.append("📊 OVERALL STATISTICS")
    report_lines.append("-" * 80)
    report_lines.append(f"Total products validated: {validator.products_validated:,}")
    report_lines.append(f"Valid products: {validator.valid_products:,} ({validator.valid_products/max(validator.products_validated,1)*100:.1f}%)")
    report_lines.append(f"Invalid products: {validator.invalid_products:,} ({validator.invalid_products/max(validator.products_validated,1)*100:.1f}%)")
    report_lines.append("")

    # Issue summary by severity
    critical_count = sum(1 for i in validator.issues if i.severity == 'CRITICAL')
    warning_count = sum(1 for i in validator.issues if i.severity == 'WARNING')
    info_count = sum(1 for i in validator.issues if i.severity == 'INFO')

    report_lines.append("🚨 ISSUES BY SEVERITY")
    report_lines.append("-" * 80)
    report_lines.append(f"CRITICAL: {critical_count:,}")
    report_lines.append(f"WARNING:  {warning_count:,}")
    report_lines.append(f"INFO:     {info_count:,}")
    report_lines.append(f"TOTAL:    {len(validator.issues):,}")
    report_lines.append("")

    # Issue summary by category
    report_lines.append("📋 ISSUES BY CATEGORY")
    report_lines.append("-" * 80)
    for category in ['STRUCTURE', 'DATA_QUALITY', 'PACKAGING_SPECIFIC']:
        category_issues = [i for i in validator.issues if i.category == category]
        report_lines.append(f"{category}: {len(category_issues):,}")
    report_lines.append("")

    # Packaging-specific insights
    report_lines.append("📦 PACKAGING DATA INSIGHTS")
    report_lines.append("-" * 80)

    report_lines.append(f"\nTop 10 Materials (재질):")
    for material, count in validator.material_types.most_common(10):
        report_lines.append(f"  {material}: {count:,} products")

    report_lines.append(f"\nTop 10 Capacities (용량):")
    for capacity, count in validator.capacity_formats.most_common(10):
        report_lines.append(f"  {capacity}: {count:,} products")

    report_lines.append(f"\nOrigin Distribution (원산지):")
    for origin, count in validator.origin_countries.most_common():
        report_lines.append(f"  {origin}: {count:,} products")

    report_lines.append(f"\nTop 10 Manufacturers (제조사):")
    for mfr, count in validator.manufacturers.most_common(10):
        report_lines.append(f"  {mfr}: {count:,} products")

    report_lines.append("")

    # Top issues
    report_lines.append("⚠️  TOP 20 CRITICAL ISSUES")
    report_lines.append("-" * 80)
    critical_issues = [i for i in validator.issues if i.severity == 'CRITICAL'][:20]
    for issue in critical_issues:
        product_info = f" (Product: {issue.product_id})" if issue.product_id else ""
        report_lines.append(f"  [{issue.category}] {issue.message}{product_info}")

    report_lines.append("")
    report_lines.append("💡 RECOMMENDATIONS")
    report_lines.append("-" * 80)

    if critical_count > 0:
        report_lines.append(f"⚠️  {critical_count:,} CRITICAL issues found - Review before image download")

    if validator.invalid_products > validator.valid_products * 0.1:
        report_lines.append(f"⚠️  {validator.invalid_products/max(validator.products_validated,1)*100:.1f}% invalid products - Consider re-crawling")

    missing_images = sum(1 for i in validator.issues
                        if "No product images" in i.message)
    if missing_images > 0:
        report_lines.append(f"ℹ️  {missing_images:,} products without images will be skipped")

    if validator.valid_products > validator.products_validated * 0.9:
        report_lines.append("✅ Data quality is excellent - Safe to proceed with image download")

    report_lines.append("")
    report_lines.append("=" * 80)

    return "\n".join(report_lines)

def main():
    print("🔍 Validating Category 2 (Packaging) Product Data")
    print("=" * 80)
    print(f"Target category: {TARGET_CATEGORY}")
    print()

    # Initialize validator
    validator = DataValidator()

    # Find all Phase 2 files
    phase2_files = find_phase2_files()

    if not phase2_files:
        print("❌ No Phase 2 output files found!")
        return

    print(f"📂 Found {len(phase2_files)} Phase 2 output files")
    print()

    # Process all files
    print("🔄 Validating products...")
    for file_idx, file_path in enumerate(phase2_files, 1):
        print(f"   Processing {file_idx}/{len(phase2_files)}: {file_path.name}", end='\r')

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        product = json.loads(line)

                        # Only validate category 2
                        if product.get('category_id') == TARGET_CATEGORY:
                            validator.validate_product(product)

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            print(f"\n⚠️  Error reading {file_path.name}: {e}")
            continue

    print("\n")

    # Generate report
    report = generate_validation_report(validator)

    # Print to console
    print(report)

    # Save to file
    VALIDATION_REPORT_PATH.mkdir(parents=True, exist_ok=True)
    report_file = VALIDATION_REPORT_PATH / f"category2_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n💾 Full report saved to: {report_file}")

    # Save detailed issues to JSON
    issues_file = VALIDATION_REPORT_PATH / f"category2_issues_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    issues_data = {
        'validation_date': datetime.now().isoformat(),
        'statistics': {
            'total_products': validator.products_validated,
            'valid_products': validator.valid_products,
            'invalid_products': validator.invalid_products,
            'total_issues': len(validator.issues),
            'critical_issues': sum(1 for i in validator.issues if i.severity == 'CRITICAL'),
            'warning_issues': sum(1 for i in validator.issues if i.severity == 'WARNING'),
            'info_issues': sum(1 for i in validator.issues if i.severity == 'INFO')
        },
        'issues': [
            {
                'severity': i.severity,
                'category': i.category,
                'message': i.message,
                'product_id': i.product_id,
                'timestamp': i.timestamp
            }
            for i in validator.issues
        ],
        'packaging_insights': {
            'materials': dict(validator.material_types.most_common(20)),
            'capacities': dict(validator.capacity_formats.most_common(20)),
            'origins': dict(validator.origin_countries),
            'manufacturers': dict(validator.manufacturers.most_common(20))
        }
    }

    with open(issues_file, 'w', encoding='utf-8') as f:
        json.dump(issues_data, f, indent=2, ensure_ascii=False)

    print(f"💾 Detailed issues saved to: {issues_file}")

if __name__ == '__main__':
    main()
