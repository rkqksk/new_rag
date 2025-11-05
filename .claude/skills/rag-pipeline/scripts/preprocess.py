#!/usr/bin/env python3
"""
Preprocess crawled data for RAG embedding

Usage:
    python preprocess.py --input data/crawled/onehago/crawled/production/packaging_unique_for_images.jsonl \
                        --output data/crawled/onehago/crawled/production/packaging_enhanced.jsonl \
                        --data-type onehago
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from preprocessors import get_preprocessor


def main():
    parser = argparse.ArgumentParser(description='Preprocess crawled data for RAG embedding')

    parser.add_argument(
        '--input',
        type=Path,
        required=True,
        help='Input JSONL file (raw crawled data)'
    )

    parser.add_argument(
        '--output',
        type=Path,
        required=True,
        help='Output JSONL file (enhanced data)'
    )

    parser.add_argument(
        '--data-type',
        type=str,
        required=True,
        choices=['onehago', 'chungjinkorea'],
        help='Type of data to preprocess'
    )

    parser.add_argument(
        '--images-root',
        type=Path,
        help='Custom images root directory (optional)'
    )

    parser.add_argument(
        '--stats-file',
        type=Path,
        help='Output file for preprocessing statistics (optional)'
    )

    args = parser.parse_args()

    # Validate input file exists
    if not args.input.exists():
        print(f"❌ Error: Input file not found: {args.input}")
        sys.exit(1)

    # Create output directory if needed
    args.output.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("RAG Pipeline - Data Preprocessing")
    print("=" * 80)
    print(f"\n📂 Input:  {args.input}")
    print(f"📂 Output: {args.output}")
    print(f"📦 Type:   {args.data_type}")

    # Get preprocessor
    try:
        if args.images_root:
            print(f"📁 Images: {args.images_root}")
            # For onehago, pass images_root
            from preprocessors.onehago import OnehagoPreprocessor
            preprocessor = OnehagoPreprocessor(images_root=args.images_root)
        else:
            preprocessor = get_preprocessor(args.data_type)

        print(f"\n✅ Loaded {args.data_type} preprocessor")

    except ValueError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

    # Process data
    try:
        print("\n" + "=" * 80)
        print("Starting preprocessing...")
        print("=" * 80)

        processed_data = preprocessor.process(args.input)

        print("\n" + "=" * 80)
        print("Saving results...")
        print("=" * 80)

        # Save processed data
        processed_data.save(args.output)
        print(f"\n✅ Saved {len(processed_data)} products to {args.output}")

        # Save statistics
        if args.stats_file:
            import json
            stats = {
                'input_file': str(args.input),
                'output_file': str(args.output),
                'data_type': args.data_type,
                'total_products': len(processed_data),
                'steps_applied': processed_data.steps_applied,
                'statistics': processed_data.stats
            }

            with open(args.stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)

            print(f"✅ Saved statistics to {args.stats_file}")

        # Print summary
        print("\n" + "=" * 80)
        print("Preprocessing Complete!")
        print("=" * 80)
        print(f"\n📊 Summary:")
        print(f"   Total products: {len(processed_data)}")
        print(f"   Steps applied: {', '.join(processed_data.steps_applied)}")
        print(f"\n📈 Statistics:")
        for key, value in processed_data.stats.items():
            percentage = (value / len(processed_data) * 100) if len(processed_data) > 0 else 0
            print(f"   {key}: {value} ({percentage:.1f}%)")

        print("\n✅ Ready for embedding!")

    except Exception as e:
        print(f"\n❌ Error during preprocessing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
