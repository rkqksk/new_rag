"""
Excel Upload and Analysis Routes
공식 Excel 파일 업로드 및 데이터 품질 검증
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from qdrant_client import QdrantClient

from apps.api.core.dependencies import get_qdrant_client
from apps.api.services.excel_parser_service import ExcelParserService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/excel", tags=["Excel Management"])


@router.post("/analyze")
async def analyze_excel(
    filename: str, qdrant_client: QdrantClient = Depends(get_qdrant_client)
) -> Dict[str, Any]:
    """
    Excel 파일 분석 및 DB 비교

    Args:
        filename: raw/ 폴더에 업로드한 Excel 파일명

    Returns:
        비교 리포트
    """
    try:
        logger.info(f"📊 Analyzing Excel: {filename}")

        # 1. Excel 파싱
        parser = ExcelParserService()
        excel_products = parser.parse_excel(filename)

        if not excel_products:
            raise HTTPException(
                status_code=400, detail=f"Failed to parse Excel or no products found: {filename}"
            )

        # 2. Qdrant에서 모든 제품 가져오기
        points, _ = qdrant_client.scroll(
            collection_name="products_all", limit=1000, with_payload=True, with_vector=False
        )

        db_products = [p.payload for p in points if p.payload]

        # 3. 비교
        report = parser.compare_with_database(excel_products, db_products)

        # 4. 파싱 데이터 저장
        saved_path = parser.save_parsed_data(filename, excel_products)

        return {
            "status": "success",
            "filename": filename,
            "report": report,
            "parsed_data_saved": saved_path,
            "message": f"분석 완료: Excel {report['total_excel']}개 vs DB {report['total_db']}개",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing Excel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_excel_files() -> Dict[str, Any]:
    """
    업로드된 Excel 파일 목록 조회
    """
    try:
        parser = ExcelParserService()

        raw_files = list(parser.raw_dir.glob("*.xlsx"))
        processed_files = list(parser.processed_dir.glob("*.json"))
        image_files = list(parser.images_dir.glob("*"))

        return {
            "raw_files": [f.name for f in raw_files],
            "processed_files": [f.name for f in processed_files],
            "image_count": len(image_files),
            "upload_path": str(parser.raw_dir),
            "instructions": "Excel 파일을 upload_path에 복사 후 /analyze 호출",
        }

    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail=str(e))
