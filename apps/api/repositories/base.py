"""Base Repository Pattern"""

from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Base repository interface"""

    @abstractmethod
    async def get(self, id: str) -> Optional[T]:
        """Get entity by ID"""
        pass

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create entity"""
        pass

    @abstractmethod
    async def update(self, id: str, entity: T) -> T:
        """Update entity"""
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete entity"""
        pass
