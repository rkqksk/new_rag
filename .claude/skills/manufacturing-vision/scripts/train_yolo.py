#!/usr/bin/env python3
"""
Train YOLO model for defect detection
"""
import argparse
from pathlib import Path

def train_yolo(
    data_yaml: str,
    model: str = "yolov8n",
    epochs: int = 100,
    imgsz: int = 640,
    batch: int = 16,
    device: str = "0"
):
    """
    Train YOLO model for manufacturing defect detection
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        print("Error: ultralytics not installed")
        print("Run: pip install ultralytics")
        return

    print("=" * 60)
    print(f"Training YOLO Model: {model}")
    print("=" * 60)
    print(f"Data: {data_yaml}")
    print(f"Epochs: {epochs}")
    print(f"Image size: {imgsz}")
    print(f"Batch size: {batch}")
    print(f"Device: {device}")
    print()

    # Load model
    model = YOLO(f"{model}.pt")

    # Train
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=device,
        project="runs/detect",
        name="defect_detection",
        exist_ok=True,
        # Augmentation
        augment=True,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=10,
        translate=0.1,
        scale=0.5,
        shear=2.0,
        flipud=0.5,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.1,
        # Optimization
        optimizer='AdamW',
        lr0=0.001,
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3.0,
        patience=50,
        # Logging
        save=True,
        save_period=10,
        plots=True,
        verbose=True
    )

    print()
    print("=" * 60)
    print("Training Complete!")
    print("=" * 60)
    print(f"Best model: runs/detect/defect_detection/weights/best.pt")
    print(f"Last model: runs/detect/defect_detection/weights/last.pt")
    print(f"mAP50: {results.results_dict['metrics/mAP50(B)']:.3f}")
    print(f"mAP50-95: {results.results_dict['metrics/mAP50-95(B)']:.3f}")

    # Validate
    print()
    print("Running validation...")
    val_results = model.val()

    print()
    print("Next steps:")
    print("1. python scripts/evaluate_model.py --model runs/detect/defect_detection/weights/best.pt")
    print("2. python scripts/export_onnx.py --model runs/detect/defect_detection/weights/best.pt")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Train YOLO defect detection")
    parser.add_argument('--data', required=True, help='Path to data.yaml')
    parser.add_argument('--model', default='yolov8n', help='Model size (n/s/m/l/x)')
    parser.add_argument('--epochs', type=int, default=100)
    parser.add_argument('--imgsz', type=int, default=640)
    parser.add_argument('--batch', type=int, default=16)
    parser.add_argument('--device', default='0', help='CUDA device')

    args = parser.parse_args()

    train_yolo(
        data_yaml=args.data,
        model=args.model,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device
    )
