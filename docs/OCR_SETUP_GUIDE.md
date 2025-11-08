# OCR Setup Guide - PaddleOCR Configuration

**Complete setup guide for PaddleOCR-based OCR pipeline**

---

## Table of Contents

1. [Overview](#overview)
2. [PaddleOCR Version](#paddleocr-version)
3. [Installation](#installation)
4. [GPU Support](#gpu-support)
5. [Model Download](#model-download)
6. [Configuration](#configuration)
7. [Verification](#verification)
8. [Troubleshooting](#troubleshooting)

---

## Overview

### OCR Stack

```
Primary Engine: PaddleOCR v2.7.0.3 (Latest Stable)
Fallback #1: EasyOCR v1.7.0
Fallback #2: Tesseract 5.x

Models:
- PP-OCRv4 (Detection + Recognition)
- Korean + English language packs
```

**Note**: When PaddleOCR v3.3.1 is released, this guide will be updated with migration instructions.

---

## PaddleOCR Version

### Current Version: 2.7.0.3

**Why this version**:
- ✅ Latest stable release (as of 2024)
- ✅ PP-OCRv4 support
- ✅ Korean language optimizations
- ✅ Production-ready
- ✅ Well-documented

**Roadmap**:
- **Current**: v2.7.0.3 (PP-OCRv4)
- **Target**: v3.3.1 (when released)

### Checking for Updates

```bash
# Check installed version
pip show paddleocr

# Check latest version
pip index versions paddleocr

# Monitor releases
# https://github.com/PaddlePaddle/PaddleOCR/releases
```

### Migration to v3.3.1 (When Available)

When v3.3.1 is released:

```bash
# 1. Backup current setup
pip freeze > requirements-backup.txt

# 2. Upgrade
pip install paddleocr==3.3.1

# 3. Test
python3 scripts/test_ocr.py

# 4. If issues, rollback
pip install paddleocr==2.7.0.3
```

---

## Installation

### Method 1: Using requirements.txt (Recommended)

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Install all dependencies
pip install -r requirements.txt

# Includes:
# paddleocr==2.7.0.3
# paddlepaddle==2.5.2  # CPU version
# easyocr==1.7.0
# pytesseract==0.3.10
# opencv-python==4.8.1.78
# pillow==10.1.0
```

### Method 2: Manual Installation

```bash
# CPU version
pip install paddlepaddle==2.5.2 paddleocr==2.7.0.3

# GPU version (CUDA 11.7)
pip install paddlepaddle-gpu==2.5.2 paddleocr==2.7.0.3
```

### Method 3: From Source (Advanced)

```bash
# Clone PaddleOCR repository
git clone https://github.com/PaddlePaddle/PaddleOCR.git
cd PaddleOCR

# Checkout specific version
git checkout v2.7.0.3

# Install
pip install -e .
```

---

## GPU Support

### Check GPU Availability

```bash
# Check CUDA
nvidia-smi

# Check PaddlePaddle GPU
python3 -c "import paddle; print(paddle.device.cuda.device_count())"
# Output: 1 (if GPU available)
```

### Install GPU Version

**CUDA 11.7**:
```bash
pip install paddlepaddle-gpu==2.5.2 -f https://www.paddlepaddle.org.cn/whl/linux/mkl/avx/stable.html
```

**CUDA 12.0**:
```bash
pip install paddlepaddle-gpu==2.5.2.post120 -f https://www.paddlepaddle.org.cn/whl/linux/mkl/avx/stable.html
```

**Apple Silicon (M1/M2)**:
```bash
# PaddlePaddle doesn't officially support MPS yet
# Use CPU version
pip install paddlepaddle==2.5.2
```

### Configure GPU Usage

```python
# src/core/ocr_processors/ocr_config.py

import os

OCR_CONFIG = {
    # Auto-detect GPU
    "use_gpu": os.getenv("OCR_USE_GPU", "true").lower() == "true",

    # GPU ID (if multiple GPUs)
    "gpu_id": int(os.getenv("OCR_GPU_ID", "0")),

    # GPU memory limit (MB)
    "gpu_mem": int(os.getenv("OCR_GPU_MEM", "4000")),
}
```

---

## Model Download

### Automatic Download (Recommended)

PaddleOCR automatically downloads models on first use:

```python
from paddleocr import PaddleOCR

# This will download models to ~/.paddleocr/
ocr = PaddleOCR(lang='korean')

# Models downloaded:
# - Detection: en_PP-OCRv4_det
# - Recognition: korean_PP-OCRv4_rec
# - Angle classifier: ch_ppocr_mobile_v2.0_cls
```

**Model Location**: `~/.paddleocr/whl/`

**Model Sizes**:
- Detection model: ~3MB
- Korean recognition model: ~12MB
- Angle classifier: ~2MB
- **Total**: ~17MB

### Manual Download

If automatic download fails:

```bash
# 1. Create model directory
mkdir -p ~/.paddleocr/whl/det/en/
mkdir -p ~/.paddleocr/whl/rec/korean/
mkdir -p ~/.paddleocr/whl/cls/

# 2. Download models
cd ~/.paddleocr/whl/det/en/
wget https://paddleocr.bj.bcebos.com/PP-OCRv4/english/en_PP-OCRv4_det_infer.tar
tar -xf en_PP-OCRv4_det_infer.tar

cd ~/.paddleocr/whl/rec/korean/
wget https://paddleocr.bj.bcebos.com/PP-OCRv4/korean/korean_PP-OCRv4_rec_infer.tar
tar -xf korean_PP-OCRv4_rec_infer.tar

cd ~/.paddleocr/whl/cls/
wget https://paddleocr.bj.bcebos.com/dygraph_v2.0/ch/ch_ppocr_mobile_v2.0_cls_infer.tar
tar -xf ch_ppocr_mobile_v2.0_cls_infer.tar
```

### Custom Models

To use custom trained models:

```python
from paddleocr import PaddleOCR

ocr = PaddleOCR(
    det_model_dir='/path/to/custom_det_model',
    rec_model_dir='/path/to/custom_rec_model',
    cls_model_dir='/path/to/custom_cls_model',
    use_angle_cls=True,
    lang='korean'
)
```

---

## Configuration

### Environment Variables

```bash
# .env

# OCR Engine Selection
OCR_USE_GPU=true
OCR_GPU_ID=0
OCR_GPU_MEM=4000

# PaddleOCR Configuration
PADDLE_OCR_LANG=korean
PADDLE_OCR_USE_ANGLE_CLS=true
PADDLE_OCR_DET_ALGORITHM=DB++
PADDLE_OCR_REC_ALGORITHM=SVTR_LCNet

# Confidence Thresholds
OCR_PADDLE_THRESHOLD=0.75
OCR_EASY_THRESHOLD=0.70

# Model Paths (optional)
PADDLE_DET_MODEL_DIR=
PADDLE_REC_MODEL_DIR=
PADDLE_CLS_MODEL_DIR=

# Performance
OCR_MAX_BATCH_SIZE=8
OCR_USE_MULTIPROCESS=false
```

### Python Configuration

```python
# src/core/ocr_processors/ocr_config.py

from pydantic_settings import BaseSettings

class OCRSettings(BaseSettings):
    """OCR configuration"""

    # GPU
    use_gpu: bool = True
    gpu_id: int = 0
    gpu_mem: int = 4000

    # PaddleOCR
    paddle_lang: str = "korean"
    paddle_use_angle_cls: bool = True
    paddle_det_algorithm: str = "DB++"
    paddle_rec_algorithm: str = "SVTR_LCNet"

    # Thresholds
    paddle_threshold: float = 0.75
    easy_threshold: float = 0.70

    # Models
    paddle_det_model_dir: str = ""
    paddle_rec_model_dir: str = ""
    paddle_cls_model_dir: str = ""

    # Performance
    max_batch_size: int = 8
    use_multiprocess: bool = False

    class Config:
        env_file = ".env"
        env_prefix = "OCR_"

settings = OCRSettings()
```

### Initialize PaddleOCR

```python
# src/core/ocr_processors/paddle_ocr_wrapper.py

from paddleocr import PaddleOCR
from .ocr_config import settings

def get_paddleocr():
    """Get configured PaddleOCR instance"""

    config = {
        "lang": settings.paddle_lang,
        "use_angle_cls": settings.paddle_use_angle_cls,
        "use_gpu": settings.use_gpu,
        "show_log": False
    }

    # Custom models (if specified)
    if settings.paddle_det_model_dir:
        config["det_model_dir"] = settings.paddle_det_model_dir
    if settings.paddle_rec_model_dir:
        config["rec_model_dir"] = settings.paddle_rec_model_dir
    if settings.paddle_cls_model_dir:
        config["cls_model_dir"] = settings.paddle_cls_model_dir

    return PaddleOCR(**config)

# Singleton instance
_paddle_ocr = None

def get_ocr_instance():
    """Get singleton OCR instance"""
    global _paddle_ocr
    if _paddle_ocr is None:
        _paddle_ocr = get_paddleocr()
    return _paddle_ocr
```

---

## Verification

### Test Script

```python
# scripts/test_ocr.py

from paddleocr import PaddleOCR
import time

def test_paddleocr():
    """Test PaddleOCR installation"""

    print("Testing PaddleOCR v2.7.0.3...")
    print("-" * 50)

    # 1. Check version
    import paddleocr
    print(f"PaddleOCR version: {paddleocr.__version__}")

    # 2. Check GPU
    import paddle
    print(f"GPU available: {paddle.device.cuda.device_count() > 0}")

    # 3. Initialize OCR
    print("\nInitializing OCR...")
    start = time.time()
    ocr = PaddleOCR(lang='korean', use_angle_cls=True, use_gpu=True)
    init_time = time.time() - start
    print(f"Initialization time: {init_time:.2f}s")

    # 4. Test with sample image
    print("\nTesting OCR on sample image...")

    # Create test image with Korean text
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new('RGB', (800, 200), color='white')
    draw = ImageDraw.Draw(img)

    # Draw test text
    text = "50ml PET 투명 용기 테스트"
    draw.text((50, 50), text, fill='black')

    # Save
    img.save('/tmp/test_ocr.png')

    # Run OCR
    start = time.time()
    result = ocr.ocr('/tmp/test_ocr.png', cls=True)
    ocr_time = time.time() - start

    print(f"OCR time: {ocr_time:.3f}s")

    # Print results
    print("\nResults:")
    for line in result[0]:
        text = line[1][0]
        confidence = line[1][1]
        print(f"  Text: {text}")
        print(f"  Confidence: {confidence:.2f}")

    print("\n" + "="*50)
    print("✅ PaddleOCR test completed successfully!")

if __name__ == "__main__":
    test_paddleocr()
```

**Run test**:
```bash
python3 scripts/test_ocr.py
```

**Expected output**:
```
Testing PaddleOCR v2.7.0.3...
--------------------------------------------------
PaddleOCR version: 2.7.0.3
GPU available: True

Initializing OCR...
Initialization time: 1.23s

Testing OCR on sample image...
OCR time: 0.342s

Results:
  Text: 50ml PET 투명 용기 테스트
  Confidence: 0.94

==================================================
✅ PaddleOCR test completed successfully!
```

---

## Troubleshooting

### Issue 1: ImportError: libgomp.so.1

**Error**: `OSError: libgomp.so.1: cannot open shared object file`

**Solution** (Ubuntu/Debian):
```bash
sudo apt-get install libgomp1
```

**Solution** (CentOS/RHEL):
```bash
sudo yum install libgomp
```

---

### Issue 2: CUDA Out of Memory

**Error**: `CUDA out of memory`

**Solution 1**: Reduce GPU memory limit
```bash
export OCR_GPU_MEM=2000  # Reduce from 4000 to 2000
```

**Solution 2**: Use CPU
```bash
export OCR_USE_GPU=false
```

**Solution 3**: Process images in smaller batches
```python
# Process one at a time
for image in images:
    result = ocr.ocr(image)
```

---

### Issue 3: Slow Initialization

**Problem**: First OCR call takes 2-3 seconds

**Explanation**: Model loading happens on first use

**Solution**: Pre-warm on startup
```python
# src/api/app.py

@app.on_event("startup")
async def startup_event():
    """Pre-load OCR models"""
    from src.core.ocr_processors.paddle_ocr_wrapper import get_ocr_instance

    logger.info("Pre-loading OCR models...")
    ocr = get_ocr_instance()
    logger.info("OCR models loaded")
```

---

### Issue 4: Low Accuracy for Korean Text

**Solutions**:

1. **Use Korean language pack**:
```python
ocr = PaddleOCR(lang='korean')  # Not 'en'
```

2. **Enable preprocessing**:
```python
from src.core.ocr_processors.image_preprocessor import ImagePreprocessor

preprocessor = ImagePreprocessor()
optimized_path = preprocessor.optimize_for_ocr(image_path)
result = ocr.ocr(optimized_path)
```

3. **Adjust confidence threshold**:
```python
# Lower threshold if getting too few results
OCR_PADDLE_THRESHOLD=0.60  # From 0.75
```

---

### Issue 5: Model Download Fails

**Error**: `URLError` or timeout during model download

**Solution 1**: Manual download (see [Model Download](#model-download))

**Solution 2**: Use mirror
```bash
# China mirror
export PADDLEOCR_URL=https://paddleocr.bj.bcebos.com

# International mirror
export PADDLEOCR_URL=https://github.com/PaddlePaddle/PaddleOCR/releases/download
```

---

## Best Practices

### 1. Production Deployment

```python
# Use singleton pattern
ocr_instance = get_ocr_instance()

# Pre-load on startup
@app.on_event("startup")
async def load_models():
    get_ocr_instance()
```

### 2. Error Handling

```python
try:
    result = ocr.ocr(image_path)
except Exception as e:
    logger.error(f"PaddleOCR failed: {e}")
    # Fallback to EasyOCR
    result = easyocr_fallback(image_path)
```

### 3. Performance Optimization

```python
# Batch processing
images = [img1, img2, img3]
results = [ocr.ocr(img) for img in images]

# Async processing
async def process_images(images):
    tasks = [asyncio.to_thread(ocr.ocr, img) for img in images]
    return await asyncio.gather(*tasks)
```

---

## References

- [PaddleOCR GitHub](https://github.com/PaddlePaddle/PaddleOCR)
- [PaddleOCR Documentation](https://paddlepaddle.github.io/PaddleOCR/)
- [PP-OCRv4 Paper](https://arxiv.org/abs/2203.03916)
- [PaddlePaddle Installation](https://www.paddlepaddle.org.cn/install/quick)

---

**Last Updated**: 2025-11-08
**Version**: 1.0.0 (PaddleOCR 2.7.0.3)
