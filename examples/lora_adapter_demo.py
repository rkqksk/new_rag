#!/usr/bin/env python3
"""
LORA Adapter Switching Demo

v7.1.0 - Advanced Manufacturing
Demonstrates fast adapter switching for product-specific defect detection

Features:
- <200ms adapter switching
- <50ms inference per image
- Product-specific YOLO models
- Real-time performance metrics
"""

import sys
from pathlib import Path
import time
import numpy as np
import cv2

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.lora_vision_service import get_lora_vision_service


def demo_adapter_switching():
    """Demonstrate adapter switching performance"""
    print("=" * 80)
    print("LORA Adapter Switching Demo")
    print("=" * 80)
    print()

    # Initialize service
    print("Initializing LORA Vision Service...")
    lora_vision = get_lora_vision_service()
    print("✅ Service initialized")
    print()

    # List available adapters
    print("Available LORA Adapters:")
    print("-" * 80)
    adapters = lora_vision.list_adapters()
    for adapter in adapters:
        status = "✅ TRAINED" if adapter["is_trained"] else "⏳ NOT TRAINED"
        active = " (ACTIVE)" if adapter["is_active"] else ""
        print(f"  {adapter['product_type']:15} | {status}{active}")
        print(f"    Classes: {', '.join(adapter['defect_classes'])}")
        if adapter.get("file_size_mb"):
            print(f"    Size: {adapter['file_size_mb']:.2f} MB")
    print()

    # Demo adapter switching
    products = ["pet_bottles", "aluminum_cans", "mold_defects", "pcb_defects"]

    print("Adapter Switching Performance:")
    print("-" * 80)

    switch_times = []
    for product in products:
        start = time.time()
        result = lora_vision.switch_adapter(product)
        switch_time = (time.time() - start) * 1000

        switch_times.append(switch_time)

        status = "✅" if result["switched"] else "⏭️"
        print(f"  {product:15} | {status} {switch_time:.1f}ms")

    print()
    print(f"Average switch time: {np.mean(switch_times):.1f}ms")
    print(f"Max switch time: {np.max(switch_times):.1f}ms")
    print()


def demo_inspection():
    """Demonstrate defect inspection"""
    print("=" * 80)
    print("Defect Inspection Demo")
    print("=" * 80)
    print()

    lora_vision = get_lora_vision_service()

    # Create synthetic test image (640x640 gray)
    print("Creating test image (640x640)...")
    test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)

    # Draw some synthetic "defects"
    cv2.rectangle(test_image, (100, 100), (200, 200), (0, 0, 255), 3)
    cv2.circle(test_image, (400, 400), 50, (0, 255, 0), -1)
    print("✅ Test image created with synthetic defects")
    print()

    # Inspect with different adapters
    products = ["pet_bottles", "aluminum_cans"]

    for product in products:
        print(f"Inspecting with adapter: {product}")
        print("-" * 80)

        result = lora_vision.inspect(test_image, product_type=product)

        print(f"  Timestamp: {result['timestamp']}")
        print(f"  Product: {result['product_type']}")
        print(f"  Defects found: {result['defect_count']}")
        print(f"  Inference time: {result['inference_time_ms']:.2f}ms")
        print(f"  Total time: {result['total_time_ms']:.2f}ms")
        print(f"  LORA adapter: {result['lora_adapter']}")

        if result['defects']:
            print("  Detected defects:")
            for i, defect in enumerate(result['defects'], 1):
                print(f"    {i}. {defect['defect_type']} "
                      f"(confidence: {defect['confidence']:.2f})")
        else:
            print("  No defects detected (using base model without training)")

        print()


def demo_metrics():
    """Demonstrate performance metrics"""
    print("=" * 80)
    print("Performance Metrics")
    print("=" * 80)
    print()

    lora_vision = get_lora_vision_service()

    metrics = lora_vision.get_metrics()

    print(f"Total inspections: {metrics['total_inspections']}")
    print(f"Total defects detected: {metrics['total_defects']}")
    print(f"Average inference time: {metrics['avg_inference_ms']:.2f}ms")
    print(f"Adapter switches: {metrics['adapter_switches']}")
    print(f"Current product: {metrics['current_product']}")
    print(f"Available adapters: {len(metrics['available_adapters'])}")
    print(f"Adapters trained: {metrics['adapters_trained']}/{len(metrics['available_adapters'])}")
    print()


def main():
    """Run all demos"""
    try:
        # Demo 1: Adapter switching
        demo_adapter_switching()

        # Demo 2: Defect inspection
        demo_inspection()

        # Demo 3: Performance metrics
        demo_metrics()

        print("=" * 80)
        print("✅ Demo Complete!")
        print("=" * 80)
        print()
        print("Next steps:")
        print("1. Collect/generate training images (500+ per product)")
        print("2. Annotate images with YOLO format")
        print("3. Train LORA adapters:")
        print("   python scripts/train_lora_adapter.py --product pet_bottles --epochs 50")
        print("4. Test trained adapters with real images")
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
