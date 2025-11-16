#!/usr/bin/env python3
"""Batch process Excel files"""
import pandas as pd
from pathlib import Path
import argparse

def process_excel_batch(input_dir: str, output_dir: str):
    """Process all Excel files in directory"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    excel_files = list(input_path.glob("*.xlsx")) + list(input_path.glob("*.xls"))

    print(f"Found {len(excel_files)} Excel files")

    for file in excel_files:
        try:
            df = pd.read_excel(file)
            output_file = output_path / f"{file.stem}_processed.csv"
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"✅ {file.name} → {output_file.name}")
        except Exception as e:
            print(f"❌ {file.name}: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    process_excel_batch(args.input, args.output)
