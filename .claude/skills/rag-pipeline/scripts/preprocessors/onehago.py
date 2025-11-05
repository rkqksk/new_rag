"""
Onehago-specific data preprocessor

Handles:
- Linking local images from packaging folder
- Parsing specifications (capacity, neck_size, materials)
- Cleaning material strings
- Extracting capacity from product names
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Any
from .base import BasePreprocessor, ProcessedData


class OnehagoPreprocessor(BasePreprocessor):
    """
    Preprocessor for Onehago data

    Transforms raw crawled data into RAG-ready format:
    - Links images from data/crawled/onehago/images/packaging/
    - Parses specifications from product fields
    - Cleans and normalizes material strings
    - Extracts structured capacity information
    """

    def __init__(self, images_root: Path = None):
        super().__init__()

        # Default images root
        if images_root is None:
            project_root = Path(__file__).parents[5]  # Up to rag-enterprise/
            images_root = project_root / 'data' / 'crawled' / 'onehago' / 'images' / 'packaging'

        self.images_root = images_root

        # Material mapping
        self.material_mapping = {
            'OTHER': '기타',
            'PP': 'PP',
            'PET': 'PET',
            'PE': 'PE',
            'HDPE': 'HDPE',
            'LDPE': 'LDPE',
            'PS': 'PS',
            'ABS': 'ABS',
            'PVC': 'PVC',
            'PC': 'PC',
            'PETG': 'PETG',
            'AS': 'AS',
            'PMMA': 'PMMA',
            'SAN': 'SAN',
            'GLASS': '유리',
            'ALUMINUM': '알루미늄'
        }

        # Capacity extraction patterns
        self.capacity_patterns = [
            r'(\d+(?:\.\d+)?)\s*ml',
            r'(\d+(?:\.\d+)?)\s*ML',
            r'(\d+(?:\.\d+)?)\s*cc',
            r'(\d+(?:\.\d+)?)\s*CC',
            r'(\d+(?:\.\d+)?)\s*g',
            r'(\d+(?:\.\d+)?)\s*G',
        ]

        # Neck size extraction pattern (supports ×, x, X, Ø, ø symbols)
        self.neck_size_pattern = r'Neck\s*[×xXØø]\s*(\d+)'

    def process(self, input_file: Path) -> ProcessedData:
        """
        Process Onehago raw data

        Steps:
        1. Load raw JSONL
        2. Link local images
        3. Parse specifications
        4. Clean materials
        5. Extract capacity
        6. Collect statistics

        Args:
            input_file: Path to raw JSONL (e.g., packaging_unique_for_images.jsonl)

        Returns:
            ProcessedData with enhanced products
        """
        print(f"\n📦 Processing Onehago data: {input_file.name}")
        print(f"📁 Images root: {self.images_root}")

        # Step 1: Load raw data
        print("\n1️⃣ Loading raw data...")
        products = self.load_jsonl(input_file)
        print(f"   ✅ Loaded {len(products)} products")
        self.steps_applied.append('load_jsonl')

        # Step 2: Link images
        print("\n2️⃣ Linking local images...")
        products = self.link_images(products)
        linked_count = sum(1 for p in products if p.get('has_local_images'))
        print(f"   ✅ Linked images for {linked_count} products ({linked_count/len(products)*100:.1f}%)")
        self.steps_applied.append('link_images')

        # Step 3: Parse specifications
        print("\n3️⃣ Parsing specifications...")
        products = self.parse_specifications(products)
        parsed_count = sum(1 for p in products if p.get('specifications_parsed'))
        print(f"   ✅ Parsed specs for {parsed_count} products")
        self.steps_applied.append('parse_specifications')

        # Step 4: Clean materials
        print("\n4️⃣ Cleaning materials...")
        products = self.clean_materials(products)
        material_count = sum(1 for p in products
                           if p.get('specifications_parsed', {}).get('materials'))
        print(f"   ✅ Cleaned materials for {material_count} products")
        self.steps_applied.append('clean_materials')

        # Step 5: Extract capacity
        print("\n5️⃣ Extracting capacity...")
        products = self.extract_capacity(products)
        capacity_count = sum(1 for p in products
                           if p.get('specifications_parsed', {}).get('capacity'))
        print(f"   ✅ Extracted capacity for {capacity_count} products")
        self.steps_applied.append('extract_capacity')

        # Step 6: Collect statistics
        print("\n6️⃣ Collecting statistics...")
        stats = self.collect_stats(products)
        self.stats = stats

        print("\n✅ Preprocessing complete!")
        print(f"\n📊 Statistics:")
        for key, value in stats.items():
            print(f"   {key}: {value}")

        return ProcessedData(
            products=products,
            steps_applied=self.steps_applied.copy(),
            stats=stats
        )

    def link_images(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Link local images to products

        Scans data/crawled/onehago/images/packaging/{product_id}/
        for images and metadata.json

        Adds fields:
        - has_local_images: bool
        - local_images: List[dict] with index, filename, paths, type, size
        - image_metadata: dict with total_available, downloaded, downloaded_at
        """
        for product in products:
            product_id = str(product.get('product_id', ''))

            if not product_id:
                product['has_local_images'] = False
                product['local_images'] = []
                continue

            # Check if image folder exists
            image_folder = self.images_root / product_id

            if not image_folder.exists():
                product['has_local_images'] = False
                product['local_images'] = []
                continue

            # Read metadata.json
            metadata_file = image_folder / 'metadata.json'
            image_metadata = {}

            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        image_metadata = {
                            'total_available': metadata.get('total_images_available'),
                            'downloaded': metadata.get('images_downloaded'),
                            'downloaded_at': metadata.get('downloaded_at')
                        }
                except Exception as e:
                    print(f"   ⚠️ Failed to read metadata for product {product_id}: {e}")

            # List all images
            images = sorted(image_folder.glob('img_*.jpg'))

            if not images:
                product['has_local_images'] = False
                product['local_images'] = []
                continue

            # Create image entries
            local_images = []
            for i, img in enumerate(images):
                local_images.append({
                    'index': i + 1,
                    'filename': img.name,
                    'local_path': str(img),
                    'relative_path': f'images/packaging/{product_id}/{img.name}',
                    'type': 'product' if i == 0 else 'detail',
                    'file_size_kb': img.stat().st_size // 1024
                })

            product['has_local_images'] = True
            product['local_images'] = local_images
            product['image_metadata'] = image_metadata

        return products

    def parse_specifications(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Parse specifications from product fields

        Extracts:
        - neck_size: From "용량" field (e.g., "Neck×20" → 20)
        - capacity: From product_name (handled by extract_capacity)
        - materials: From "재질" field (handled by clean_materials)
        - moq: Convert to integer

        Creates specifications_parsed field with structured data
        """
        for product in products:
            specs = {}

            # Get specifications dict (nested under product['specifications'])
            specifications = product.get('specifications', {})

            # Extract neck size from "용량" field
            capacity_field = specifications.get('용량', '')
            if capacity_field and isinstance(capacity_field, str):
                match = re.search(self.neck_size_pattern, capacity_field, re.IGNORECASE)
                if match:
                    try:
                        specs['neck_size'] = int(match.group(1))
                    except ValueError:
                        pass

            # Get material (will be cleaned in clean_materials step)
            material_field = specifications.get('재질', '')
            if material_field:
                specs['material_raw'] = material_field

            # Parse MOQ
            moq_field = specifications.get('MOQ', '') or specifications.get('최소수량', '')
            if moq_field:
                try:
                    # Remove commas and convert to int
                    moq_str = str(moq_field).replace(',', '').strip()
                    if moq_str.isdigit():
                        specs['moq'] = int(moq_str)
                except (ValueError, AttributeError):
                    pass

            # Mark as parsed
            product['specifications_parsed'] = specs

        return products

    def clean_materials(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean and normalize material strings

        Transforms:
        - "PP,OTHER," → ["PP", "기타"]
        - "PET" → ["PET"]
        - Empty/None → []

        Uses material_mapping for Korean translations
        """
        for product in products:
            specs = product.get('specifications_parsed', {})
            material_raw = specs.get('material_raw', '')

            if not material_raw:
                specs['materials'] = []
                continue

            # Split by comma and clean
            materials_list = []
            for mat in material_raw.split(','):
                mat = mat.strip().upper()
                if mat:
                    # Map to Korean if available
                    cleaned = self.material_mapping.get(mat, mat)
                    materials_list.append(cleaned)

            # Remove duplicates while preserving order
            seen = set()
            unique_materials = []
            for mat in materials_list:
                if mat not in seen:
                    seen.add(mat)
                    unique_materials.append(mat)

            specs['materials'] = unique_materials
            product['specifications_parsed'] = specs

        return products

    def extract_capacity(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract capacity from product name

        Patterns:
        - "50ml PET 병" → 50 ml
        - "100cc 용기" → 100 cc
        - "30g 크림용기" → 30 g

        Stores in specifications_parsed['capacity'] as dict:
        {'value': 50, 'unit': 'ml'}
        """
        for product in products:
            specs = product.get('specifications_parsed', {})
            product_name = product.get('product_name', '')

            if not product_name:
                continue

            # Try each pattern
            for pattern in self.capacity_patterns:
                match = re.search(pattern, product_name, re.IGNORECASE)
                if match:
                    try:
                        value = float(match.group(1))
                        # Extract unit from pattern
                        unit = re.search(r'(ml|ML|cc|CC|g|G)', match.group(0))
                        if unit:
                            unit_str = unit.group(1).lower()
                            specs['capacity'] = {
                                'value': value,
                                'unit': unit_str
                            }
                            break
                    except (ValueError, IndexError):
                        continue

            product['specifications_parsed'] = specs

        return products
