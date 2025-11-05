"""
Manufacturing Expert SKILL - Usage Examples

Shows how to use manufacturing-expert SKILL for document processing
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the skill
from .claude.skills.manufacturing_expert.scripts import skill


def example_1_classify_document():
    """Example 1: Classify a manufacturing document"""

    print("=" * 60)
    print("Example 1: Document Classification")
    print("=" * 60)

    document = {
        "content": "SOP-001: Injection Molding Process. This procedure outlines the standard operating procedure for injection molding operations. Equipment: Haitian MA900. Process parameters: Temperature 200°C, Pressure 80 MPa.",
        "filename": "sop-injection-molding.pdf"
    }

    result = skill.execute('classify', document)

    print(f"\n✓ Document Type: {result['doc_type']}")
    print(f"✓ Categories: {', '.join(result['categories'])}")
    print(f"✓ Domain: {result['domain']}")


def example_2_extract_terminology():
    """Example 2: Extract quality metrics and terminology"""

    print("\n" + "=" * 60)
    print("Example 2: Terminology Extraction")
    print("=" * 60)

    document = {
        "content": """
        Quality Control Report - Molding Line A

        Process Capability: Cpk = 1.67, Cp = 1.85
        Overall Equipment Effectiveness (OEE): 87.5%
        Defect Rate: 234 PPM
        Mean Time Between Failures (MTBF): 156 hours
        First Pass Yield (FPY): 96.8%

        Compliance: ISO 9001:2015 certified
        Regulatory: FDA 21 CFR Part 820 compliant
        """,
        "filename": "quality-report-2024.pdf"
    }

    result = skill.execute('extract', document)

    print(f"\n✓ Extracted {len(result['terminology'])} terms:")
    for term in sorted(result['terminology'])[:10]:
        print(f"  • {term}")


def example_3_full_processing():
    """Example 3: Complete document processing with enrichment"""

    print("\n" + "=" * 60)
    print("Example 3: Full Document Processing")
    print("=" * 60)

    document = {
        "content": """
        FMEA - Injection Molding Process

        Failure Mode: Short shot
        Severity: 8
        Occurrence: 4
        Detection: 6
        RPN: 192

        Recommended Actions:
        1. Increase injection pressure
        2. Verify material temperature
        3. Check mold venting

        Process Capability Target: Cpk ≥ 1.33
        Current OEE: 82%
        Target OEE: 85%

        Standards: ISO 9001, IATF 16949
        """,
        "filename": "fmea-injection-molding.pdf"
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

        # Show quality metrics if extracted
        if hasattr(metadata, 'extracted_entities'):
            quality_metrics = metadata.extracted_entities.get('quality_metrics', [])
            if quality_metrics:
                print(f"\n  Quality Metrics Detected:")
                for metric in quality_metrics[:5]:
                    print(f"    • {metric['type']}: {metric['value']}")


def example_4_quick_helpers():
    """Example 4: Using quick helper functions"""

    print("\n" + "=" * 60)
    print("Example 4: Quick Helper Functions")
    print("=" * 60)

    document = {
        "content": "Equipment Specification: CNC Milling Machine. Precision: ±0.001mm. Compliance: ISO 13485.",
        "filename": "cnc-spec.pdf"
    }

    # Using quick access functions
    classification = skill.classify_document(document)
    terminology = skill.extract_terminology(document)

    print(f"\n✓ Quick Classification: {classification['doc_type']}")
    print(f"✓ Quick Terminology: {len(terminology['terminology'])} terms")


def example_5_batch_processing():
    """Example 5: Batch processing multiple documents"""

    print("\n" + "=" * 60)
    print("Example 5: Batch Document Processing")
    print("=" * 60)

    documents = [
        {"content": "SOP-001: Assembly procedure", "filename": "sop-assembly.pdf"},
        {"content": "Equipment Calibration Record. Cpk: 1.45", "filename": "calibration.pdf"},
        {"content": "Deviation Report NCR-2024-001. Root cause analysis.", "filename": "ncr.pdf"},
    ]

    print(f"\n✓ Processing {len(documents)} documents...")

    for i, doc in enumerate(documents, 1):
        result = skill.execute('classify', doc)
        print(f"  {i}. {doc['filename']}: {result['doc_type']}")


if __name__ == "__main__":
    print("\n" + "🏭" * 30)
    print("Manufacturing Expert SKILL - Usage Examples")
    print("🏭" * 30 + "\n")

    # Run all examples
    example_1_classify_document()
    example_2_extract_terminology()
    example_3_full_processing()
    example_4_quick_helpers()
    example_5_batch_processing()

    print("\n" + "=" * 60)
    print("✅ All examples completed successfully!")
    print("=" * 60 + "\n")
