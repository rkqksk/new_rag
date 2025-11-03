#!/usr/bin/env python3
"""
FREEMOLD DATA REORGANIZATION
Parse and clean the products_text_complete.jsonl file
Reorganize manufacturer field to separate contact information into proper fields
"""

import json
import re
from pathlib import Path

INPUT_FILE = Path("/Users/oypnus/Project/rag-enterprise/data/freemold/crawled/products_text_complete.jsonl")
OUTPUT_FILE = Path("/Users/oypnus/Project/rag-enterprise/data/freemold/crawled/products_text_reorganized.jsonl")

print("\n" + "="*80)
print("🔄 FREEMOLD DATA REORGANIZATION")
print("="*80)
print("Reorganizing manufacturer field and contact information...")
print("="*80 + "\n")

def parse_manufacturer_field(manufacturer_text):
    """
    Parse manufacturer field containing contact information
    Extract: manufacturer name, phone, fax, email
    """
    if not manufacturer_text:
        return {
            "name": None,
            "phone": None,
            "fax": None,
            "email": None
        }

    result = {
        "name": None,
        "phone": None,
        "fax": None,
        "email": None
    }

    # Clean up the text - remove extra whitespace and newlines
    text = manufacturer_text.strip()

    # Extract phone number
    phone_match = re.search(r'전화\s*:?\s*([\d\-\/]+)', text)
    if phone_match:
        result["phone"] = phone_match.group(1).strip()

    # Extract fax number
    fax_match = re.search(r'팩스\s*:?\s*([\d\-\/]*)', text)
    if fax_match:
        fax_value = fax_match.group(1).strip()
        result["fax"] = fax_value if fax_value else None

    # Extract email
    email_match = re.search(r'회사메일\s*:?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text)
    if email_match:
        result["email"] = email_match.group(1).strip()

    return result

def reorganize_product(product):
    """
    Reorganize a product record
    Parse manufacturer field and separate contact information
    """
    # Make a copy to avoid modifying original
    organized = product.copy()

    # Parse the manufacturer field
    manufacturer_text = product.get("manufacturer", "")
    parsed = parse_manufacturer_field(manufacturer_text)

    # Set organized manufacturer name (if we can extract company info)
    # For now, we'll use the company name from email domain or set to null
    organized["manufacturer"] = parsed["name"] or None

    # Create/update contact field with structured data
    organized["contact"] = {
        "phone": parsed["phone"],
        "fax": parsed["fax"],
        "email": parsed["email"]
    }

    # Clean up empty contact fields
    organized["contact"] = {k: v for k, v in organized["contact"].items() if v}

    return organized

# Process the file
total_products = 0
reorganized_products = 0
errors = 0

try:
    with open(INPUT_FILE, 'r', encoding='utf-8') as infile, \
         open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:

        for line_num, line in enumerate(infile, 1):
            try:
                product = json.loads(line)
                reorganized = reorganize_product(product)
                outfile.write(json.dumps(reorganized, ensure_ascii=False) + '\n')

                total_products += 1
                reorganized_products += 1

                if line_num % 1000 == 0:
                    print(f"Processed: {line_num} products...")

            except json.JSONDecodeError as e:
                print(f"❌ Error on line {line_num}: {e}")
                errors += 1
                continue
            except Exception as e:
                print(f"❌ Error processing product on line {line_num}: {e}")
                errors += 1
                continue

    print(f"\n✅ REORGANIZATION COMPLETE")
    print("="*80)
    print(f"Total products processed: {total_products}")
    print(f"Successfully reorganized: {reorganized_products}")
    print(f"Errors: {errors}")
    print(f"Output file: {OUTPUT_FILE}")
    print("="*80)

    # Show sample output
    print("\n📋 SAMPLE OUTPUT (First 2 Records):")
    print("-"*80)

    with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 2:
                break
            product = json.loads(line)
            print(f"\n{'Record ' + str(i+1)}:")
            print(json.dumps(product, indent=2, ensure_ascii=False))
            print("-"*80)

    print("\n✨ Data reorganization complete!")
    print(f"Original file: {INPUT_FILE}")
    print(f"New file: {OUTPUT_FILE}")

except Exception as e:
    print(f"❌ Fatal error: {e}")
    import traceback
    traceback.print_exc()
