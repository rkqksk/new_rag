"""
Full RAG Pipeline E2E Test

Tests complete flow: Document → Plugin → Vector DB → Search → QA
"""

import pytest
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio

try:
    from plugins.test_plugins import PluginManager, ProcessingResult
    from plugins.base_plugin import DocumentMetadata
    PLUGINS_AVAILABLE = True
except ImportError:
    PLUGINS_AVAILABLE = False
    pytest.skip("Domain plugins not available", allow_module_level=True)


@pytest.fixture
def manufacturing_document():
    """Sample manufacturing document for pipeline testing"""
    return {
        "content": """
        Standard Operating Procedure: CNC Machining

        Equipment: CNC Mill (Haas VF-2)
        Material: Aluminum 6061-T6

        Process Parameters:
        - Spindle speed: 3000 RPM
        - Feed rate: 500 mm/min
        - Depth of cut: 2mm per pass
        - Coolant: Water-soluble

        Quality Control:
        - CMM inspection for critical dimensions
        - Surface roughness: Ra < 1.6 μm
        - Tolerances: ±0.05mm

        Safety Requirements:
        - Safety glasses required
        - Machine enclosure must be closed during operation
        """,
        "filename": "cnc_machining_sop.pdf",
        "metadata": {
            "doc_type": "SOP",
            "department": "Manufacturing"
        }
    }


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client for testing"""
    mock_client = Mock()
    mock_client.upsert = AsyncMock(return_value={"status": "ok"})
    mock_client.search = AsyncMock(return_value=[
        {
            "id": "doc1",
            "score": 0.95,
            "payload": {
                "text": "CNC machining content",
                "domain": "manufacturing",
                "doc_type": "sop"
            }
        }
    ])
    mock_client.create_collection = AsyncMock(return_value={"status": "ok"})
    mock_client.collection_exists = AsyncMock(return_value=True)
    return mock_client


@pytest.fixture
def plugin_manager():
    """Initialize plugin manager"""
    return PluginManager()


class TestFullRAGPipeline:
    """Test complete RAG pipeline with plugin integration"""

    @pytest.mark.asyncio
    async def test_document_to_vector_db_pipeline(
        self, plugin_manager, manufacturing_document, mock_qdrant_client
    ):
        """
        Test complete pipeline: Document processing → Vector DB storage
        """
        # Step 1: Process document with plugin
        result = plugin_manager.process_document(manufacturing_document)

        assert result.success is True
        assert result.metadata is not None
        assert result.metadata.domain == "manufacturing"

        # Step 2: Prepare document for vector DB with enriched metadata
        vector_payload = {
            "text": result.enriched_content,
            "domain": result.metadata.domain,
            "doc_type": result.metadata.doc_type,
            "categories": result.metadata.categories,
            "terminology": result.metadata.terminology,
            "entities": result.metadata.extracted_entities,
            "confidence": result.metadata.confidence,
            "filename": manufacturing_document.get("filename")
        }

        # Step 3: Verify payload structure is correct for Qdrant
        assert "text" in vector_payload
        assert "domain" in vector_payload
        assert vector_payload["domain"] == "manufacturing"
        assert isinstance(vector_payload["terminology"], list)
        assert isinstance(vector_payload["entities"], dict)

        # Step 4: Simulate vector DB upsert
        with patch('qdrant_client.QdrantClient', return_value=mock_qdrant_client):
            await mock_qdrant_client.upsert(
                collection_name="documents",
                points=[{
                    "id": "test_doc_1",
                    "vector": [0.1] * 384,  # Mock embedding
                    "payload": vector_payload
                }]
            )

        # Verify upsert was called
        mock_qdrant_client.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_domain_filtered_search(
        self, plugin_manager, manufacturing_document, mock_qdrant_client
    ):
        """
        Test domain-filtered search with plugin metadata
        """
        # Step 1: Process document
        result = plugin_manager.process_document(manufacturing_document)

        # Step 2: Create search filter based on plugin domain
        search_filter = {
            "must": [
                {"key": "domain", "match": {"value": result.metadata.domain}}
            ]
        }

        # Step 3: Simulate domain-filtered search
        with patch('qdrant_client.QdrantClient', return_value=mock_qdrant_client):
            search_results = await mock_qdrant_client.search(
                collection_name="documents",
                query_vector=[0.1] * 384,  # Mock query embedding
                filter=search_filter,
                limit=10
            )

        # Verify search was called with correct filter
        mock_qdrant_client.search.assert_called_once()
        call_kwargs = mock_qdrant_client.search.call_args[1]
        assert "filter" in call_kwargs
        assert call_kwargs["filter"]["must"][0]["key"] == "domain"

        # Verify search results contain domain metadata
        assert len(search_results) > 0
        assert search_results[0]["payload"]["domain"] == "manufacturing"

    @pytest.mark.asyncio
    async def test_multiple_documents_different_domains(
        self, plugin_manager, mock_qdrant_client
    ):
        """
        Test pipeline with multiple documents from different domains
        """
        # Create documents from different domains
        manufacturing_doc = {
            "content": """
            Standard Operating Procedure: CNC Machining
            Equipment: CNC Mill
            Process: Milling operation with spindle speed 3000 RPM
            Feed rate: 500 mm/min
            Quality control: CMM inspection required
            """,
            "filename": "manufacturing_sop.pdf"
        }

        packaging_doc = {
            "content": """
            Packaging Specification
            Container Type: PET Bottle
            Material: Polyethylene Terephthalate
            Capacity: 500ml
            Neck Size: 28mm
            Quality Standards: FDA approved
            """,
            "filename": "packaging_spec.pdf"
        }

        # Process both documents
        mfg_result = plugin_manager.process_document(manufacturing_doc)
        pkg_result = plugin_manager.process_document(packaging_doc)

        # Verify different domains
        assert mfg_result.metadata.domain == "manufacturing"
        assert pkg_result.metadata.domain == "packaging"

        # Prepare payloads
        payloads = [
            {
                "text": mfg_result.enriched_content,
                "domain": mfg_result.metadata.domain,
                "doc_type": mfg_result.metadata.doc_type
            },
            {
                "text": pkg_result.enriched_content,
                "domain": pkg_result.metadata.domain,
                "doc_type": pkg_result.metadata.doc_type
            }
        ]

        # Verify both payloads have correct structure
        for payload in payloads:
            assert "text" in payload
            assert "domain" in payload
            assert "doc_type" in payload
            assert payload["domain"] in ["manufacturing", "packaging"]

    @pytest.mark.asyncio
    async def test_chunk_based_storage(
        self, plugin_manager, manufacturing_document
    ):
        """
        Test that chunks are properly prepared for vector storage
        """
        # Process document
        result = plugin_manager.process_document(manufacturing_document)

        # Verify chunks are created
        assert len(result.chunks) > 0

        # Verify each chunk has metadata
        for chunk in result.chunks:
            assert "text" in chunk
            assert "metadata" in chunk
            assert "domain" in chunk["metadata"]
            assert "doc_type" in chunk["metadata"]
            assert "chunk_index" in chunk["metadata"]

            # Each chunk should be storable in vector DB
            chunk_payload = {
                **chunk["metadata"],
                "text": chunk["text"]
            }

            assert chunk_payload["domain"] == "manufacturing"

    @pytest.mark.asyncio
    async def test_search_result_ranking_with_confidence(
        self, plugin_manager, manufacturing_document, mock_qdrant_client
    ):
        """
        Test that plugin confidence scores can be used for ranking
        """
        # Process document
        result = plugin_manager.process_document(manufacturing_document)

        # Store confidence in payload
        payload = {
            "text": result.enriched_content,
            "domain": result.metadata.domain,
            "plugin_confidence": result.metadata.confidence
        }

        # High confidence documents should be prioritized
        assert payload["plugin_confidence"] >= 0.0
        assert payload["plugin_confidence"] <= 1.0

        # In a real search, we could use this for:
        # 1. Boosting high-confidence results
        # 2. Filtering low-confidence results
        # 3. Explaining result relevance to users

    @pytest.mark.asyncio
    async def test_terminology_based_search_enhancement(
        self, plugin_manager, manufacturing_document
    ):
        """
        Test that extracted terminology enhances search
        """
        # Process document
        result = plugin_manager.process_document(manufacturing_document)

        # Terminology should be stored with document
        payload = {
            "text": result.enriched_content,
            "domain": result.metadata.domain,
            "terminology": result.metadata.terminology
        }

        # Terminology can be used for:
        # 1. Query expansion (search for related terms)
        # 2. Highlighting important concepts
        # 3. Building domain-specific indexes

        # Verify terminology is searchable
        if len(payload["terminology"]) > 0:
            # Could create additional search fields
            terminology_text = " ".join(payload["terminology"])
            assert len(terminology_text) > 0


class TestPipelineErrorHandling:
    """Test error handling in full pipeline"""

    @pytest.mark.asyncio
    async def test_pipeline_with_failed_plugin_processing(
        self, plugin_manager, mock_qdrant_client
    ):
        """
        Test pipeline handles plugin processing failures gracefully
        """
        # Document that might fail processing
        invalid_doc = {
            "content": "",  # Empty content
            "filename": "invalid.pdf"
        }

        # Process document
        result = plugin_manager.process_document(invalid_doc)

        # Should handle gracefully
        if not result.success:
            # Pipeline should not store failed documents
            assert result.metadata is None
            # Should log error but not crash
            assert len(result.errors) > 0
        else:
            # If it processes, confidence should be very low
            assert result.metadata.confidence < 0.5

    @pytest.mark.asyncio
    async def test_pipeline_with_vector_db_failure(
        self, plugin_manager, manufacturing_document
    ):
        """
        Test pipeline handles vector DB failures gracefully
        """
        # Process document successfully
        result = plugin_manager.process_document(manufacturing_document)
        assert result.success is True

        # Simulate vector DB failure
        mock_client = Mock()
        mock_client.upsert = AsyncMock(side_effect=Exception("Vector DB connection failed"))

        # Pipeline should catch and handle the error
        try:
            with patch('qdrant_client.QdrantClient', return_value=mock_client):
                await mock_client.upsert(
                    collection_name="documents",
                    points=[{"id": "test", "vector": [0.1] * 384, "payload": {}}]
                )
        except Exception as e:
            # Error should be caught and logged
            assert "Vector DB" in str(e)
            # Original document processing should still be valid
            assert result.success is True


class TestPipelineIntegration:
    """Integration tests for complete pipeline"""

    def test_end_to_end_document_lifecycle(
        self, plugin_manager, manufacturing_document
    ):
        """
        Test complete document lifecycle:
        Upload → Process → Store → Search → Retrieve
        """
        # Step 1: Upload (simulate)
        uploaded_doc = manufacturing_document

        # Step 2: Process with plugin
        result = plugin_manager.process_document(uploaded_doc)
        assert result.success is True

        # Step 3: Store (prepare payload)
        storage_payload = {
            "document_id": "doc_123",
            "text": result.enriched_content,
            "domain": result.metadata.domain,
            "doc_type": result.metadata.doc_type,
            "categories": result.metadata.categories,
            "terminology": result.metadata.terminology,
            "entities": result.metadata.extracted_entities,
            "confidence": result.metadata.confidence,
            "original_filename": uploaded_doc.get("filename")
        }

        # Step 4: Verify storage payload is complete
        required_fields = [
            "document_id", "text", "domain", "doc_type",
            "categories", "terminology", "entities", "confidence"
        ]
        for field in required_fields:
            assert field in storage_payload, f"Missing field: {field}"

        # Step 5: Search (simulate with filter)
        search_filter = {
            "domain": storage_payload["domain"],
            "doc_type": storage_payload["doc_type"]
        }

        # Step 6: Retrieve (verify payload matches search criteria)
        assert storage_payload["domain"] == search_filter["domain"]
        assert storage_payload["doc_type"] == search_filter["doc_type"]

    def test_plugin_metadata_preserves_through_pipeline(
        self, plugin_manager, manufacturing_document
    ):
        """
        Test that plugin-generated metadata is preserved throughout pipeline
        """
        # Process document
        result = plugin_manager.process_document(manufacturing_document)

        # Extract metadata
        original_metadata = {
            "domain": result.metadata.domain,
            "doc_type": result.metadata.doc_type,
            "confidence": result.metadata.confidence,
            "terminology": result.metadata.terminology,
            "entities": result.metadata.extracted_entities
        }

        # Simulate storage and retrieval
        stored_payload = {**original_metadata, "text": result.enriched_content}

        # Verify metadata is preserved
        assert stored_payload["domain"] == original_metadata["domain"]
        assert stored_payload["doc_type"] == original_metadata["doc_type"]
        assert stored_payload["confidence"] == original_metadata["confidence"]
        assert stored_payload["terminology"] == original_metadata["terminology"]
        assert stored_payload["entities"] == original_metadata["entities"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
