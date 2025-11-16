"""
Ultimate Preprocessing API Routes - v7.4.0
Complete API for Ultimate Data Preprocessing System
"""

from typing import List, Dict, Optional, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field

from src.services.ultimate_preprocessing_service import (
    UltimatePreprocessingService,
    FileType,
    ProcessingStatus,
    get_ultimate_preprocessing_service
)


class PreprocessingStatsResponse(BaseModel):
    """Statistics response"""
    total_processed: int
    excel_processed: int
    pdf_processed: int
    image_processed: int
    quality_failures: int
    avg_quality_score: float
    avg_processing_time_ms: float


class UltimatePreprocessingRouter:
    """Ultimate Preprocessing API Router"""

    def __init__(self, service: Optional[UltimatePreprocessingService] = None):
        self.router = APIRouter(prefix="/ultimate-preprocessing", tags=["Ultimate Preprocessing"])
        self.service = service or get_ultimate_preprocessing_service()
        self._setup_routes()

    def _setup_routes(self):
        """Setup API routes"""

        @self.router.post("/process-file")
        async def process_file(file: UploadFile = File(...)):
            """
            Process any file type automatically
            
            Supported:
            - Excel (.xlsx, .xls, .xlsm)
            - PDF (.pdf)
            - Images (.jpg, .png, .bmp, .tiff)
            - CSV (.csv)
            - JSON (.json)
            """
            try:
                # Save uploaded file
                import tempfile
                import os
                
                suffix = os.path.splitext(file.filename)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
                    content = await file.read()
                    temp.write(content)
                    temp_path = temp.name
                
                # Process file
                result = await self.service.process_file(temp_path)
                
                # Clean up
                os.unlink(temp_path)
                
                return result.dict()
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

        @self.router.post("/process-excel")
        async def process_excel(file: UploadFile = File(...)):
            """Process Excel file with advanced features"""
            try:
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp:
                    content = await file.read()
                    temp.write(content)
                    temp_path = temp.name
                
                result = await self.service.process_excel(temp_path)
                os.unlink(temp_path)
                
                return result.dict()
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Excel processing failed: {str(e)}")

        @self.router.post("/process-pdf")
        async def process_pdf(file: UploadFile = File(...)):
            """Process PDF file with OCR and table extraction"""
            try:
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp:
                    content = await file.read()
                    temp.write(content)
                    temp_path = temp.name
                
                result = await self.service.process_pdf(temp_path)
                os.unlink(temp_path)
                
                return result.dict()
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"PDF processing failed: {str(e)}")

        @self.router.post("/process-image")
        async def process_image(file: UploadFile = File(...)):
            """Process image with OCR and object detection"""
            try:
                import tempfile
                import os
                
                suffix = os.path.splitext(file.filename)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
                    content = await file.read()
                    temp.write(content)
                    temp_path = temp.name
                
                result = await self.service.process_image(temp_path)
                os.unlink(temp_path)
                
                return result.dict()
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")

        @self.router.get("/stats", response_model=PreprocessingStatsResponse)
        async def get_stats():
            """Get comprehensive preprocessing statistics"""
            try:
                stats = self.service.get_stats()
                return PreprocessingStatsResponse(**stats)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

        @self.router.post("/batch-process")
        async def batch_process(files: List[UploadFile] = File(...)):
            """Process multiple files in batch"""
            try:
                results = []
                for file in files:
                    import tempfile
                    import os
                    
                    suffix = os.path.splitext(file.filename)[1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
                        content = await file.read()
                        temp.write(content)
                        temp_path = temp.name
                    
                    result = await self.service.process_file(temp_path)
                    os.unlink(temp_path)
                    
                    results.append({
                        "filename": file.filename,
                        "status": result.status,
                        "quality_score": result.quality.overall_score
                    })
                
                return {
                    "total_files": len(files),
                    "results": results
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")

        @self.router.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "service": "Ultimate Preprocessing",
                "version": "7.4.0",
                "features": {
                    "ocr": self.service.enable_ocr,
                    "object_detection": self.service.enable_object_detection,
                    "quality_validation": self.service.enable_quality_validation,
                    "enrichment": self.service.enable_enrichment
                },
                "stats": self.service.get_stats()
            }


def get_ultimate_preprocessing_router(service: Optional[UltimatePreprocessingService] = None) -> APIRouter:
    """Factory function to create router"""
    router_instance = UltimatePreprocessingRouter(service=service)
    return router_instance.router
