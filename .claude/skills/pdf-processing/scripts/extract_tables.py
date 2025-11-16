#!/usr/bin/env python3
"""Extract tables from PDF files"""
import argparse
from pathlib import Path

def extract_pdf_tables(pdf_file: str, output_dir: str):
    """Extract all tables from PDF"""
    try:
        import pdfplumber
        import pandas as pd
    except ImportError:
        print("Error: Install pdfplumber and pandas")
        return

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    with pdfplumber.open(pdf_file) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            tables = page.extract_tables()

            for j, table in enumerate(tables, 1):
                if table:
                    df = pd.DataFrame(table[1:], columns=table[0])
                    output_file = output_path / f"page{i}_table{j}.csv"
                    df.to_csv(output_file, index=False, encoding='utf-8-sig')
                    print(f"✅ Page {i}, Table {j}: {len(df)} rows")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdf', required=True)
    parser.add_argument('--output', default='output')
    args = parser.parse_args()
    extract_pdf_tables(args.pdf, args.output)
