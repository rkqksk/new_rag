#!/usr/bin/env python3
"""
FREEMOLD DATA VALIDATION SCRIPT
Comprehensive validation of all product data fields
Checks: specifications, materials, contact info, images, naming conventions, etc.
"""

import json
import re
from pathlib import Path
from collections import defaultdict

INPUT_FILE = Path("/Users/oypnus/Project/rag-enterprise/data/freemold/crawled/products_text_complete.jsonl")

print("\n" + "="*80)
print("🔍 FREEMOLD DATA VALIDATION - COMPREHENSIVE QUALITY CHECK")
print("="*80 + "\n")

# Statistics collection
stats = {
    "total_products": 0,
    "fields_present": defaultdict(int),
    "fields_null": defaultdict(int),
    "fields_empty": defaultdict(int),
    "data_quality": {},
}

# Field validators
validation_results = {
    "product_id": {"valid": 0, "invalid": 0, "issues": []},
    "name": {"valid": 0, "invalid": 0, "issues": []},
    "category": {"valid": 0, "invalid": 0, "issues": []},
    "specs": {"valid": 0, "invalid": 0, "issues": []},
    "contact": {"valid": 0, "invalid": 0, "issues": []},
    "images": {"valid": 0, "invalid": 0, "issues": []},
    "url": {"valid": 0, "invalid": 0, "issues": []},
}

def validate_product_id(product_id):
    """Product ID should be numeric and non-empty"""
    if not product_id:
        return False, "Empty product ID"
    if not str(product_id).isdigit():
        return False, f"Non-numeric product ID: {product_id}"
    return True, None

def validate_name(name):
    """Product name should be present and meaningful"""
    if not name:
        return False, "Empty product name"
    if len(name) < 2:
        return False, f"Name too short: {name}"
    return True, None

def validate_specs(specs):
    """Specifications should have structure (specification, material fields)"""
    if specs is None:
        return False, "Null specifications"
    if not isinstance(specs, dict):
        return False, f"Specs not a dict: {type(specs)}"

    # Check for misarranged data (phone numbers in specs, etc.)
    spec_text = str(specs).lower()
    if re.search(r'전화|팩스|phone|fax', spec_text):
        return False, "Contact info mixed in specs"

    # Check for at least one field
    if len(specs) == 0:
        return False, "Empty specifications"

    return True, None

def validate_contact(contact):
    """Contact info should be properly structured"""
    if contact is None:
        return False, "Null contact info"
    if not isinstance(contact, dict):
        return False, f"Contact not a dict: {type(contact)}"

    # Should have at least one contact method
    has_data = any([contact.get("phone"), contact.get("email"), contact.get("fax")])
    if not has_data:
        return False, "No contact information"

    # Validate email if present
    email = contact.get("email")
    if email:
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return False, f"Invalid email format: {email}"

    return True, None

def validate_images(images):
    """Images should be a list with valid URLs"""
    if not isinstance(images, list):
        return False, f"Images not a list: {type(images)}"

    # Should have some images
    if len(images) == 0:
        return False, "No images"

    # Check image URL format
    for img in images:
        if not isinstance(img, str):
            return False, f"Image not string: {type(img)}"
        if not img.startswith("http"):
            return False, f"Invalid image URL: {img}"

    return True, None

def validate_url(url):
    """URL should be valid and properly formatted"""
    if not url:
        return False, "Empty URL"
    if not url.startswith("https://www.freemold.net"):
        return False, f"Invalid freemold URL: {url}"
    if "pIdx=" not in url:
        return False, "URL missing product ID parameter"
    return True, None

# Process all products
print("📋 Processing products...\n")

try:
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            product = json.loads(line)
            stats["total_products"] += 1

            # Track field presence
            for key in product.keys():
                stats["fields_present"][key] += 1
                if product[key] is None:
                    stats["fields_null"][key] += 1
                elif product[key] == "" or product[key] == [] or product[key] == {}:
                    stats["fields_empty"][key] += 1

            # Validate individual fields
            if "product_id" in product:
                valid, issue = validate_product_id(product["product_id"])
                if valid:
                    validation_results["product_id"]["valid"] += 1
                else:
                    validation_results["product_id"]["invalid"] += 1
                    if issue and len(validation_results["product_id"]["issues"]) < 3:
                        validation_results["product_id"]["issues"].append((line_num, issue))

            if "name" in product:
                valid, issue = validate_name(product["name"])
                if valid:
                    validation_results["name"]["valid"] += 1
                else:
                    validation_results["name"]["invalid"] += 1
                    if issue and len(validation_results["name"]["issues"]) < 3:
                        validation_results["name"]["issues"].append((line_num, issue))

            if "specs" in product:
                valid, issue = validate_specs(product["specs"])
                if valid:
                    validation_results["specs"]["valid"] += 1
                else:
                    validation_results["specs"]["invalid"] += 1
                    if issue and len(validation_results["specs"]["issues"]) < 3:
                        validation_results["specs"]["issues"].append((line_num, issue))

            if "contact" in product:
                valid, issue = validate_contact(product["contact"])
                if valid:
                    validation_results["contact"]["valid"] += 1
                else:
                    validation_results["contact"]["invalid"] += 1
                    if issue and len(validation_results["contact"]["issues"]) < 3:
                        validation_results["contact"]["issues"].append((line_num, issue))

            if "images" in product:
                valid, issue = validate_images(product["images"])
                if valid:
                    validation_results["images"]["valid"] += 1
                else:
                    validation_results["images"]["invalid"] += 1
                    if issue and len(validation_results["images"]["issues"]) < 3:
                        validation_results["images"]["issues"].append((line_num, issue))

            if "url" in product:
                valid, issue = validate_url(product["url"])
                if valid:
                    validation_results["url"]["valid"] += 1
                else:
                    validation_results["url"]["invalid"] += 1
                    if issue and len(validation_results["url"]["issues"]) < 3:
                        validation_results["url"]["issues"].append((line_num, issue))

            if line_num % 1000 == 0:
                print(f"✓ Processed {line_num} products...")

    print(f"\n✅ Processed {stats['total_products']} total products")

    # Print validation results
    print("\n" + "="*80)
    print("📊 VALIDATION RESULTS BY FIELD")
    print("="*80 + "\n")

    for field, results in validation_results.items():
        total = results["valid"] + results["invalid"]
        if total > 0:
            valid_pct = (results["valid"] / total * 100)
            status = "✅" if valid_pct >= 95 else "⚠️"

            print(f"{status} {field.upper()}")
            print(f"   Valid: {results['valid']}/{total} ({valid_pct:.1f}%)")

            if results["invalid"] > 0:
                print(f"   Invalid: {results['invalid']}")
                if results["issues"]:
                    for line_num, issue in results["issues"][:2]:
                        print(f"     Line {line_num}: {issue}")
            print()

    # Field presence summary
    print("="*80)
    print("📋 FIELD PRESENCE ANALYSIS")
    print("="*80 + "\n")

    for field in sorted(stats["fields_present"].keys()):
        count = stats["fields_present"][field]
        null_count = stats["fields_null"].get(field, 0)
        empty_count = stats["fields_empty"].get(field, 0)
        filled = count - null_count - empty_count
        filled_pct = (filled / count * 100) if count > 0 else 0

        status = "✅" if filled_pct >= 80 else "⚠️"
        print(f"{status} {field}: {filled}/{count} filled ({filled_pct:.1f}%)")

        if null_count > 0:
            print(f"    └─ {null_count} null values")
        if empty_count > 0:
            print(f"    └─ {empty_count} empty values")

    # Calculate overall quality score
    print("\n" + "="*80)
    print("📈 OVERALL DATA QUALITY SCORE")
    print("="*80 + "\n")

    total_validations = sum(r["valid"] + r["invalid"] for r in validation_results.values())
    total_valid = sum(r["valid"] for r in validation_results.values())

    if total_validations > 0:
        quality_score = (total_valid / total_validations * 100)

        if quality_score >= 95:
            grade = "A (Excellent)"
        elif quality_score >= 85:
            grade = "B (Good)"
        elif quality_score >= 75:
            grade = "C (Fair)"
        elif quality_score >= 65:
            grade = "D (Poor)"
        else:
            grade = "F (Critical)"

        print(f"Quality Score: {quality_score:.1f}% ({grade})")
        print(f"Valid validations: {total_valid}/{total_validations}")

    # Recommendations
    print("\n" + "="*80)
    print("💡 RECOMMENDATIONS")
    print("="*80 + "\n")

    recommendations = []

    # Check for contact issues
    if validation_results["contact"]["invalid"] > 0:
        recommendations.append("✓ Review contact information - some records missing valid contact data")

    # Check for specification issues
    if validation_results["specs"]["invalid"] > 0:
        recommendations.append("✓ Audit specification fields - may have mixed/misplaced data")

    # Check for image issues
    if validation_results["images"]["invalid"] > 0:
        recommendations.append("✓ Verify image URLs - some may be broken or invalid")

    # Check for URL issues
    if validation_results["url"]["invalid"] > 0:
        recommendations.append("✓ Validate product URLs - some may be malformed")

    if not recommendations:
        print("✅ No major issues detected - data quality is good!")
    else:
        for rec in recommendations:
            print(rec)

    print("\n" + "="*80)
    print("✨ Validation complete!")
    print("="*80)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
