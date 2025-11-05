#!/usr/bin/env python3
"""
Comprehensive Test Suite for Parsing and Chunking System

Tests all parsers (PDF, JSON, JSONL, TXT, CSV) and all chunking strategies
(semantic, sentence, recursive, sliding window).
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from parsers import parse_document, get_parser_factory
from chunking import get_chunker


def print_section(title):
    """Print formatted section header"""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def test_json_parser():
    """Test JSON parser with nested objects"""
    print_section("TEST 1: JSON Parser")

    # Create sample JSON file
    json_data = {
        "product": {
            "name": "PET Bottle 500ml",
            "specs": {
                "material": "PET",
                "capacity": "500ml",
                "neck_size": "28/410"
            },
            "manufacturer": {
                "name": "ABC Plastics",
                "location": "Korea"
            }
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(json_data, f)
        json_file = f.name

    try:
        result = parse_document(json_file, options={
            'flatten': True,
            'include_keys': True
        })

        print(f"✅ Parse success: {result.success}")
        print(f"📊 Content length: {len(result.content)} characters")
        print(f"📝 Preview:\n{result.content[:300]}...")

        assert result.success, "JSON parsing failed"
        assert 'PET Bottle' in result.content, "Missing product name"
        assert 'PET' in result.content, "Missing material"
        print("\n✅ JSON Parser: PASSED")

    finally:
        os.unlink(json_file)


def test_jsonl_parser():
    """Test JSONL parser with multiple records"""
    print_section("TEST 2: JSONL Parser")

    # Create sample JSONL file
    records = [
        {"id": 1, "name": "Product A", "material": "HDPE", "capacity": "1L"},
        {"id": 2, "name": "Product B", "material": "PET", "capacity": "500ml"},
        {"id": 3, "name": "Product C", "material": "PP", "capacity": "250ml"},
        {"id": 4, "name": "Product D", "material": "PETG", "capacity": "750ml"},
        {"id": 5, "name": "Product E", "material": "LLDPE", "capacity": "2L"},
        {"id": 6, "name": "Product F", "material": "LDPE", "capacity": "100ml"},
        {"id": 7, "name": "Product G", "material": "PS", "capacity": "350ml"}
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for record in records:
            f.write(json.dumps(record) + '\n')
        jsonl_file = f.name

    try:
        result = parse_document(jsonl_file, options={
            'flatten': True,
            'include_keys': True
        })

        print(f"✅ Parse success: {result.success}")
        print(f"📦 Record count: {result.metadata.get('record_count')}")
        print(f"📊 Content length: {len(result.content)} characters")
        print(f"📝 Preview:\n{result.content[:400]}...")

        assert result.success, "JSONL parsing failed"
        assert result.metadata['record_count'] == 7, "Wrong record count"
        assert 'Product A' in result.content, "Missing record 1"
        assert 'Product B' in result.content, "Missing record 2"
        assert 'PETG' in result.content, "Missing PETG material"
        assert 'LLDPE' in result.content, "Missing LLDPE material"
        assert 'LDPE' in result.content, "Missing LDPE material"
        assert 'PS' in result.content, "Missing PS material"
        print("\n✅ JSONL Parser: PASSED")

    finally:
        os.unlink(jsonl_file)


def test_csv_parser():
    """Test CSV parser with headers"""
    print_section("TEST 3: CSV Parser")

    # Create sample CSV file
    csv_content = """Product,Material,Capacity,Price
PET Bottle,PET,500ml,1.50
PETG Container,PETG,750ml,1.80
HDPE Container,HDPE,1L,2.00
PP Cup,PP,250ml,0.80
LLDPE Film,LLDPE,Roll,3.50
LDPE Bag,LDPE,2L,1.20
PS Cup,PS,350ml,0.90"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        csv_file = f.name

    try:
        result = parse_document(csv_file, options={
            'csv_delimiter': ',',
            'csv_has_header': True
        })

        print(f"✅ Parse success: {result.success}")
        print(f"📊 Row count: {result.metadata.get('row_count')}")
        print(f"📊 Column count: {result.metadata.get('column_count')}")
        print(f"📝 Headers: {result.metadata.get('headers')}")
        print(f"📝 Preview:\n{result.content[:300]}...")

        assert result.success, "CSV parsing failed"
        assert result.metadata['row_count'] == 7, "Wrong row count"
        assert result.metadata['column_count'] == 4, "Wrong column count"
        assert 'PET Bottle' in result.content, "Missing CSV data"
        assert 'PETG Container' in result.content, "Missing PETG data"
        assert 'LLDPE Film' in result.content, "Missing LLDPE data"
        assert 'LDPE Bag' in result.content, "Missing LDPE data"
        assert 'PS Cup' in result.content, "Missing PS data"
        print("\n✅ CSV Parser: PASSED")

    finally:
        os.unlink(csv_file)


def test_text_parser():
    """Test text parser with paragraphs"""
    print_section("TEST 4: Text Parser")

    # Create sample text file
    text_content = """Manufacturing Standard Operating Procedure

Quality Control Requirements:
The process capability index (Cpk) must be maintained at ≥1.33 for all critical dimensions.

Equipment Efficiency:
Overall Equipment Effectiveness (OEE) target is 85% or higher.

Compliance:
All processes must comply with ISO 9001:2015 standards."""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(text_content)
        txt_file = f.name

    try:
        result = parse_document(txt_file)

        print(f"✅ Parse success: {result.success}")
        print(f"📊 Line count: {result.metadata.get('line_count')}")
        print(f"📊 Character count: {result.metadata.get('char_count')}")
        print(f"📝 Preview:\n{result.content[:300]}...")

        assert result.success, "Text parsing failed"
        assert 'Cpk' in result.content, "Missing content"
        assert 'OEE' in result.content, "Missing content"
        print("\n✅ Text Parser: PASSED")

    finally:
        os.unlink(txt_file)


def test_semantic_chunker():
    """Test semantic chunker (paragraph-based)"""
    print_section("TEST 5: Semantic Chunker")

    text = """First paragraph about manufacturing processes.
This paragraph describes quality control procedures.

Second paragraph about equipment maintenance.
This covers preventive maintenance schedules.

Third paragraph about safety requirements.
This outlines the safety protocols."""

    chunker = get_chunker('semantic', chunk_size=100, overlap=20)
    chunks = chunker.chunk(text, metadata={'doc_id': 'test_1'})

    print(f"📦 Total chunks: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i}:")
        print(f"  Size: {chunk['metadata']['chunk_size']} chars")
        print(f"  Strategy: {chunk['metadata']['chunk_strategy']}")
        print(f"  Content: {chunk['text'][:80]}...")

    assert len(chunks) >= 2, "Should create multiple chunks"
    assert all(c['metadata']['chunk_strategy'] == 'semantic' for c in chunks), "Wrong strategy"
    print("\n✅ Semantic Chunker: PASSED")


def test_sentence_chunker():
    """Test sentence chunker"""
    print_section("TEST 6: Sentence Chunker")

    text = """Quality control is critical. The Cpk must be 1.33 or higher. Equipment must be calibrated regularly. All measurements must be documented. Safety protocols must be followed."""

    chunker = get_chunker('sentence', chunk_size=80, overlap=20)
    chunks = chunker.chunk(text, metadata={'doc_id': 'test_2'})

    print(f"📦 Total chunks: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i}:")
        print(f"  Size: {chunk['metadata']['chunk_size']} chars")
        print(f"  Strategy: {chunk['metadata']['chunk_strategy']}")
        print(f"  Content: {chunk['text']}")

    assert len(chunks) >= 2, "Should create multiple chunks"
    assert all(c['metadata']['chunk_strategy'] == 'sentence' for c in chunks), "Wrong strategy"
    print("\n✅ Sentence Chunker: PASSED")


def test_recursive_chunker():
    """Test recursive chunker with custom separators"""
    print_section("TEST 7: Recursive Chunker")

    text = """Section 1: Quality Control

Subsection A: Cpk Requirements
- Critical dimensions: Cpk ≥ 1.33
- Non-critical: Cpk ≥ 1.00

Subsection B: OEE Targets
- Target: 85%
- Minimum: 75%

Section 2: Safety Protocols

Always follow safety procedures."""

    chunker = get_chunker('recursive',
        chunk_size=100,
        overlap=20,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = chunker.chunk(text, metadata={'doc_id': 'test_3'})

    print(f"📦 Total chunks: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i}:")
        print(f"  Size: {chunk['metadata']['chunk_size']} chars")
        print(f"  Strategy: {chunk['metadata']['chunk_strategy']}")
        print(f"  Content: {chunk['text'][:80]}...")

    assert len(chunks) >= 2, "Should create multiple chunks"
    assert all(c['metadata']['chunk_strategy'] == 'recursive' for c in chunks), "Wrong strategy"
    print("\n✅ Recursive Chunker: PASSED")


def test_sliding_window_chunker():
    """Test sliding window chunker"""
    print_section("TEST 8: Sliding Window Chunker")

    text = "A" * 500  # Long text for testing

    chunker = get_chunker('sliding_window', chunk_size=100, overlap=25)
    chunks = chunker.chunk(text, metadata={'doc_id': 'test_4'})

    print(f"📦 Total chunks: {len(chunks)}")
    for i, chunk in enumerate(chunks[:3]):  # Show first 3
        print(f"\nChunk {i}:")
        print(f"  Size: {chunk['metadata']['chunk_size']} chars")
        print(f"  Strategy: {chunk['metadata']['chunk_strategy']}")
        print(f"  Start: {chunk['metadata']['window_start']}")
        print(f"  End: {chunk['metadata']['window_end']}")

    assert len(chunks) > 1, "Should create multiple chunks"
    assert all(c['metadata']['chunk_strategy'] == 'sliding_window' for c in chunks), "Wrong strategy"
    # Verify overlap
    if len(chunks) > 1:
        overlap_check = chunks[1]['metadata']['window_start'] < chunks[0]['metadata']['window_end']
        assert overlap_check, "Overlap not working correctly"
    print("\n✅ Sliding Window Chunker: PASSED")


def test_end_to_end_workflow():
    """Test complete parsing + chunking workflow"""
    print_section("TEST 9: End-to-End Workflow")

    # Create JSONL file
    records = [
        {"title": "Manufacturing SOP", "content": "Process capability requirements. Cpk must be maintained at 1.33 or higher."},
        {"title": "Quality Standards", "content": "ISO 9001:2015 compliance is mandatory. All documentation must be current."}
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for record in records:
            f.write(json.dumps(record) + '\n')
        jsonl_file = f.name

    try:
        # Step 1: Parse
        parse_result = parse_document(jsonl_file, options={'flatten': True})
        print(f"✅ Parsing: {parse_result.success}")
        print(f"📦 Records parsed: {parse_result.metadata.get('record_count')}")

        # Step 2: Chunk
        chunker = get_chunker('semantic', chunk_size=200, overlap=30)
        chunks = chunker.chunk(
            parse_result.content,
            metadata={
                'doc_id': 'workflow_test',
                'source_file': jsonl_file,
                **parse_result.metadata
            }
        )

        print(f"✂️  Chunks created: {len(chunks)}")
        print(f"\n📝 Sample chunk:")
        print(f"  Text: {chunks[0]['text'][:150]}...")
        print(f"  Metadata: {chunks[0]['metadata']}")

        assert parse_result.success, "Parsing failed"
        assert len(chunks) > 0, "No chunks created"
        assert 'record_count' in chunks[0]['metadata'], "Metadata not preserved"
        print("\n✅ End-to-End Workflow: PASSED")

    finally:
        os.unlink(jsonl_file)


def test_parser_factory():
    """Test parser factory registration and selection"""
    print_section("TEST 10: Parser Factory")

    factory = get_parser_factory()

    # Test supported formats
    supported = factory.supported_formats()
    print(f"📋 Supported formats: {supported}")

    assert 'pdf' in supported, "PDF not supported"
    assert 'json' in supported, "JSON not supported"
    assert 'jsonl' in supported, "JSONL not supported"
    assert 'txt' in supported, "TXT not supported"
    assert 'csv' in supported, "CSV not supported"

    # Test parser selection
    pdf_parser = factory.get_parser('test.pdf')
    json_parser = factory.get_parser('test.json')

    assert pdf_parser is not None, "PDF parser not found"
    assert json_parser is not None, "JSON parser not found"

    print("\n✅ Parser Factory: PASSED")


def run_all_tests():
    """Run all test functions"""
    print(f"\n{'#' * 80}")
    print("  RAG Pipeline - Parsing & Chunking Test Suite")
    print(f"{'#' * 80}\n")

    tests = [
        test_json_parser,
        test_jsonl_parser,
        test_csv_parser,
        test_text_parser,
        test_semantic_chunker,
        test_sentence_chunker,
        test_recursive_chunker,
        test_sliding_window_chunker,
        test_end_to_end_workflow,
        test_parser_factory
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            failed += 1

    print_section("TEST SUMMARY")
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {failed} tests failed")
        return 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
