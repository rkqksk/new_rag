import pytest
from fastapi.testclient import TestClient
from src.api.app import create_app

@pytest.fixture
def test_client():
    """Create a test client for API integration testing"""
    app = create_app()
    return TestClient(app)

class TestRAGIntegration:
    def test_document_upload(self, test_client, tmp_path):
        """Test document upload via API"""
        # Create a temporary test document
        test_doc = tmp_path / "test_doc.txt"
        test_doc.write_text("This is a test document about machine learning.")

        # Perform upload
        response = test_client.post(
            "/rag/upload",
            json={
                "file_paths": [str(test_doc)],
                "metadata": {"source": "test"}
            }
        )

        assert response.status_code == 200
        result = response.json()
        assert result['total_documents'] == 1
        assert result['total_chunks'] > 0

    def test_query_processing(self, test_client, tmp_path):
        """Test end-to-end query processing"""
        # First upload documents
        test_docs = [
            tmp_path / "doc1.txt",
            tmp_path / "doc2.txt"
        ]
        for doc in test_docs:
            doc.write_text("This is a test document about machine learning and AI.")

        test_client.post(
            "/rag/upload",
            json={"file_paths": [str(doc) for doc in test_docs]}
        )

        # Perform query
        response = test_client.post(
            "/rag/query",
            json={
                "query": "Tell me about machine learning",
                "top_k": 2,
                "filters": {"include_tags": ["test"]}
            }
        )

        assert response.status_code == 200
        result = response.json()

        assert 'response' in result
        assert 'context_chunks' in result
        assert 'citations' in result
        assert len(result['context_chunks']) > 0
        assert result['metadata']['citation_count'] >= 0

    def test_error_handling(self, test_client):
        """Test API error handling mechanisms"""
        # Invalid query
        response = test_client.post(
            "/rag/query",
            json={"query": ""}
        )
        assert response.status_code == 422  # Validation error

        # Non-existent document upload
        response = test_client.post(
            "/rag/upload",
            json={"file_paths": ["/path/to/nonexistent/file.txt"]}
        )
        assert response.status_code == 500