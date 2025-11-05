"""
Base preprocessor for data transformation
"""

from pathlib import Path
from typing import List, Dict, Any
import json
from dataclasses import dataclass, field


@dataclass
class ProcessedData:
    """Container for processed data"""
    products: List[Dict[str, Any]]
    steps_applied: List[str] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)

    def __len__(self):
        return len(self.products)

    def save(self, output_file: Path):
        """Save processed data to JSONL"""
        with open(output_file, 'w', encoding='utf-8') as f:
            for product in self.products:
                f.write(json.dumps(product, ensure_ascii=False) + '\n')


class BasePreprocessor:
    """
    Base class for data preprocessing

    Subclasses should implement process() method and
    any site-specific preprocessing logic
    """

    def __init__(self):
        self.steps_applied = []
        self.stats = {}

    def process(self, input_file: Path) -> ProcessedData:
        """
        Process raw data

        Args:
            input_file: Path to raw JSONL file

        Returns:
            ProcessedData with transformed products
        """
        raise NotImplementedError("Subclasses must implement process()")

    def load_jsonl(self, input_file: Path) -> List[Dict[str, Any]]:
        """Load products from JSONL file"""
        products = []
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    products.append(json.loads(line))
        return products

    def link_images(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Link local images to products - override in subclass"""
        return products

    def parse_specifications(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse specifications - override in subclass"""
        return products

    def clean_materials(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean material strings - override in subclass"""
        return products

    def extract_capacity(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract capacity from product name - override in subclass"""
        return products

    def collect_stats(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Collect statistics about processed data"""
        stats = {
            'total_products': len(products),
            'products_with_images': sum(1 for p in products if p.get('has_local_images')),
            'products_with_parsed_specs': sum(1 for p in products if p.get('specifications_parsed')),
            'products_with_capacity': sum(1 for p in products
                                        if p.get('specifications_parsed', {}).get('capacity')),
            'products_with_neck_size': sum(1 for p in products
                                         if p.get('specifications_parsed', {}).get('neck_size')),
        }
        return stats
