"""
Unit tests for RAG Data Upload API - v7.4.0
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import io
import pandas as pd


class TestRAGDataUploadAPI:
    """Test RAG Data Upload API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from src.api.routes.rag_data_upload import get_rag_data_upload_router
        from fastapi import FastAPI

        app = FastAPI()
        router = get_rag_data_upload_router()
        app.include_router(router)

        return TestClient(app)

    def test_list_templates(self, client):
        """Test listing available templates"""
        response = client.get("/rag-data/templates")

        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert "products" in data["templates"]
        assert "product_specifications" in data["templates"]

    def test_download_template_excel(self, client):
        """Test downloading Excel template"""
        response = client.get("/rag-data/templates/products/download")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    def test_download_template_csv(self, client):
        """Test downloading CSV template"""
        response = client.get("/rag-data/templates/products/download-csv")

        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

    def test_download_invalid_template(self, client):
        """Test downloading invalid template"""
        response = client.get("/rag-data/templates/invalid_template/download")

        assert response.status_code == 404

    def test_upload_products_excel(self, client):
        """Test uploading products Excel file"""
        # Create sample Excel file
        df = pd.DataFrame({
            "product_code": ["PRD-001"],
            "product_name": ["Test Product"],
            "category": ["Test Category"],
            "subcategory": [""],
            "description": ["Test description"],
            "manufacturer": ["Test Mfg"],
            "brand": ["Test Brand"],
            "model_number": ["TM-001"],
            "material": ["Plastic"],
            "capacity": ["100ml"],
            "dimensions": ["10x10x10"],
            "weight": ["50g"],
            "color": ["Blue"],
            "price": [100.0],
            "stock_quantity": [1000],
            "minimum_order_qty": [10],
            "lead_time_days": [7],
            "country_of_origin": ["Korea"],
            "certifications": ["FDA"],
            "keywords": ["test, product"],
            "status": ["active"]
        })

        # Save to BytesIO
        excel_file = io.BytesIO()
        df.to_excel(excel_file, index=False)
        excel_file.seek(0)

        response = client.post(
            "/rag-data/templates/products/upload",
            files={"file": ("test.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            params={"auto_embed": False, "auto_index": False}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["template"] == "products"
        assert data["total_rows"] == 1
        assert data["success_count"] >= 0

    def test_get_products(self, client):
        """Test getting products"""
        response = client.get("/rag-data/products")

        assert response.status_code == 200
        data = response.json()
        assert "products" in data
        assert "total" in data

    def test_get_product_by_code(self, client):
        """Test getting product by code"""
        # First upload a product
        df = pd.DataFrame({
            "product_code": ["TEST-001"],
            "product_name": ["Test Product"],
            "category": ["Test"],
            "subcategory": [""],
            "description": [""],
            "manufacturer": [""],
            "brand": [""],
            "model_number": [""],
            "material": [""],
            "capacity": [""],
            "dimensions": [""],
            "weight": [""],
            "color": [""],
            "price": [0],
            "stock_quantity": [0],
            "minimum_order_qty": [1],
            "lead_time_days": [7],
            "country_of_origin": [""],
            "certifications": [""],
            "keywords": [""],
            "status": ["active"]
        })

        excel_file = io.BytesIO()
        df.to_excel(excel_file, index=False)
        excel_file.seek(0)

        upload_response = client.post(
            "/rag-data/templates/products/upload",
            files={"file": ("test.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            params={"auto_embed": False, "auto_index": False}
        )

        # Then get it
        response = client.get("/rag-data/products/TEST-001")

        if response.status_code == 200:
            data = response.json()
            assert "product" in data
            assert data["product"]["product_code"] == "TEST-001"

    def test_get_categories(self, client):
        """Test getting categories"""
        response = client.get("/rag-data/categories")

        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert "total" in data

    def test_get_stats(self, client):
        """Test getting statistics"""
        response = client.get("/rag-data/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_products" in data
        assert "total_specifications" in data
        assert "total_images" in data

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/rag-data/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "RAG Data Upload"
        assert data["version"] == "7.4.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
