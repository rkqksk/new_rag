# Image-Based Product Search - Drag & Drop Design
**Created**: 2025-10-22
**Feature**: Drag-and-drop image search for container products
**Status**: Ready to Implement

## Overview

Enable customers to **drag-and-drop** container images directly onto the chat interface to find visually similar products using OpenCLIP embeddings.

## User Experience

### Primary Method: Drag & Drop
```
┌─────────────────────────────────────┐
│  Q&A Chat Interface                 │
│                                     │
│  [User drags image file over chat] │
│                                     │
│  ┌───────────────────────────────┐ │
│  │ 📷 Drop image here to search  │ │ ← Dropzone overlay
│  │    JPEG, JPG, PNG (max 5MB)   │ │
│  └───────────────────────────────┘ │
│                                     │
│  [User drops file]                  │
│                                     │
│  ┌───────────────────────────────┐ │
│  │ [Preview] container.jpg       │ │
│  │ Add text: "50ml only" (optional)│
│  │ [Search] [×Cancel]            │ │
│  └───────────────────────────────┘ │
└─────────────────────────────────────┘
```

### Secondary Method: Click to Upload
- Small "📷" icon button next to text input
- Opens file picker as fallback

## Implementation

### Frontend Changes (qa_chat.html)

#### 1. CSS - Drag & Drop Overlay
```css
/* Dropzone overlay - appears on drag */
.dropzone-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(102, 126, 234, 0.95);
    display: none;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    border-radius: 20px;
}

.dropzone-overlay.active {
    display: flex;
}

.dropzone-content {
    text-align: center;
    color: white;
}

.dropzone-content .icon {
    font-size: 64px;
    margin-bottom: 20px;
}

.dropzone-content .text {
    font-size: 24px;
    font-weight: 600;
    margin-bottom: 10px;
}

.dropzone-content .hint {
    font-size: 14px;
    opacity: 0.9;
}

/* Image preview card */
.image-preview-card {
    display: none;
    margin: 15px 0;
    padding: 15px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.image-preview-card.active {
    display: flex;
    gap: 15px;
    align-items: center;
}

.preview-thumbnail {
    width: 100px;
    height: 100px;
    object-fit: cover;
    border-radius: 8px;
}

.preview-info {
    flex: 1;
}

.preview-filename {
    font-weight: 600;
    margin-bottom: 5px;
}

.preview-size {
    font-size: 12px;
    color: #666;
}

.optional-text {
    margin-top: 10px;
}

.optional-text input {
    width: 100%;
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 6px;
    font-size: 14px;
}

.preview-actions {
    display: flex;
    gap: 10px;
}

.btn-search {
    padding: 8px 20px;
    background: #4CAF50;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 600;
}

.btn-cancel {
    padding: 8px 20px;
    background: #ff4444;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
}

/* Small upload icon button */
.upload-icon-btn {
    padding: 10px;
    background: transparent;
    border: none;
    cursor: pointer;
    font-size: 20px;
    opacity: 0.7;
    transition: opacity 0.2s;
}

.upload-icon-btn:hover {
    opacity: 1;
}
```

#### 2. HTML Structure
```html
<div class="container">
    <!-- Dropzone overlay -->
    <div class="dropzone-overlay" id="dropzone">
        <div class="dropzone-content">
            <div class="icon">📷</div>
            <div class="text">Drop image here to search</div>
            <div class="hint">JPEG, JPG, PNG (max 5MB)</div>
        </div>
    </div>

    <!-- Existing header -->
    <div class="header">...</div>

    <!-- Existing chat container -->
    <div class="chat-container" id="chat">...</div>

    <!-- Image preview card -->
    <div class="image-preview-card" id="preview-card">
        <img class="preview-thumbnail" id="preview-img" src="" alt="Preview">
        <div class="preview-info">
            <div class="preview-filename" id="preview-filename"></div>
            <div class="preview-size" id="preview-size"></div>
            <div class="optional-text">
                <input type="text" id="optional-query" placeholder="Add text filter (optional): e.g., 50ml, PET only">
            </div>
        </div>
        <div class="preview-actions">
            <button class="btn-search" id="btn-search-image">Search</button>
            <button class="btn-cancel" id="btn-cancel">Cancel</button>
        </div>
    </div>

    <!-- Input area -->
    <div class="input-container">
        <textarea id="query-input" placeholder="Type or drag image here..."></textarea>

        <!-- Hidden file input -->
        <input type="file" id="file-input" accept="image/jpeg,image/jpg,image/png" style="display:none">

        <!-- Small upload icon -->
        <button class="upload-icon-btn" id="upload-icon" title="Upload image">📷</button>

        <button id="send-btn">Send</button>
    </div>
</div>
```

#### 3. JavaScript - Drag & Drop Logic
```javascript
// Global state
let selectedImageFile = null;

// Get elements
const container = document.querySelector('.container');
const dropzone = document.getElementById('dropzone');
const previewCard = document.getElementById('preview-card');
const fileInput = document.getElementById('file-input');

// Prevent default drag behaviors
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    container.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

// Highlight dropzone when dragging over
['dragenter', 'dragover'].forEach(eventName => {
    container.addEventListener(eventName, () => {
        dropzone.classList.add('active');
    }, false);
});

['dragleave', 'drop'].forEach(eventName => {
    container.addEventListener(eventName, () => {
        dropzone.classList.remove('active');
    }, false);
});

// Handle dropped files
container.addEventListener('drop', handleDrop, false);

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;

    if (files.length > 0) {
        handleFile(files[0]);
    }
}

// Handle file input click
document.getElementById('upload-icon').addEventListener('click', () => {
    fileInput.click();
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
});

// Validate and preview file
function handleFile(file) {
    // Validate type
    if (!['image/jpeg', 'image/jpg', 'image/png'].includes(file.type)) {
        alert('❌ JPEG, JPG, PNG 파일만 업로드 가능합니다.');
        return;
    }

    // Validate size (5MB)
    if (file.size > 5 * 1024 * 1024) {
        alert('❌ 파일 크기는 5MB를 초과할 수 없습니다.');
        return;
    }

    selectedImageFile = file;

    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        document.getElementById('preview-img').src = e.target.result;
        document.getElementById('preview-filename').textContent = file.name;
        document.getElementById('preview-size').textContent = formatFileSize(file.size);
        previewCard.classList.add('active');
    };
    reader.readAsDataURL(file);
}

// Format file size
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// Cancel button
document.getElementById('btn-cancel').addEventListener('click', () => {
    selectedImageFile = null;
    previewCard.classList.remove('active');
    fileInput.value = '';
    document.getElementById('optional-query').value = '';
});

// Search button
document.getElementById('btn-search-image').addEventListener('click', async () => {
    if (!selectedImageFile) return;

    const optionalText = document.getElementById('optional-query').value.trim();

    // Create FormData
    const formData = new FormData();
    formData.append('image', selectedImageFile);
    if (optionalText) {
        formData.append('query', optionalText);
    }

    try {
        // Show loading in chat
        addMessage('user', `🔍 Searching by image: ${selectedImageFile.name}`);
        addMessage('bot', '⏳ Processing image...', true);

        const response = await fetch('/api/v1/search/image', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        // Remove loading message
        removeLoadingMessage();

        // Display results
        displayImageSearchResults(data);

        // Clear preview
        document.getElementById('btn-cancel').click();

    } catch (error) {
        console.error('Image search error:', error);
        removeLoadingMessage();
        addMessage('bot', '❌ 이미지 검색 중 오류가 발생했습니다.');
    }
});

// Display image search results
function displayImageSearchResults(data) {
    if (!data.results || data.results.length === 0) {
        addMessage('bot', '😞 유사한 제품을 찾지 못했습니다.');
        return;
    }

    let html = `<div class="message-text">
        🔍 <strong>이미지 검색 결과</strong> (${data.count}개 제품 발견)
    </div>`;

    html += '<div class="products-list">';
    data.results.forEach(product => {
        const similarity = (product.similarity_score * 100).toFixed(0);
        html += `
        <div class="product-card">
            <div class="product-image">
                <img src="${product.image_url}" alt="${product.product_name}"
                     onerror="this.src='/static/placeholder.png'">
            </div>
            <div class="product-info">
                <div class="product-name">${product.product_name}</div>
                <div class="product-category">${product.category}</div>
                <div class="similarity-badge">📊 ${similarity}% 유사</div>
            </div>
            <button class="detail-btn" onclick="viewProduct('${product.product_id}')">
                상세보기
            </button>
        </div>`;
    });
    html += '</div>';

    addMessage('bot', html);
}

// Helper functions
function addMessage(type, content, isLoading = false) {
    const chatContainer = document.getElementById('chat');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    if (isLoading) messageDiv.id = 'loading-message';

    messageDiv.innerHTML = `
        <div class="message-content">
            ${content}
        </div>
    `;

    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function removeLoadingMessage() {
    const loading = document.getElementById('loading-message');
    if (loading) loading.remove();
}
```

### Backend Implementation

#### File: `/app/services/image_search_service.py`
```python
"""Image-based product search service"""

import os
import uuid
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from PIL import Image
import torch
import open_clip

from qdrant_client import QdrantClient
from fastapi import UploadFile, HTTPException

logger = logging.getLogger(__name__)


class ImageSearchService:
    def __init__(self, qdrant_client: QdrantClient, device: str = "auto"):
        self.qdrant_client = qdrant_client

        # Auto-detect device
        if device == "auto":
            if torch.backends.mps.is_available():
                self.device = "mps"
            elif torch.cuda.is_available():
                self.device = "cuda"
            else:
                self.device = "cpu"
        else:
            self.device = device

        # Load OpenCLIP (same model as embedding pipeline)
        self.model, self.preprocess, _ = open_clip.create_model_and_transforms(
            model_name="ViT-H-14",
            pretrained="laion2b-s32b-b79k",
            device=self.device
        )
        logger.info(f"✅ ImageSearchService ready on {self.device}")

    def embed_image(self, image_path: str) -> List[float]:
        """Generate 1024-dim image embedding"""
        image = Image.open(image_path).convert("RGB")
        image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            embedding = self.model.encode_image(image_tensor)

        return embedding.squeeze(0).cpu().numpy().tolist()

    async def search_by_image(
        self,
        image_file: UploadFile,
        query_text: Optional[str] = None,
        top_k: int = 10,
        collection: str = "products_all"
    ) -> Dict[str, Any]:
        """Search for visually similar products"""

        search_id = str(uuid.uuid4())
        start_time = datetime.now()

        # Validate file
        if image_file.content_type not in ['image/jpeg', 'image/jpg', 'image/png']:
            raise HTTPException(400, "Only JPEG/PNG images supported")

        # Save temporarily
        upload_dir = Path("/tmp/rag_uploads")
        upload_dir.mkdir(exist_ok=True)
        temp_path = upload_dir / f"{search_id}_{image_file.filename}"

        try:
            content = await image_file.read()
            with open(temp_path, "wb") as f:
                f.write(content)

            # Generate embedding
            image_embedding = self.embed_image(str(temp_path))

            # IMPORTANT: This requires multi-vector Qdrant setup
            # Currently we only have text vectors stored
            # Need to regenerate with both text + image vectors

            # For now, return mock results
            # TODO: Implement actual Qdrant search with image vectors

            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return {
                "search_id": search_id,
                "search_type": "hybrid" if query_text else "image",
                "query_text": query_text,
                "image_filename": image_file.filename,
                "results": [],  # TODO: Real results from Qdrant
                "count": 0,
                "processing_time_ms": processing_time,
                "timestamp": datetime.now().isoformat(),
                "note": "Multi-vector Qdrant setup required - regenerating embeddings needed"
            }

        finally:
            if temp_path.exists():
                temp_path.unlink()
```

#### File: `/app/api/routes/image_routes.py`
```python
"""Image search routes"""

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from typing import Optional
import logging

from app.core.dependencies import get_qdrant_client
from app.services.image_search_service import ImageSearchService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/search", tags=["Image Search"])


@router.post("/image")
async def search_by_image(
    image: UploadFile = File(..., description="Container image (JPEG/JPG/PNG, max 5MB)"),
    query: Optional[str] = Form(None, description="Optional text filter"),
    top_k: int = Form(10, description="Number of results"),
    qdrant_client = Depends(get_qdrant_client)
):
    """
    🔍 Image-based product search with drag & drop support

    Upload a container image to find visually similar products.
    Optionally add text filters like "50ml only" or "PET material".
    """
    try:
        service = ImageSearchService(qdrant_client)
        results = await service.search_by_image(
            image_file=image,
            query_text=query,
            top_k=top_k
        )
        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image search error: {e}")
        raise HTTPException(500, detail=str(e))
```

## Next Steps

### Step 1: Update Qdrant Collections (Multi-Vector) ⚠️
**Current Problem**: Only text embeddings stored, not images

**Solution**: Regenerate embeddings with multi-vector config:
```python
# Update product_embedding_pipeline.py
vectors_config={
    "text": VectorParams(size=384, distance=Distance.COSINE),
    "image": VectorParams(size=1024, distance=Distance.COSINE)
}
```

### Step 2: Implement Backend
1. Create `ImageSearchService`
2. Add route to `main.py`
3. Test with Postman/curl

### Step 3: Update Frontend
1. Add drag-and-drop HTML/CSS
2. Add JavaScript handlers
3. Test with sample images

### Step 4: Testing
1. Drag-and-drop various image formats
2. Test with/without text filters
3. Validate similarity scores

---

**Status**: ✅ Design Ready
**Next**: Multi-vector Qdrant setup
**Priority**: HIGH (User requested feature)
