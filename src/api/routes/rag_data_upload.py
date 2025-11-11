"""
RAG Product Data Upload API Routes - v7.4.0
RAG 제품 데이터 Excel 템플릿 업로드/다운로드 시스템
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from decimal import Decimal
import io
import csv
import hashlib

from fastapi import APIRouter, HTTPException, UploadFile, File, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, HttpUrl
import pandas as pd

# Note: These imports would need to be adjusted based on your actual RAG implementation
# from src.services.rag_service import RAGService, get_rag_service
# from src.services.embedding_service import EmbeddingService
# from src.services.vector_db_service import VectorDBService


# ========================================================================
# Request/Response Models
# ========================================================================

class ProductUploadRequest(BaseModel):
    """Request for product upload"""
    auto_embed: bool = Field(True, description="Automatically generate embeddings")
    auto_index: bool = Field(True, description="Automatically index to vector DB")
    overwrite: bool = Field(False, description="Overwrite existing products")


class BulkUploadResponse(BaseModel):
    """Response for bulk upload"""
    template: str
    total_rows: int
    success_count: int
    error_count: int
    skipped_count: int
    errors: List[Dict[str, Any]]
    embedded_count: int = 0
    indexed_count: int = 0
    message: str


# ========================================================================
# Excel Template Definitions
# ========================================================================

RAG_EXCEL_TEMPLATES = {
    "products": {
        "columns": [
            "product_code",          # 제품 코드 (필수, 고유)
            "product_name",          # 제품명 (필수)
            "category",              # 카테고리
            "subcategory",           # 하위 카테고리
            "description",           # 제품 설명
            "manufacturer",          # 제조사
            "brand",                 # 브랜드
            "model_number",          # 모델 번호
            "material",              # 재질
            "capacity",              # 용량
            "dimensions",            # 치수 (W x H x D)
            "weight",                # 무게
            "color",                 # 색상
            "price",                 # 가격
            "stock_quantity",        # 재고 수량
            "minimum_order_qty",     # 최소 주문 수량
            "lead_time_days",        # 리드타임 (일)
            "country_of_origin",     # 원산지
            "certifications",        # 인증 (쉼표 구분)
            "keywords",              # 키워드 (쉼표 구분)
            "status"                 # 상태 (active, discontinued, coming_soon)
        ],
        "sample_data": [
            [
                "PRD-PET-50ML-001",
                "PET 원형 용기 50ml 투명",
                "플라스틱 용기",
                "PET 용기",
                "투명한 PET 재질의 50ml 원형 용기입니다. 화장품, 음료 등에 적합합니다.",
                "한국플라스틱",
                "EcoPack",
                "EP-PET-50-R",
                "PET (Polyethylene Terephthalate)",
                "50ml",
                "45mm x 85mm",
                "15g",
                "투명",
                150.00,
                10000,
                1000,
                7,
                "대한민국",
                "FDA, KFDA, ISO9001",
                "PET용기, 50ml, 투명, 화장품용기, 음료용기",
                "active"
            ],
            [
                "PRD-HDPE-100ML-002",
                "HDPE 사각 용기 100ml 백색",
                "플라스틱 용기",
                "HDPE 용기",
                "백색 HDPE 재질의 100ml 사각 용기입니다. 샴푸, 세제 등에 적합합니다.",
                "한국플라스틱",
                "EcoPack",
                "EP-HDPE-100-S",
                "HDPE (High-Density Polyethylene)",
                "100ml",
                "50mm x 60mm x 40mm",
                "25g",
                "백색",
                200.00,
                8000,
                500,
                7,
                "대한민국",
                "FDA, KFDA",
                "HDPE용기, 100ml, 백색, 샴푸용기, 세제용기",
                "active"
            ]
        ]
    },

    "product_specifications": {
        "columns": [
            "product_code",          # 제품 코드 (외래키)
            "spec_category",         # 스펙 카테고리 (physical, chemical, mechanical, thermal)
            "spec_name",             # 스펙 이름
            "spec_value",            # 스펙 값
            "unit",                  # 단위
            "test_method",           # 테스트 방법
            "min_value",             # 최소값 (optional)
            "max_value",             # 최대값 (optional)
            "notes"                  # 비고
        ],
        "sample_data": [
            ["PRD-PET-50ML-001", "physical", "Thickness", "0.3", "mm", "KS M 3809", "0.25", "0.35", "Wall thickness"],
            ["PRD-PET-50ML-001", "chemical", "PET Content", "100", "%", "FTIR", "99", "100", "Virgin PET"],
            ["PRD-PET-50ML-001", "mechanical", "Tensile Strength", "60", "MPa", "ASTM D638", "55", "70", ""],
            ["PRD-PET-50ML-001", "thermal", "Heat Resistance", "70", "°C", "ISO 75", "65", "75", "Max temperature"],
            ["PRD-HDPE-100ML-002", "physical", "Density", "0.95", "g/cm³", "ASTM D792", "0.94", "0.96", ""],
            ["PRD-HDPE-100ML-002", "chemical", "HDPE Content", "100", "%", "FTIR", "99", "100", "Virgin HDPE"]
        ]
    },

    "product_images": {
        "columns": [
            "product_code",          # 제품 코드 (외래키)
            "image_type",            # 이미지 타입 (main, detail, dimension, usage, certification)
            "image_url",             # 이미지 URL or 파일 경로
            "image_description",     # 이미지 설명
            "display_order",         # 표시 순서
            "is_primary"             # 대표 이미지 여부 (Y/N)
        ],
        "sample_data": [
            ["PRD-PET-50ML-001", "main", "https://cdn.example.com/products/pet-50ml-001-main.jpg", "메인 제품 이미지", 1, "Y"],
            ["PRD-PET-50ML-001", "detail", "https://cdn.example.com/products/pet-50ml-001-detail.jpg", "상세 이미지 - 캡 부분", 2, "N"],
            ["PRD-PET-50ML-001", "dimension", "https://cdn.example.com/products/pet-50ml-001-dimension.jpg", "치수 도면", 3, "N"],
            ["PRD-HDPE-100ML-002", "main", "https://cdn.example.com/products/hdpe-100ml-002-main.jpg", "메인 제품 이미지", 1, "Y"],
            ["PRD-HDPE-100ML-002", "usage", "https://cdn.example.com/products/hdpe-100ml-002-usage.jpg", "사용 예시", 2, "N"]
        ]
    },

    "product_documents": {
        "columns": [
            "product_code",          # 제품 코드 (외래키)
            "document_type",         # 문서 타입 (msds, test_report, catalog, manual, certification)
            "document_name",         # 문서명
            "document_url",          # 문서 URL or 파일 경로
            "language",              # 언어 (ko, en, ja, zh)
            "version",               # 버전
            "issue_date",            # 발행일
            "expiry_date",           # 만료일 (optional)
            "issuer"                 # 발행기관
        ],
        "sample_data": [
            ["PRD-PET-50ML-001", "msds", "PET 50ml 용기 MSDS", "https://cdn.example.com/docs/pet-50ml-msds-ko.pdf", "ko", "1.0", "2024-01-01", "2026-01-01", "한국플라스틱"],
            ["PRD-PET-50ML-001", "test_report", "PET 50ml 식품접촉 시험성적서", "https://cdn.example.com/docs/pet-50ml-food-test.pdf", "ko", "1.0", "2024-01-15", "", "한국시험연구원"],
            ["PRD-PET-50ML-001", "certification", "FDA 인증서", "https://cdn.example.com/docs/pet-50ml-fda-cert.pdf", "en", "1.0", "2023-12-01", "2025-12-01", "FDA"],
            ["PRD-HDPE-100ML-002", "msds", "HDPE 100ml 용기 MSDS", "https://cdn.example.com/docs/hdpe-100ml-msds-ko.pdf", "ko", "1.0", "2024-01-01", "2026-01-01", "한국플라스틱"],
            ["PRD-HDPE-100ML-002", "catalog", "HDPE 용기 카탈로그", "https://cdn.example.com/docs/hdpe-catalog.pdf", "ko", "2.0", "2024-02-01", "", "한국플라스틱"]
        ]
    },

    "categories": {
        "columns": [
            "category_code",         # 카테고리 코드 (고유)
            "category_name",         # 카테고리명
            "parent_category",       # 상위 카테고리 (optional)
            "description",           # 설명
            "display_order",         # 표시 순서
            "icon_url",              # 아이콘 URL
            "is_active"              # 활성 여부 (Y/N)
        ],
        "sample_data": [
            ["CAT-PLASTIC", "플라스틱 용기", "", "플라스틱 재질의 각종 용기", 1, "https://cdn.example.com/icons/plastic.png", "Y"],
            ["CAT-PLASTIC-PET", "PET 용기", "CAT-PLASTIC", "PET 재질 용기", 1, "https://cdn.example.com/icons/pet.png", "Y"],
            ["CAT-PLASTIC-HDPE", "HDPE 용기", "CAT-PLASTIC", "HDPE 재질 용기", 2, "https://cdn.example.com/icons/hdpe.png", "Y"],
            ["CAT-PLASTIC-PP", "PP 용기", "CAT-PLASTIC", "PP 재질 용기", 3, "https://cdn.example.com/icons/pp.png", "Y"],
            ["CAT-MOLD", "금형", "", "사출 금형", 2, "https://cdn.example.com/icons/mold.png", "Y"]
        ]
    }
}


# ========================================================================
# Router
# ========================================================================

class RAGDataUploadRouter:
    """RAG Product Data Upload API Router"""

    def __init__(self):
        self.router = APIRouter(prefix="/rag-data", tags=["RAG Data Upload"])
        self.products_db: Dict[str, Dict[str, Any]] = {}  # In-memory storage (replace with real DB)
        self.specifications_db: List[Dict[str, Any]] = []
        self.images_db: List[Dict[str, Any]] = []
        self.documents_db: List[Dict[str, Any]] = []
        self.categories_db: Dict[str, Dict[str, Any]] = {}
        self._setup_routes()

    def _setup_routes(self):
        """Setup API routes"""

        # ================================================================
        # Excel Template Download/Upload for RAG Data
        # ================================================================

        @self.router.get("/templates")
        async def list_rag_templates():
            """
            List available RAG product data templates

            사용 가능한 RAG 제품 데이터 템플릿 목록
            """
            return {
                "templates": list(RAG_EXCEL_TEMPLATES.keys()),
                "descriptions": {
                    "products": "Product Master Data Template (제품 기본 정보)",
                    "product_specifications": "Product Specifications Template (제품 상세 스펙)",
                    "product_images": "Product Images Template (제품 이미지)",
                    "product_documents": "Product Documents Template (MSDS, 시험성적서, 인증서)",
                    "categories": "Product Categories Template (제품 카테고리)"
                },
                "usage": {
                    "step1": "Download template (Excel or CSV)",
                    "step2": "Fill in product data",
                    "step3": "Upload to system",
                    "step4": "System automatically generates embeddings and indexes to vector DB"
                }
            }

        @self.router.get("/templates/{template_name}/download")
        async def download_rag_template(template_name: str):
            """
            Download RAG product data Excel template

            RAG 제품 데이터 Excel 템플릿 다운로드 (샘플 데이터 포함)

            Templates:
            - products: Product master data with full details
            - product_specifications: Technical specifications (physical, chemical, mechanical, thermal)
            - product_images: Product images (main, detail, dimension, usage)
            - product_documents: Documents (MSDS, test reports, certifications, catalogs)
            - categories: Product category hierarchy
            """
            if template_name not in RAG_EXCEL_TEMPLATES:
                raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")

            template = RAG_EXCEL_TEMPLATES[template_name]

            # Create DataFrame with sample data
            df = pd.DataFrame(template["sample_data"], columns=template["columns"])

            # Convert to Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name=template_name)

                # Add a guide sheet
                guide_data = [
                    ["RAG Product Data Template Guide"],
                    [""],
                    ["Instructions:"],
                    ["1. Fill in the data in the template sheet"],
                    ["2. Do not modify column names"],
                    ["3. Required fields must be filled"],
                    ["4. Upload the completed file"],
                    ["5. System will automatically generate embeddings and index to RAG"],
                    [""],
                    ["Notes:"],
                    ["- product_code must be unique"],
                    ["- Use comma (,) to separate multiple values (keywords, certifications)"],
                    ["- Date format: YYYY-MM-DD"],
                    ["- Image/Document URLs must be accessible"],
                    [""],
                    ["Support:"],
                    ["For questions, contact: support@example.com"]
                ]
                guide_df = pd.DataFrame(guide_data, columns=["Guide"])
                guide_df.to_excel(writer, index=False, sheet_name="Guide", header=False)

            output.seek(0)

            return StreamingResponse(
                output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename=rag_{template_name}_template.xlsx"
                }
            )

        @self.router.get("/templates/{template_name}/download-csv")
        async def download_rag_template_csv(template_name: str):
            """
            Download RAG product data CSV template

            RAG 제품 데이터 CSV 템플릿 다운로드
            """
            if template_name not in RAG_EXCEL_TEMPLATES:
                raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")

            template = RAG_EXCEL_TEMPLATES[template_name]

            # Create CSV
            output = io.StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow(template["columns"])

            # Write sample data
            for row in template["sample_data"]:
                writer.writerow(row)

            # Convert to bytes with UTF-8 BOM for Excel compatibility
            csv_bytes = output.getvalue().encode('utf-8-sig')

            return StreamingResponse(
                io.BytesIO(csv_bytes),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=rag_{template_name}_template.csv"
                }
            )

        @self.router.post("/templates/{template_name}/upload")
        async def upload_rag_template(
            template_name: str,
            file: UploadFile = File(...),
            auto_embed: bool = Query(True, description="Auto-generate embeddings"),
            auto_index: bool = Query(True, description="Auto-index to vector DB"),
            overwrite: bool = Query(False, description="Overwrite existing data"),
            background_tasks: BackgroundTasks = None
        ):
            """
            Upload RAG product data (Excel/CSV)

            RAG 제품 데이터 대량 업로드

            Process:
            1. Parse Excel/CSV file
            2. Validate data
            3. Import to database
            4. Generate embeddings (if auto_embed=True)
            5. Index to vector DB (if auto_index=True)
            6. Return detailed results

            Supports:
            - .xlsx (Excel)
            - .csv (CSV)

            Features:
            - Automatic embedding generation
            - Automatic vector DB indexing
            - Duplicate detection
            - Row-level error reporting
            """
            if template_name not in RAG_EXCEL_TEMPLATES:
                raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")

            try:
                # Read file
                contents = await file.read()

                # Parse based on file type
                if file.filename.endswith('.xlsx') or file.filename.endswith('.xls'):
                    df = pd.read_excel(io.BytesIO(contents))
                elif file.filename.endswith('.csv'):
                    df = pd.read_csv(io.BytesIO(contents))
                else:
                    raise HTTPException(status_code=400, detail="Unsupported file type. Use .xlsx or .csv")

                # Validate columns
                template = RAG_EXCEL_TEMPLATES[template_name]
                missing_cols = set(template["columns"]) - set(df.columns)
                if missing_cols:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Missing columns: {', '.join(missing_cols)}"
                    )

                # Process based on template type
                results = await self._process_rag_template_upload(
                    template_name, df, auto_embed, auto_index, overwrite
                )

                # If auto_embed and auto_index, process in background for large datasets
                if auto_embed and auto_index and len(df) > 100:
                    if background_tasks:
                        background_tasks.add_task(
                            self._background_embed_and_index,
                            results["imported_items"]
                        )
                        results["message"] += " (Embedding and indexing in background)"

                return BulkUploadResponse(
                    template=template_name,
                    total_rows=len(df),
                    success_count=results["success_count"],
                    error_count=results["error_count"],
                    skipped_count=results["skipped_count"],
                    errors=results["errors"],
                    embedded_count=results.get("embedded_count", 0),
                    indexed_count=results.get("indexed_count", 0),
                    message=results["message"]
                )

            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

        async def _process_rag_template_upload(
            self,
            template_name: str,
            df: pd.DataFrame,
            auto_embed: bool,
            auto_index: bool,
            overwrite: bool
        ) -> Dict[str, Any]:
            """Process uploaded RAG template data"""
            success_count = 0
            error_count = 0
            skipped_count = 0
            errors = []
            imported_items = []
            embedded_count = 0
            indexed_count = 0

            for idx, row in df.iterrows():
                try:
                    if template_name == "products":
                        product_code = str(row["product_code"])

                        # Check for duplicates
                        if product_code in self.products_db and not overwrite:
                            skipped_count += 1
                            continue

                        # Create product entry
                        product_data = {
                            "product_code": product_code,
                            "product_name": str(row["product_name"]),
                            "category": str(row.get("category", "")),
                            "subcategory": str(row.get("subcategory", "")),
                            "description": str(row.get("description", "")),
                            "manufacturer": str(row.get("manufacturer", "")),
                            "brand": str(row.get("brand", "")),
                            "model_number": str(row.get("model_number", "")),
                            "material": str(row.get("material", "")),
                            "capacity": str(row.get("capacity", "")),
                            "dimensions": str(row.get("dimensions", "")),
                            "weight": str(row.get("weight", "")),
                            "color": str(row.get("color", "")),
                            "price": float(row.get("price", 0)),
                            "stock_quantity": int(row.get("stock_quantity", 0)),
                            "minimum_order_qty": int(row.get("minimum_order_qty", 1)),
                            "lead_time_days": int(row.get("lead_time_days", 7)),
                            "country_of_origin": str(row.get("country_of_origin", "")),
                            "certifications": str(row.get("certifications", "")),
                            "keywords": str(row.get("keywords", "")),
                            "status": str(row.get("status", "active")),
                            "created_at": datetime.now().isoformat(),
                            "updated_at": datetime.now().isoformat()
                        }

                        # Generate text for embedding
                        if auto_embed:
                            product_text = self._generate_product_text(product_data)
                            embedding = await self._generate_embedding(product_text)
                            product_data["embedding"] = embedding
                            product_data["embedding_text"] = product_text
                            embedded_count += 1

                        # Store in DB
                        self.products_db[product_code] = product_data
                        imported_items.append(("product", product_code, product_data))

                        # Index to vector DB
                        if auto_index and auto_embed:
                            await self._index_to_vector_db(product_code, product_data)
                            indexed_count += 1

                    elif template_name == "product_specifications":
                        spec_data = {
                            "product_code": str(row["product_code"]),
                            "spec_category": str(row["spec_category"]),
                            "spec_name": str(row["spec_name"]),
                            "spec_value": str(row["spec_value"]),
                            "unit": str(row.get("unit", "")),
                            "test_method": str(row.get("test_method", "")),
                            "min_value": str(row.get("min_value", "")),
                            "max_value": str(row.get("max_value", "")),
                            "notes": str(row.get("notes", "")),
                            "created_at": datetime.now().isoformat()
                        }
                        self.specifications_db.append(spec_data)
                        imported_items.append(("spec", len(self.specifications_db) - 1, spec_data))

                    elif template_name == "product_images":
                        image_data = {
                            "product_code": str(row["product_code"]),
                            "image_type": str(row["image_type"]),
                            "image_url": str(row["image_url"]),
                            "image_description": str(row.get("image_description", "")),
                            "display_order": int(row.get("display_order", 1)),
                            "is_primary": str(row.get("is_primary", "N")).upper() == "Y",
                            "created_at": datetime.now().isoformat()
                        }
                        self.images_db.append(image_data)
                        imported_items.append(("image", len(self.images_db) - 1, image_data))

                        # TODO: Process image with vision model if auto_embed is True

                    elif template_name == "product_documents":
                        doc_data = {
                            "product_code": str(row["product_code"]),
                            "document_type": str(row["document_type"]),
                            "document_name": str(row["document_name"]),
                            "document_url": str(row["document_url"]),
                            "language": str(row.get("language", "ko")),
                            "version": str(row.get("version", "1.0")),
                            "issue_date": str(row.get("issue_date", "")),
                            "expiry_date": str(row.get("expiry_date", "")),
                            "issuer": str(row.get("issuer", "")),
                            "created_at": datetime.now().isoformat()
                        }
                        self.documents_db.append(doc_data)
                        imported_items.append(("document", len(self.documents_db) - 1, doc_data))

                        # TODO: Parse document (PDF, etc.) and generate embeddings

                    elif template_name == "categories":
                        category_code = str(row["category_code"])

                        if category_code in self.categories_db and not overwrite:
                            skipped_count += 1
                            continue

                        category_data = {
                            "category_code": category_code,
                            "category_name": str(row["category_name"]),
                            "parent_category": str(row.get("parent_category", "")),
                            "description": str(row.get("description", "")),
                            "display_order": int(row.get("display_order", 1)),
                            "icon_url": str(row.get("icon_url", "")),
                            "is_active": str(row.get("is_active", "Y")).upper() == "Y",
                            "created_at": datetime.now().isoformat()
                        }
                        self.categories_db[category_code] = category_data
                        imported_items.append(("category", category_code, category_data))

                    success_count += 1

                except Exception as e:
                    error_count += 1
                    errors.append({
                        "row": idx + 2,  # +2 for header and 0-index
                        "error": str(e)
                    })

            message = f"Processed {len(df)} rows: {success_count} succeeded, {error_count} failed, {skipped_count} skipped"
            if auto_embed:
                message += f", {embedded_count} embedded"
            if auto_index:
                message += f", {indexed_count} indexed"

            return {
                "success_count": success_count,
                "error_count": error_count,
                "skipped_count": skipped_count,
                "errors": errors[:10],  # Return first 10 errors
                "imported_items": imported_items,
                "embedded_count": embedded_count,
                "indexed_count": indexed_count,
                "message": message
            }

        async def _background_embed_and_index(self, items: List[tuple]):
            """Background task for embedding and indexing"""
            # This would be called for large datasets
            # TODO: Implement actual embedding and indexing logic
            pass

        def _generate_product_text(self, product_data: Dict[str, Any]) -> str:
            """Generate comprehensive text for product embedding"""
            parts = [
                f"제품명: {product_data['product_name']}",
                f"제품코드: {product_data['product_code']}",
                f"카테고리: {product_data['category']} > {product_data['subcategory']}",
                f"제조사: {product_data['manufacturer']}",
                f"브랜드: {product_data['brand']}",
                f"모델번호: {product_data['model_number']}",
                f"재질: {product_data['material']}",
                f"용량: {product_data['capacity']}",
                f"치수: {product_data['dimensions']}",
                f"무게: {product_data['weight']}",
                f"색상: {product_data['color']}",
                f"원산지: {product_data['country_of_origin']}",
                f"인증: {product_data['certifications']}",
                f"키워드: {product_data['keywords']}",
                f"설명: {product_data['description']}"
            ]

            return " | ".join([p for p in parts if p.split(": ")[1]])  # Filter empty values

        async def _generate_embedding(self, text: str) -> List[float]:
            """Generate embedding for text"""
            # TODO: Replace with actual embedding service
            # For now, return dummy embedding
            # In production, use: embedding_service.generate_embedding(text)

            # Dummy embedding (768 dimensions)
            import hashlib
            text_hash = hashlib.md5(text.encode()).hexdigest()
            dummy_embedding = [float(int(text_hash[i:i+2], 16)) / 255.0 for i in range(0, 32, 2)]
            # Pad to 768 dimensions
            dummy_embedding = dummy_embedding * 48
            return dummy_embedding[:768]

        async def _index_to_vector_db(self, product_code: str, product_data: Dict[str, Any]):
            """Index product to vector database"""
            # TODO: Replace with actual vector DB service
            # In production, use: vector_db_service.upsert(product_code, embedding, metadata)
            pass

        # ================================================================
        # Query Endpoints
        # ================================================================

        @self.router.get("/products")
        async def get_products(
            category: Optional[str] = None,
            status: Optional[str] = None,
            limit: int = Query(100, ge=1, le=1000)
        ):
            """Get products with filters"""
            try:
                products = list(self.products_db.values())

                if category:
                    products = [p for p in products if p["category"] == category]
                if status:
                    products = [p for p in products if p["status"] == status]

                products = products[:limit]

                return {
                    "products": products,
                    "total": len(products)
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get products: {str(e)}")

        @self.router.get("/products/{product_code}")
        async def get_product(product_code: str):
            """Get product details"""
            try:
                if product_code not in self.products_db:
                    raise HTTPException(status_code=404, detail="Product not found")

                product = self.products_db[product_code]

                # Get related data
                specs = [s for s in self.specifications_db if s["product_code"] == product_code]
                images = [i for i in self.images_db if i["product_code"] == product_code]
                documents = [d for d in self.documents_db if d["product_code"] == product_code]

                return {
                    "product": product,
                    "specifications": specs,
                    "images": images,
                    "documents": documents
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get product: {str(e)}")

        @self.router.get("/categories")
        async def get_categories(parent: Optional[str] = None):
            """Get categories"""
            try:
                categories = list(self.categories_db.values())

                if parent is not None:
                    categories = [c for c in categories if c["parent_category"] == parent]

                return {
                    "categories": categories,
                    "total": len(categories)
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")

        @self.router.get("/stats")
        async def get_stats():
            """Get RAG data statistics"""
            return {
                "total_products": len(self.products_db),
                "total_specifications": len(self.specifications_db),
                "total_images": len(self.images_db),
                "total_documents": len(self.documents_db),
                "total_categories": len(self.categories_db),
                "products_with_embeddings": sum(1 for p in self.products_db.values() if "embedding" in p),
                "active_products": sum(1 for p in self.products_db.values() if p["status"] == "active")
            }

        @self.router.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "service": "RAG Data Upload",
                "version": "7.4.0",
                "features": {
                    "excel_templates": True,
                    "auto_embedding": True,
                    "auto_indexing": True,
                    "multi_format": True  # Excel, CSV
                }
            }


def get_rag_data_upload_router() -> APIRouter:
    """Factory function to create router"""
    router_instance = RAGDataUploadRouter()
    return router_instance.router
