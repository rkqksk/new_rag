"""
Image Processing API Routes

Features:
- Watermark removal
- Text removal
- Image enhancement
- OCR preprocessing
"""

import io
import logging
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from PIL import Image

from apps.api.core.ocr.image_preprocessor import ImagePreprocessor
from apps.api.core.ocr.watermark_remover import (
    WatermarkRemover,
    remove_color_watermark,
    remove_watermark,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/image", tags=["Image Processing"])


@router.post("/remove-watermark")
async def remove_watermark_endpoint(
    image: UploadFile = File(
        ..., description="Image with watermark (JPEG/PNG, max 10MB)"
    ),
    method: str = Form(
        "telea",
        description="Inpainting method: 'telea' (fast), 'ns' (quality), 'lama' (best)",
    ),
    auto_detect: bool = Form(True, description="Auto-detect text regions"),
    regions: Optional[str] = Form(
        None,
        description="Manual regions as JSON: [[x,y,w,h], ...] e.g., '[[100,50,200,30]]'",
    ),
):
    """
    🎨 **Remove watermarks and text overlays from images**

    Upload an image to automatically remove watermarks, text, logos, or other unwanted elements.

    **Features**:
    - **Auto-detection**: Automatically finds and removes text/watermarks
    - **Manual regions**: Specify exact areas to remove
    - **Multiple algorithms**: Choose speed vs quality tradeoff

    **Inpainting Methods**:
    - `telea` (default): Fast Marching Method - best for thin text
    - `ns`: Navier-Stokes - better for larger regions
    - `lama`: State-of-the-art - highest quality (requires model download)

    **Example use cases**:
    - Remove copyright watermarks from product photos
    - Clean up text overlays before OCR
    - Remove logos or branding from images
    - Prepare images for product listings

    **Manual regions format**:
    ```json
    [[x1, y1, width1, height1], [x2, y2, width2, height2], ...]
    ```

    **Technical details**:
    - Uses PaddleOCR for text detection
    - OpenCV inpainting algorithms (TELEA, NS)
    - Optional LaMa model for best quality
    - Typical processing time: 1-3 seconds per image

    **Returns**:
    - Cleaned image (same format as input)
    - Content-Type: image/jpeg or image/png

    **Cost**: $0/month (100% open-source)
    """
    try:
        logger.info(
            f"Watermark removal request: {image.filename}, method={method}, "
            f"auto_detect={auto_detect}"
        )

        # Validate file type
        if not image.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {image.content_type}. Expected image/*",
            )

        # Read image
        contents = await image.read()
        pil_image = Image.open(io.BytesIO(contents))

        # Parse manual regions if provided
        manual_regions = None
        if regions:
            import json

            try:
                manual_regions = json.loads(regions)
                if not isinstance(manual_regions, list):
                    raise ValueError("Regions must be a list")
                for region in manual_regions:
                    if len(region) != 4:
                        raise ValueError("Each region must be [x, y, width, height]")
                logger.info(f"Manual regions: {manual_regions}")
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid regions JSON: {e}",
                )

        # Remove watermark
        clean_image = remove_watermark(
            image=pil_image,
            regions=manual_regions,
            method=method,
            auto_detect=auto_detect,
        )

        # Convert to bytes
        output = io.BytesIO()
        output_format = "PNG" if image.content_type == "image/png" else "JPEG"
        clean_image.save(output, format=output_format, quality=95)
        output.seek(0)

        logger.info(
            f"Watermark removal completed: {image.filename}, "
            f"format={output_format}"
        )

        # Return image
        media_type = f"image/{output_format.lower()}"
        return StreamingResponse(output, media_type=media_type)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Watermark removal error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Watermark removal failed: {str(e)}"
        )


@router.post("/remove-color-watermark")
async def remove_color_watermark_endpoint(
    image: UploadFile = File(..., description="Image with color watermark"),
    color_r: int = Form(255, description="Red channel (0-255)", ge=0, le=255),
    color_g: int = Form(255, description="Green channel (0-255)", ge=0, le=255),
    color_b: int = Form(255, description="Blue channel (0-255)", ge=0, le=255),
    tolerance: int = Form(
        30, description="Color tolerance (0-255)", ge=0, le=255
    ),
):
    """
    🎨 **Remove specific color watermarks**

    Remove watermarks of a specific color (e.g., white, semi-transparent).

    **Use cases**:
    - Remove white watermarks on product images
    - Clean up monochrome overlays
    - Remove single-color logos

    **How to find the color**:
    1. Use color picker tool on the watermark
    2. Get RGB values (e.g., 255, 255, 255 for white)
    3. Adjust tolerance based on how solid the watermark is

    **Examples**:
    - White watermark: `r=255, g=255, b=255, tolerance=30`
    - Light gray: `r=200, g=200, b=200, tolerance=20`
    - Semi-transparent: Increase tolerance to 50-80

    **Returns**:
    - Cleaned image with specified color removed

    **Cost**: $0/month (100% open-source)
    """
    try:
        logger.info(
            f"Color watermark removal: {image.filename}, "
            f"color=({color_r},{color_g},{color_b}), tolerance={tolerance}"
        )

        # Read image
        contents = await image.read()
        pil_image = Image.open(io.BytesIO(contents))

        # Remove color watermark
        clean_image = remove_color_watermark(
            image=pil_image, color=(color_r, color_g, color_b), tolerance=tolerance
        )

        # Convert to bytes
        output = io.BytesIO()
        output_format = "PNG" if image.content_type == "image/png" else "JPEG"
        clean_image.save(output, format=output_format, quality=95)
        output.seek(0)

        logger.info(f"Color watermark removal completed: {image.filename}")

        # Return image
        media_type = f"image/{output_format.lower()}"
        return StreamingResponse(output, media_type=media_type)

    except Exception as e:
        logger.error(f"Color watermark removal error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Color watermark removal failed: {str(e)}",
        )


@router.post("/preprocess-ocr")
async def preprocess_for_ocr_endpoint(
    image: UploadFile = File(..., description="Image to preprocess for OCR"),
    remove_watermark: bool = Form(False, description="Remove watermarks before OCR"),
    watermark_method: str = Form("telea", description="Watermark removal method"),
    enable_deskew: bool = Form(True, description="Correct image rotation"),
    enable_denoise: bool = Form(True, description="Apply denoising"),
    enable_contrast: bool = Form(True, description="Enhance contrast (CLAHE)"),
):
    """
    📄 **Preprocess images for OCR**

    Optimize images for OCR with multi-stage preprocessing pipeline.

    **Pipeline stages**:
    1. **Watermark removal** (optional)
    2. **Deskew**: Correct rotation
    3. **Denoise**: Remove noise
    4. **Contrast enhancement**: CLAHE
    5. **Binarization**: Otsu's method
    6. **Border removal**: Crop margins

    **When to use**:
    - Low-quality scans
    - Rotated documents
    - Images with watermarks
    - Noisy photographs

    **Returns**:
    - Optimized image ready for OCR
    - Typically improves OCR accuracy by 10-30%

    **Cost**: $0/month (100% open-source)
    """
    try:
        logger.info(
            f"OCR preprocessing: {image.filename}, remove_watermark={remove_watermark}"
        )

        # Read image
        contents = await image.read()
        pil_image = Image.open(io.BytesIO(contents))

        # Initialize preprocessor
        preprocessor = ImagePreprocessor(
            enable_denoising=enable_denoise,
            enable_deskew=enable_deskew,
            enable_contrast=enable_contrast,
            enable_watermark_removal=remove_watermark,
            watermark_method=watermark_method,
        )

        # Preprocess
        optimized_image = preprocessor.optimize_for_ocr(pil_image)

        # Convert to bytes
        output = io.BytesIO()
        optimized_image.save(output, format="PNG", quality=95)
        output.seek(0)

        logger.info(f"OCR preprocessing completed: {image.filename}")

        # Return image
        return StreamingResponse(output, media_type="image/png")

    except Exception as e:
        logger.error(f"OCR preprocessing error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"OCR preprocessing failed: {str(e)}"
        )
