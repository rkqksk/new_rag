"""
Collection Manager for Multi-Collection Routing

Manages multiple Qdrant collections for selective data routing
"""
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any


class CollectionManager:
    """Manages collection registry and routing"""

    def __init__(self, config_path: str = "config/collections.yaml"):
        """
        Initialize collection manager

        Args:
            config_path: Path to collections.yaml
        """
        self.config_path = Path(config_path)
        self.collections = {}
        self.load_registry()

    def load_registry(self):
        """Load collection registry from YAML"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Collection registry not found: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        self.collections = data.get('collections', {})
        self.default_collection = data.get('default_collection', 'products')
        self.active_collections = data.get('active_collections', [])

    def get_collection(self, collection_id: str) -> Optional[Dict[str, Any]]:
        """
        Get collection metadata

        Args:
            collection_id: Collection ID (e.g., 'chungjinkorea')

        Returns:
            Collection metadata dict or None
        """
        return self.collections.get(collection_id)

    def get_collection_name(self, collection_id: str) -> str:
        """
        Get Qdrant collection name

        Args:
            collection_id: Collection ID

        Returns:
            Qdrant collection name
        """
        collection = self.get_collection(collection_id)
        if not collection:
            raise ValueError(f"Collection not found: {collection_id}")

        return collection.get('collection_name', collection_id)

    def list_collections(self, enabled_only: bool = False, embedded_only: bool = False) -> List[Dict[str, Any]]:
        """
        List all collections

        Args:
            enabled_only: Only return enabled collections
            embedded_only: Only return embedded collections

        Returns:
            List of collection metadata
        """
        result = []

        for collection_id, metadata in self.collections.items():
            if enabled_only and not metadata.get('enabled', False):
                continue

            if embedded_only and not metadata.get('embedded', False):
                continue

            result.append({
                'id': collection_id,
                'name': metadata.get('name', ''),
                'description': metadata.get('description', ''),
                'enabled': metadata.get('enabled', False),
                'embedded': metadata.get('embedded', False),
                'total_documents': metadata.get('total_documents', 0),
                'collection_name': metadata.get('collection_name', collection_id),
                'last_updated': metadata.get('last_updated'),
            })

        return result

    def get_active_collections(self) -> List[str]:
        """Get list of active collection IDs"""
        return self.active_collections

    def is_embedded(self, collection_id: str) -> bool:
        """
        Check if collection is embedded

        Args:
            collection_id: Collection ID

        Returns:
            True if embedded, False otherwise
        """
        collection = self.get_collection(collection_id)
        if not collection:
            return False

        return collection.get('embedded', False)

    def validate_collections(self, collection_ids: List[str]) -> List[str]:
        """
        Validate collection IDs and filter to only embedded ones

        Args:
            collection_ids: List of collection IDs to validate

        Returns:
            List of valid, embedded collection IDs
        """
        valid = []

        for collection_id in collection_ids:
            collection = self.get_collection(collection_id)

            if not collection:
                continue

            if not collection.get('enabled', False):
                continue

            if not collection.get('embedded', False):
                continue

            valid.append(collection_id)

        return valid


# Global singleton
_collection_manager = None


def get_collection_manager() -> CollectionManager:
    """Get global collection manager singleton"""
    global _collection_manager

    if _collection_manager is None:
        _collection_manager = CollectionManager()

    return _collection_manager
