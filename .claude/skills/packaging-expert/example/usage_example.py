"""
Packaging Expert SKILL - Usage Examples

Shows how to use packaging-expert SKILL for document processing
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the skill
from .claude.skills.packaging_expert.scripts import skill


def example_1_classify_packaging_document():
    """Example 1: Classify a packaging document"""

    print("=" * 60)
    print("Example 1: Packaging Document Classification")
    print("=" * 60)

    document = {
        "content": "Material Specification: PET Resin for Bottle Manufacturing. Grade: IV 0.82, Density: 1.38 g/cm³. FDA 21 CFR Part 177.1630 compliant.",
        "filename": "pet-material-spec.pdf"
    }

    result = skill.execute('classify', document)

    print(f"\n✓ Document Type: {result['doc_type']}")
    print(f"✓ Categories: {', '.join(result['categories'])}")
    print(f"✓ Domain: {result['domain']}")


def example_2_extract_materials_and_properties():
    """Example 2: Extract materials, dimensions, and barrier properties"""

    print("\n" + "=" * 60)
    print("Example 2: Material & Property Extraction")
    print("=" * 60)

    document = {
        "content": """
        Container Specification: PET Bottle

        Materials:
        - Body: PET (Polyethylene Terephthalate)
        - Closure: PP (Polypropylene) 28/410
        - Label: BOPP film

        Dimensions:
        - Capacity: 500 ml
        - Height: 210 mm
        - Diameter: 65 mm
        - Neck size: 28/410
        - Wall thickness: 0.35 mm
        - Weight: 18.5 g

        Barrier Properties:
        - Oxygen transmission rate: <0.8 cc/pkg/day
        - Moisture vapor transmission: <1.2 g/pkg/day
        - Burst strength: 280 psi

        Regulatory:
        - FDA 21 CFR Part 177 compliant
        - EU Regulation 10/2011
        - BPA-free
        """,
        "filename": "pet-bottle-500ml.pdf"
    }

    result = skill.execute('extract', document)

    print(f"\n✓ Extracted {len(result['terminology'])} terms:")
    for term in sorted(result['terminology'])[:15]:
        print(f"  • {term}")


def example_3_regulatory_compliance_check():
    """Example 3: Process regulatory compliance document"""

    print("\n" + "=" * 60)
    print("Example 3: Regulatory Compliance Processing")
    print("=" * 60)

    document = {
        "content": """
        Food Contact Compliance Certificate

        Material: HDPE (High-Density Polyethylene)
        Application: Food packaging containers

        Regulatory Compliance:
        - FDA 21 CFR 177.1520 (Olefin polymers)
        - EU Regulation (EC) 1935/2004 (Food contact materials)
        - EU Regulation (EU) 10/2011 (Plastic materials)
        - REACH compliant
        - RoHS compliant

        Migration Testing:
        - Overall migration: <10 mg/dm²
        - Specific migration (heavy metals): Below detection limit

        Test Method: EN 1186
        Certificate Number: FC-2024-12345
        """,
        "filename": "hdpe-food-contact-certificate.pdf"
    }

    result = skill.execute('process', document)

    print("\n✓ Processing Results:")
    print(f"  Status: {result.get('status', 'Unknown')}")

    if hasattr(result, 'metadata'):
        metadata = result.metadata
        print(f"  Document Type: {metadata.doc_type}")
        print(f"  Domain: {metadata.domain}")
        print(f"  Terminology Count: {len(metadata.terminology)}")
        print(f"  Categories: {', '.join(metadata.categories)}")


def example_4_container_drawing_analysis():
    """Example 4: Analyze container technical drawing"""

    print("\n" + "=" * 60)
    print("Example 4: Container Drawing Analysis")
    print("=" * 60)

    document = {
        "content": """
        Technical Drawing: PETG Cosmetic Jar

        Part Number: JAR-PETG-50
        Material: PETG (Polyethylene Terephthalate Glycol-modified)

        Dimensions:
        - Capacity: 50 ml
        - Overall height: 62 mm
        - Outside diameter: 68 mm
        - Inside diameter: 64 mm
        - Neck finish: 70/400
        - Wall thickness: 2.0 mm
        - Base thickness: 3.5 mm

        Features:
        - Double wall construction
        - UV resistant
        - Recyclability code: 7 (Other)
        - Compatible with: Cream, lotion, gel products

        Surface Treatment: UV coating
        Color: Clear (transparent)
        """,
        "filename": "petg-jar-50ml-drawing.pdf"
    }

    result = skill.execute('classify', document)

    print(f"\n✓ Document Type: {result['doc_type']}")
    print(f"✓ Analysis Categories: {', '.join(result['categories'])}")


def example_5_batch_material_specs():
    """Example 5: Batch process multiple material specifications"""

    print("\n" + "=" * 60)
    print("Example 5: Batch Material Specification Processing")
    print("=" * 60)

    documents = [
        {"content": "PET bottle material. Capacity 1000ml. FDA approved.", "filename": "pet-1l.pdf"},
        {"content": "HDPE container. Barrier properties: excellent. REACH compliant.", "filename": "hdpe-container.pdf"},
        {"content": "Glass bottle Type III. Capacity 250ml. Amber color.", "filename": "glass-amber.pdf"},
        {"content": "Aluminum can. Coated interior. BPA-free. Recyclable.", "filename": "aluminum-can.pdf"},
    ]

    print(f"\n✓ Processing {len(documents)} material specifications...")

    for i, doc in enumerate(documents, 1):
        result = skill.execute('classify', doc)
        terminology = skill.execute('extract', doc)
        print(f"  {i}. {doc['filename']}: {result['doc_type']} ({len(terminology['terminology'])} terms)")


if __name__ == "__main__":
    print("\n" + "📦" * 30)
    print("Packaging Expert SKILL - Usage Examples")
    print("📦" * 30 + "\n")

    # Run all examples
    example_1_classify_packaging_document()
    example_2_extract_materials_and_properties()
    example_3_regulatory_compliance_check()
    example_4_container_drawing_analysis()
    example_5_batch_material_specs()

    print("\n" + "=" * 60)
    print("✅ All examples completed successfully!")
    print("=" * 60 + "\n")
