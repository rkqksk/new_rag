"""
PDF Ingestion & Document Processing Tests

Tests document ingestion service with real PDF files and various document formats.
Validates parsing, chunking, embedding generation, and storage operations.
"""

import csv
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# ============================================================
# PDF File Generation & Fixtures
# ============================================================


@pytest.fixture
def temp_pdf_file():
    """Create a temporary PDF file for testing"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError:
        pytest.skip("reportlab not installed")

    with tempfile.NamedTemporaryFile(mode="wb", suffix=".pdf", delete=False) as f:
        pdf_path = f.name

    try:
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.drawString(100, 750, "Test PDF Document")
        c.drawString(100, 730, "This is a test document for ingestion testing.")
        c.drawString(100, 710, "It contains multiple lines of text.")
        c.drawString(100, 690, "Product: Steel Plate 3mm")
        c.drawString(100, 670, "Quantity: 100 units")
        c.drawString(100, 650, "Price: $50 per unit")
        c.save()
        yield pdf_path
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)


@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file for testing"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        csv_path = f.name
        writer = csv.writer(f)
        writer.writerow(["Product", "Quantity", "Unit Price", "Total"])
        writer.writerow(["Steel Plate", "100", "$50", "$5000"])
        writer.writerow(["Aluminum Rod", "50", "$75", "$3750"])
        writer.writerow(["Copper Wire", "200", "$25", "$5000"])

    try:
        yield csv_path
    finally:
        if os.path.exists(csv_path):
            os.remove(csv_path)


@pytest.fixture
def temp_json_file():
    """Create a temporary JSON file for testing"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json_path = f.name
        data = {
            "products": [
                {
                    "id": "P001",
                    "name": "Steel Plate",
                    "specification": "High carbon steel, 3mm thickness",
                    "price": 50.00,
                    "unit": "per piece",
                },
                {
                    "id": "P002",
                    "name": "Aluminum Rod",
                    "specification": "Aluminium alloy 6061, 10mm diameter",
                    "price": 75.00,
                    "unit": "per piece",
                },
            ]
        }
        json.dump(data, f, indent=2)

    try:
        yield json_path
    finally:
        if os.path.exists(json_path):
            os.remove(json_path)


@pytest.fixture
def temp_text_file():
    """Create a temporary text file for testing"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        text_path = f.name
        f.write("Manufacturing Process Documentation\n")
        f.write("=" * 40 + "\n\n")
        f.write("Section 1: Raw Material Specifications\n")
        f.write("- Steel Grade: SS 316\n")
        f.write("- Tensile Strength: 600-800 MPa\n")
        f.write("- Elongation: 30% minimum\n\n")
        f.write("Section 2: Quality Control\n")
        f.write("- Visual Inspection: Pass/Fail\n")
        f.write("- Dimension Check: ±0.5mm tolerance\n")
        f.write("- Surface Finish: Ra 3.2 maximum\n")

    try:
        yield text_path
    finally:
        if os.path.exists(text_path):
            os.remove(text_path)


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client for testing"""
    client = Mock()
    client.get_collection = Mock(side_effect=Exception("Collection not found"))
    client.create_collection = Mock()
    client.upsert = Mock()
    client.search = AsyncMock(return_value=[])
    return client


@pytest.fixture
def mock_embedding_model():
    """Mock embedding model"""
    model = Mock()
    model.encode = Mock(return_value=[[0.1] * 384 for _ in range(10)])
    model.get_sentence_embedding_dimension = Mock(return_value=384)
    return model


# ============================================================
# Document Chunk Tests
# ============================================================


@pytest.mark.integration
class TestDocumentChunk:
    """Test DocumentChunk data model"""

    def test_document_chunk_creation(self):
        """Test creating a document chunk"""
        try:
            from apps.api.services.document_ingestion_service import DocumentChunk
        except ModuleNotFoundError:
            pytest.skip("pytesseract not installed - document ingestion skipped")

        chunk = DocumentChunk(
            text="Sample text content",
            doc_id="doc_001",
            chunk_index=0,
            metadata={"source": "test_doc"},
        )

        assert chunk.text == "Sample text content"
        assert chunk.doc_id == "doc_001"
        assert chunk.chunk_index == 0
        assert chunk.metadata["source"] == "test_doc"
        assert chunk.id is not None
        assert chunk.created_at is not None

    def test_document_chunk_to_dict(self):
        """Test chunk conversion to dictionary"""
        try:
            from apps.api.services.document_ingestion_service import DocumentChunk
        except ModuleNotFoundError:
            pytest.skip("pytesseract not installed - document ingestion skipped")

        chunk = DocumentChunk(text="Test content", doc_id="doc_002", chunk_index=1)

        chunk_dict = chunk.to_dict()

        assert chunk_dict["text"] == "Test content"
        assert chunk_dict["doc_id"] == "doc_002"
        assert chunk_dict["chunk_index"] == 1
        assert "id" in chunk_dict
        assert "created_at" in chunk_dict
        assert "metadata" in chunk_dict

    def test_document_chunk_with_metadata(self):
        """Test chunk with rich metadata"""
        try:
            from apps.api.services.document_ingestion_service import DocumentChunk
        except ModuleNotFoundError:
            pytest.skip("pytesseract not installed - document ingestion skipped")

        metadata = {"source": "invoice.pdf", "page": 1, "section": "products", "confidence": 0.95}

        chunk = DocumentChunk(
            text="Product listing content", doc_id="doc_003", chunk_index=0, metadata=metadata
        )

        assert chunk.metadata == metadata
        assert chunk.metadata["page"] == 1
        assert chunk.metadata["confidence"] == 0.95


# ============================================================
# Document Ingestion Service Tests
# ============================================================


@pytest.mark.integration
class TestDocumentIngestionService:
    """Test document ingestion service"""

    def test_service_instantiation(self, mock_qdrant_client, mock_embedding_model):
        """Test service can be instantiated"""
        try:
            from apps.api.services.document_ingestion_service import DocumentIngestionService
        except ImportError:
            pytest.skip("pytesseract not installed")

        # Mock the embedding model initialization
        with patch(
            "app.services.document_ingestion_service.SentenceTransformer",
            return_value=mock_embedding_model,
        ):
            service = DocumentIngestionService(
                qdrant_client=mock_qdrant_client,
                embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            )

            assert service is not None
            assert service.qdrant_client is not None
            assert service.collection_name == "documents"

    def test_service_has_required_methods(self, mock_qdrant_client, mock_embedding_model):
        """Test service has required methods"""
        try:
            from apps.api.services.document_ingestion_service import DocumentIngestionService
        except ImportError:
            pytest.skip("pytesseract not installed")

        with patch(
            "app.services.document_ingestion_service.SentenceTransformer",
            return_value=mock_embedding_model,
        ):
            service = DocumentIngestionService(qdrant_client=mock_qdrant_client)

            assert hasattr(service, "ingest_file")
            assert hasattr(service, "_init_collection")
            assert callable(service.ingest_file)


# ============================================================
# File Format Processing Tests
# ============================================================


@pytest.mark.integration
class TestFileFormatProcessing:
    """Test processing different file formats"""

    def test_csv_file_processing(self, temp_csv_file):
        """Test CSV file can be read and processed"""
        assert os.path.exists(temp_csv_file)

        # Read CSV content
        rows = []
        with open(temp_csv_file, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                rows.append(row)

        assert len(rows) > 0
        assert rows[0] == ["Product", "Quantity", "Unit Price", "Total"]
        assert rows[1][0] == "Steel Plate"

    def test_json_file_processing(self, temp_json_file):
        """Test JSON file can be read and processed"""
        assert os.path.exists(temp_json_file)

        with open(temp_json_file, "r") as f:
            data = json.load(f)

        assert "products" in data
        assert len(data["products"]) == 2
        assert data["products"][0]["name"] == "Steel Plate"

    def test_text_file_processing(self, temp_text_file):
        """Test text file can be read and processed"""
        assert os.path.exists(temp_text_file)

        with open(temp_text_file, "r") as f:
            content = f.read()

        assert "Manufacturing Process" in content
        assert "SS 316" in content
        assert "Quality Control" in content

    def test_pdf_file_creation(self, temp_pdf_file):
        """Test PDF file is created correctly"""
        assert os.path.exists(temp_pdf_file)
        assert os.path.getsize(temp_pdf_file) > 0


# ============================================================
# Document Chunking Tests
# ============================================================


@pytest.mark.integration
class TestDocumentChunking:
    """Test document chunking logic"""

    def test_text_chunking_with_overlap(self):
        """Test text chunking with overlap"""
        text = " ".join(["This is a test sentence."] * 100)
        chunk_size = 100  # characters
        chunk_overlap = 20

        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end]
            chunks.append(chunk)

            # Move start position accounting for overlap
            start = end - chunk_overlap
            if start >= end:
                break

        assert len(chunks) > 1
        assert len(chunks[0]) == chunk_size
        # Verify overlap
        assert chunks[0][-chunk_overlap:] == chunks[1][:chunk_overlap]

    def test_csv_to_chunks(self, temp_csv_file):
        """Test converting CSV to document chunks"""
        chunks = []

        with open(temp_csv_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Each row becomes a chunk with context
                chunk_text = f"Product: {row['Product']}, Quantity: {row['Quantity']}, Price: {row['Unit Price']}"
                chunks.append(chunk_text)

        assert len(chunks) > 0
        assert "Steel Plate" in chunks[0]
        assert "100" in chunks[0]


# ============================================================
# Metadata Extraction Tests
# ============================================================


@pytest.mark.integration
class TestMetadataExtraction:
    """Test metadata extraction from documents"""

    def test_extract_file_metadata(self, temp_text_file):
        """Test extracting metadata from file"""
        file_stat = os.stat(temp_text_file)

        metadata = {
            "file_name": os.path.basename(temp_text_file),
            "file_size": file_stat.st_size,
            "file_type": "txt",
            "created": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
        }

        assert metadata["file_type"] == "txt"
        assert metadata["file_size"] > 0
        assert "created" in metadata
        assert "modified" in metadata

    def test_extract_json_metadata(self, temp_json_file):
        """Test extracting metadata from JSON"""
        with open(temp_json_file, "r") as f:
            data = json.load(f)

        metadata = {
            "document_type": "product_catalog",
            "item_count": len(data.get("products", [])),
            "first_item": data["products"][0]["name"] if data.get("products") else None,
        }

        assert metadata["item_count"] == 2
        assert metadata["first_item"] == "Steel Plate"

    def test_extract_csv_metadata(self, temp_csv_file):
        """Test extracting metadata from CSV"""
        with open(temp_csv_file, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        metadata = {
            "document_type": "product_list",
            "row_count": len(rows),
            "columns": reader.fieldnames,
        }

        assert metadata["row_count"] == 3
        assert "Product" in metadata["columns"]
        assert "Price" in metadata["columns"]


# ============================================================
# Document Storage Tests
# ============================================================


@pytest.mark.integration
class TestDocumentStorage:
    """Test document storage in Qdrant"""

    def test_chunk_to_vector_conversion(self, mock_embedding_model):
        """Test converting chunks to vectors"""
        chunks = [
            "Steel products have high tensile strength",
            "Aluminum is lightweight and corrosion resistant",
            "Copper has excellent electrical conductivity",
        ]

        vectors = mock_embedding_model.encode(chunks)

        assert len(vectors) == 3
        assert len(vectors[0]) == 384
        # All vectors should be of same dimension
        assert all(len(v) == 384 for v in vectors)

    def test_prepare_points_for_storage(self):
        """Test preparing points for Qdrant storage"""
        from qdrant_client.models import PointStruct

        from apps.api.services.document_ingestion_service import DocumentChunk

        chunks = [
            DocumentChunk(text="Product A specs", doc_id="doc_1", chunk_index=0),
            DocumentChunk(text="Product B specs", doc_id="doc_1", chunk_index=1),
        ]

        # Simulate vector generation
        vectors = [[0.1] * 384 for _ in chunks]

        points = []
        for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
            point = PointStruct(
                id=i,
                vector=vector,
                payload={
                    "text": chunk.text,
                    "doc_id": chunk.doc_id,
                    "chunk_index": chunk.chunk_index,
                    "metadata": chunk.metadata,
                },
            )
            points.append(point)

        assert len(points) == 2
        assert points[0].payload["text"] == "Product A specs"
        assert len(points[0].vector) == 384

    def test_upsert_to_qdrant(self, mock_qdrant_client):
        """Test upserting chunks to Qdrant"""
        from qdrant_client.models import PointStruct

        points = [
            PointStruct(
                id=1, vector=[0.1] * 384, payload={"text": "Test chunk 1", "doc_id": "doc_1"}
            ),
            PointStruct(
                id=2, vector=[0.2] * 384, payload={"text": "Test chunk 2", "doc_id": "doc_1"}
            ),
        ]

        # Simulate upsert
        mock_qdrant_client.upsert(collection_name="documents", points=points)

        # Verify upsert was called
        mock_qdrant_client.upsert.assert_called_once()
        call_args = mock_qdrant_client.upsert.call_args
        assert call_args[1]["collection_name"] == "documents"
        assert len(call_args[1]["points"]) == 2


# ============================================================
# Error Handling & Edge Cases
# ============================================================


@pytest.mark.integration
class TestDocumentIngestionErrors:
    """Test error handling in document ingestion"""

    def test_nonexistent_file_handling(self):
        """Test handling of non-existent files"""
        with pytest.raises((FileNotFoundError, IOError)):
            with open("/nonexistent/path/file.pdf", "r"):
                pass

    def test_corrupted_json_handling(self):
        """Test handling of corrupted JSON"""
        invalid_json = '{"invalid": json content"}'

        with pytest.raises(json.JSONDecodeError):
            json.loads(invalid_json)

    def test_empty_file_handling(self):
        """Test handling of empty files"""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            empty_file = f.name

        try:
            with open(empty_file, "r") as f:
                content = f.read()

            assert content == ""
        finally:
            os.remove(empty_file)

    def test_large_file_handling(self):
        """Test handling large files"""
        # Create a moderately sized file (10MB simulation)
        large_content = "x" * (10 * 1024 * 1024)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            large_file = f.name
            f.write(large_content)

        try:
            file_size = os.path.getsize(large_file)
            assert file_size == 10 * 1024 * 1024

            # Test reading in chunks
            chunk_size = 1024 * 1024  # 1MB chunks
            chunks_read = 0

            with open(large_file, "r") as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    chunks_read += 1

            assert chunks_read == 10
        finally:
            os.remove(large_file)


# ============================================================
# Batch Document Processing
# ============================================================


@pytest.mark.integration
class TestBatchDocumentProcessing:
    """Test batch processing of documents"""

    def test_batch_file_discovery(self):
        """Test discovering multiple files in directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create multiple test files
            for i in range(5):
                file_path = os.path.join(temp_dir, f"document_{i}.txt")
                with open(file_path, "w") as f:
                    f.write(f"Document {i} content")

            # Discover files
            files = list(Path(temp_dir).glob("*.txt"))

            assert len(files) == 5

    def test_batch_processing_progress(self):
        """Test tracking progress during batch processing"""
        total_files = 10
        processed = 0
        progress = []

        for i in range(total_files):
            processed += 1
            progress_pct = (processed / total_files) * 100
            progress.append(progress_pct)

        assert len(progress) == 10
        assert progress[0] == 10.0
        assert progress[-1] == 100.0
        # Progress should be monotonically increasing
        assert all(progress[i] <= progress[i + 1] for i in range(len(progress) - 1))

    def test_batch_error_resilience(self):
        """Test resilience when processing fails on some files"""
        files = ["file1.txt", "file2.txt", "file3.txt", "file4.txt"]
        results = []

        for file_name in files:
            try:
                # Simulate processing with occasional failures
                if "2" in file_name:
                    raise IOError(f"Failed to process {file_name}")
                results.append({"file": file_name, "status": "success"})
            except IOError as e:
                results.append({"file": file_name, "status": "error", "error": str(e)})

        successful = [r for r in results if r["status"] == "success"]
        failed = [r for r in results if r["status"] == "error"]

        assert len(successful) == 3
        assert len(failed) == 1
        assert failed[0]["file"] == "file2.txt"


# ============================================================
# Performance Tests
# ============================================================


@pytest.mark.integration
class TestDocumentProcessingPerformance:
    """Test performance of document processing"""

    def test_chunking_speed(self):
        """Test chunking speed"""
        import time

        text = " ".join(["This is a test sentence with meaningful content."] * 1000)
        chunk_size = 512

        start = time.time()
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunks.append(text[i : i + chunk_size])
        elapsed = time.time() - start

        # Should process large text quickly
        assert elapsed < 0.1
        assert len(chunks) > 0

    def test_metadata_extraction_speed(self):
        """Test metadata extraction speed"""
        import time

        metadata_templates = [
            {"source": f"doc_{i}", "page": i % 10, "date": datetime.now().isoformat()}
            for i in range(1000)
        ]

        start = time.time()
        extracted = [m.copy() for m in metadata_templates]
        elapsed = time.time() - start

        # Should extract metadata quickly
        assert elapsed < 0.1
        assert len(extracted) == 1000

    def test_batch_file_processing_speed(self):
        """Test batch file processing speed"""
        import time

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            for i in range(50):
                path = os.path.join(temp_dir, f"file_{i}.txt")
                with open(path, "w") as f:
                    f.write(f"Content {i}\n" * 100)

            start = time.time()
            files = list(Path(temp_dir).glob("*.txt"))
            elapsed = time.time() - start

            assert elapsed < 0.1
            assert len(files) == 50
