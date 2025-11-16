"""
Inquiry & Sample Request Routes
"""

import json
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter

from apps.api.models.schemas import InquiryRequest, SampleRequest

router = APIRouter(prefix="/api/v1", tags=["inquiries"])

# Data paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"


@router.post("/inquiries")
async def create_inquiry(inquiry: InquiryRequest):
    """Create product inquiry"""
    inquiries_file = DATA_DIR / "inquiries.json"

    # Load existing inquiries
    inquiries = []
    if inquiries_file.exists():
        with open(inquiries_file, "r", encoding="utf-8") as f:
            inquiries = json.load(f)

    # Add new inquiry
    inquiry_data = inquiry.dict()
    inquiry_data["inquiry_id"] = f"INQ_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    inquiry_data["status"] = "pending"
    inquiry_data["created_at"] = datetime.now().isoformat()

    inquiries.append(inquiry_data)

    # Save inquiries
    with open(inquiries_file, "w", encoding="utf-8") as f:
        json.dump(inquiries, f, ensure_ascii=False, indent=2)

    return {
        "success": True,
        "inquiry_id": inquiry_data["inquiry_id"],
        "message": "문의가 접수되었습니다",
    }


@router.get("/inquiries")
async def list_inquiries(limit: int = 50):
    """List all inquiries"""
    inquiries_file = DATA_DIR / "inquiries.json"

    if not inquiries_file.exists():
        return {"total": 0, "inquiries": []}

    with open(inquiries_file, "r", encoding="utf-8") as f:
        inquiries = json.load(f)

    # Sort by created_at descending
    inquiries.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return {"total": len(inquiries), "inquiries": inquiries[:limit]}


@router.post("/sample-request")
async def create_sample_request(request: SampleRequest):
    """Create sample request"""
    sample_requests_file = DATA_DIR / "sample_requests.json"

    # Load existing requests
    if sample_requests_file.exists():
        with open(sample_requests_file, "r", encoding="utf-8") as f:
            sample_requests = json.load(f)
    else:
        sample_requests = []

    # Add new request
    request_data = request.dict()
    request_data["id"] = str(uuid.uuid4())
    request_data["status"] = "pending"
    request_data["created_at"] = datetime.now().isoformat()

    sample_requests.append(request_data)

    # Save to file
    sample_requests_file.parent.mkdir(parents=True, exist_ok=True)
    with open(sample_requests_file, "w", encoding="utf-8") as f:
        json.dump(sample_requests, f, ensure_ascii=False, indent=2)

    return {
        "success": True,
        "message": "Sample request submitted successfully",
        "request_id": request_data["id"],
    }


@router.get("/sample-requests")
async def list_sample_requests(limit: int = 50, status: str = None):
    """List sample requests"""
    sample_requests_file = DATA_DIR / "sample_requests.json"

    if not sample_requests_file.exists():
        return {"success": True, "count": 0, "requests": []}

    with open(sample_requests_file, "r", encoding="utf-8") as f:
        all_requests = json.load(f)

    # Filter by status if provided
    if status:
        all_requests = [r for r in all_requests if r.get("status") == status]

    # Sort by created_at descending
    all_requests.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return {"success": True, "count": len(all_requests), "requests": all_requests[:limit]}
