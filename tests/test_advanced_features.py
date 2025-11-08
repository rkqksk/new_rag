from datetime import datetime, timedelta

import pytest

from src.core.error_handler import ErrorHandler, RAGError
from src.core.metadata_filter import MetadataFilter


class TestAdvancedFeatures:
    def test_metadata_date_filtering(self):
        """Test filtering documents by date range"""
        documents = [
            {"text": "Document 1", "metadata": {"created_at": datetime(2023, 1, 15)}},
            {"text": "Document 2", "metadata": {"created_at": datetime(2023, 2, 20)}},
        ]

        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 2, 1)

        filtered_docs = MetadataFilter.filter_by_date(documents, start_date, end_date)

        assert len(filtered_docs) == 1
        assert filtered_docs[0]["text"] == "Document 1"

    def test_metadata_tag_filtering(self):
        """Test filtering documents by tags"""
        documents = [
            {"text": "Technical Document", "metadata": {"tags": ["tech", "ai"]}},
            {"text": "Business Document", "metadata": {"tags": ["business"]}},
        ]

        # Include tech tag
        include_filtered = MetadataFilter.filter_by_tags(documents, include_tags=["tech"])
        assert len(include_filtered) == 1
        assert include_filtered[0]["text"] == "Technical Document"

        # Exclude business tag
        exclude_filtered = MetadataFilter.filter_by_tags(documents, exclude_tags=["business"])
        assert len(exclude_filtered) == 1
        assert exclude_filtered[0]["text"] == "Technical Document"

    def test_metadata_transformation(self):
        """Test metadata field transformation"""
        documents = [
            {
                "text": "Sample Document",
                "metadata": {"old_field": "value", "another_old_field": "another_value"},
            }
        ]

        field_mapping = {"old_field": "new_field", "another_old_field": "another_new_field"}

        transformed_docs = MetadataFilter.transform_metadata(documents, field_mapping)

        assert "old_field" not in transformed_docs[0]["metadata"]
        assert "new_field" in transformed_docs[0]["metadata"]
        assert transformed_docs[0]["metadata"]["new_field"] == "value"

    def test_error_handling(self):
        """Test comprehensive error handling"""
        error_handler = ErrorHandler(log_level=None)  # Disable logging for test

        # Simulate an error
        def error_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            try:
                error_function()
            except Exception as e:
                error_info = error_handler.log_error(e)

                assert error_info["error_type"] == "ValueError"
                assert "Test error" in error_info["error_message"]
                raise

    def test_custom_rag_error(self):
        """Test custom RAG error creation"""
        error_handler = ErrorHandler(log_level=None)

        # Create a custom RAG error
        rag_error = error_handler.create_error_event(
            "DocumentProcessingError", "Failed to process document"
        )

        assert isinstance(rag_error, RAGError)
        assert rag_error.error_type == "DocumentProcessingError"
        assert rag_error.message == "Failed to process document"
