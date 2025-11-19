"""
Hierarchical Chunking Service - Phase 1 Implementation

Implements Parent-Child chunking strategy for improved context quality.

**Strategy**:
- Parent chunks: 512 tokens (full context for answer generation)
- Child chunks: 128 tokens (searchable units for precision)
- Overlap: 50 tokens (parent), 20 tokens (child)

**Expected Results** (from RAG_ADVANCEMENT_PLAN.md):
- Search precision: 0.88 → 0.92 (+4.5%)
- Context completeness: +30%
- Missing information: -40%

**Usage**:
```python
from apps.api.services.hierarchical_chunking_service import HierarchicalChunkingService

service = HierarchicalChunkingService()

# Create hierarchical chunks
parents, children = await service.create_hierarchical_chunks(document)

# Store in Qdrant
await service.store_in_qdrant(parents, children)

# Retrieve with parent context
results = await service.retrieve_with_parent_context(query, top_k=5)
```

**Version**: v10.5.0
**Created**: 2025-11-17
**Status**: Phase 1 Implementation
"""

import re
import uuid
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from loguru import logger

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    logger.warning("Qdrant not available, chunking service will run in limited mode")


@dataclass
class Chunk:
    """Base chunk data structure"""
    id: str
    content: str
    token_count: int
    start_pos: int
    end_pos: int
    metadata: Dict = field(default_factory=dict)


@dataclass
class ParentChunk(Chunk):
    """Parent chunk (512 tokens, full context)"""
    child_ids: List[str] = field(default_factory=list)


@dataclass
class ChildChunk(Chunk):
    """Child chunk (128 tokens, searchable)"""
    parent_id: str = ""


class HierarchicalChunkingService:
    """
    Hierarchical chunking service with parent-child relationships

    **Architecture**:
    1. Parent chunks (512 tokens): Full context for answer generation
    2. Child chunks (128 tokens): Precise searchable units
    3. Linking: Each child knows its parent, parent knows all children

    **Workflow**:
    1. Create parent chunks from document
    2. Create child chunks from each parent
    3. Link children to parent
    4. Store in separate Qdrant collections
    5. Search in children, retrieve parents for context
    """

    def __init__(
        self,
        parent_chunk_size: int = 512,
        parent_overlap: int = 50,
        child_chunk_size: int = 128,
        child_overlap: int = 20,
        qdrant_client: Optional[QdrantClient] = None,
        qdrant_url: str = "http://localhost:6333"
    ):
        """
        Initialize hierarchical chunking service

        Args:
            parent_chunk_size: Target size for parent chunks (tokens)
            parent_overlap: Overlap between parent chunks (tokens)
            child_chunk_size: Target size for child chunks (tokens)
            child_overlap: Overlap between child chunks (tokens)
            qdrant_client: Optional Qdrant client instance
            qdrant_url: Qdrant server URL
        """
        self.parent_chunk_size = parent_chunk_size
        self.parent_overlap = parent_overlap
        self.child_chunk_size = child_chunk_size
        self.child_overlap = child_overlap

        # Qdrant client
        if qdrant_client:
            self.qdrant_client = qdrant_client
        elif QDRANT_AVAILABLE:
            self.qdrant_client = QdrantClient(url=qdrant_url)
        else:
            self.qdrant_client = None
            logger.warning("Qdrant client not initialized")

        logger.info(
            f"HierarchicalChunkingService initialized: "
            f"parent={parent_chunk_size}tok, child={child_chunk_size}tok"
        )

    def estimate_token_count(self, text: str) -> int:
        """
        Estimate token count (rough approximation)

        Rule of thumb: 1 token ≈ 4 characters for English
        For Korean/mixed: 1 token ≈ 2-3 characters
        """
        # Use conservative estimate (2.5 chars per token)
        return len(text) // 2

    def create_parent_chunks(
        self,
        text: str,
        metadata: Optional[Dict] = None
    ) -> List[ParentChunk]:
        """
        Create parent chunks (512 tokens, overlapping)

        Strategy:
        1. Split by sentences
        2. Group sentences until reaching chunk_size
        3. Add overlap from previous chunk

        Args:
            text: Input text
            metadata: Optional metadata to attach to chunks

        Returns:
            List of parent chunks
        """
        # Split into sentences
        sentences = re.split(r'(?<=[.?!。？！])\s+', text)

        parent_chunks = []
        current_text = ""
        current_tokens = 0
        overlap_text = ""
        start_pos = 0

        for sentence in sentences:
            sentence_tokens = self.estimate_token_count(sentence)

            # Check if adding sentence exceeds chunk size
            if current_tokens + sentence_tokens > self.parent_chunk_size:
                if current_text.strip():
                    # Create parent chunk
                    chunk_id = str(uuid.uuid4())
                    parent_chunk = ParentChunk(
                        id=chunk_id,
                        content=current_text.strip(),
                        token_count=current_tokens,
                        start_pos=start_pos,
                        end_pos=start_pos + len(current_text),
                        metadata=metadata or {},
                        child_ids=[]
                    )
                    parent_chunks.append(parent_chunk)

                    # Calculate overlap for next chunk
                    words = current_text.split()
                    overlap_words = words[-self.parent_overlap:] if self.parent_overlap else []
                    overlap_text = " ".join(overlap_words)

                    # Start new chunk with overlap
                    start_pos += len(current_text) - len(overlap_text)
                    current_text = overlap_text + " " + sentence
                    current_tokens = self.estimate_token_count(current_text)
                else:
                    # First sentence
                    current_text = sentence
                    current_tokens = sentence_tokens
            else:
                current_text += " " + sentence
                current_tokens += sentence_tokens

        # Add final chunk
        if current_text.strip():
            chunk_id = str(uuid.uuid4())
            parent_chunk = ParentChunk(
                id=chunk_id,
                content=current_text.strip(),
                token_count=current_tokens,
                start_pos=start_pos,
                end_pos=start_pos + len(current_text),
                metadata=metadata or {},
                child_ids=[]
            )
            parent_chunks.append(parent_chunk)

        logger.info(f"Created {len(parent_chunks)} parent chunks")
        return parent_chunks

    def create_child_chunks(
        self,
        parent: ParentChunk
    ) -> List[ChildChunk]:
        """
        Create child chunks from a parent chunk (128 tokens each)

        Strategy:
        1. Split parent content by sentences
        2. Group sentences until reaching child_chunk_size
        3. Add overlap between children
        4. Link each child to parent

        Args:
            parent: Parent chunk to split

        Returns:
            List of child chunks
        """
        # Split parent content into sentences
        sentences = re.split(r'(?<=[.?!。？！])\s+', parent.content)

        child_chunks = []
        current_text = ""
        current_tokens = 0
        overlap_text = ""
        child_start_pos = parent.start_pos

        for sentence in sentences:
            sentence_tokens = self.estimate_token_count(sentence)

            # Check if adding sentence exceeds child chunk size
            if current_tokens + sentence_tokens > self.child_chunk_size:
                if current_text.strip():
                    # Create child chunk
                    chunk_id = str(uuid.uuid4())
                    child_chunk = ChildChunk(
                        id=chunk_id,
                        content=current_text.strip(),
                        token_count=current_tokens,
                        start_pos=child_start_pos,
                        end_pos=child_start_pos + len(current_text),
                        metadata=parent.metadata.copy(),
                        parent_id=parent.id
                    )
                    child_chunks.append(child_chunk)

                    # Add child ID to parent
                    parent.child_ids.append(chunk_id)

                    # Calculate overlap for next child
                    words = current_text.split()
                    overlap_words = words[-self.child_overlap:] if self.child_overlap else []
                    overlap_text = " ".join(overlap_words)

                    # Start new child with overlap
                    child_start_pos += len(current_text) - len(overlap_text)
                    current_text = overlap_text + " " + sentence
                    current_tokens = self.estimate_token_count(current_text)
                else:
                    # First sentence
                    current_text = sentence
                    current_tokens = sentence_tokens
            else:
                current_text += " " + sentence
                current_tokens += sentence_tokens

        # Add final child chunk
        if current_text.strip():
            chunk_id = str(uuid.uuid4())
            child_chunk = ChildChunk(
                id=chunk_id,
                content=current_text.strip(),
                token_count=current_tokens,
                start_pos=child_start_pos,
                end_pos=child_start_pos + len(current_text),
                metadata=parent.metadata.copy(),
                parent_id=parent.id
            )
            child_chunks.append(child_chunk)
            parent.child_ids.append(chunk_id)

        logger.debug(f"Created {len(child_chunks)} children for parent {parent.id[:8]}")
        return child_chunks

    async def create_hierarchical_chunks(
        self,
        document: str,
        metadata: Optional[Dict] = None
    ) -> Tuple[List[ParentChunk], List[ChildChunk]]:
        """
        Create complete hierarchical chunk structure

        Workflow:
        1. Create parent chunks (512 tokens each)
        2. For each parent, create child chunks (128 tokens each)
        3. Link children to parents

        Args:
            document: Input document text
            metadata: Optional metadata for all chunks

        Returns:
            Tuple of (parent_chunks, child_chunks)
        """
        logger.info(f"Creating hierarchical chunks for document ({len(document)} chars)")

        # Step 1: Create parent chunks
        parent_chunks = self.create_parent_chunks(document, metadata)

        # Step 2: Create child chunks for each parent
        all_child_chunks = []
        for parent in parent_chunks:
            child_chunks = self.create_child_chunks(parent)
            all_child_chunks.extend(child_chunks)

        logger.info(
            f"Hierarchical chunking complete: "
            f"{len(parent_chunks)} parents, {len(all_child_chunks)} children"
        )

        return parent_chunks, all_child_chunks

    async def store_in_qdrant(
        self,
        parent_chunks: List[ParentChunk],
        child_chunks: List[ChildChunk],
        collection_prefix: str = "hierarchical"
    ):
        """
        Store hierarchical chunks in Qdrant collections

        Collections:
        - {prefix}_parents: Parent chunks (512 tokens)
        - {prefix}_children: Child chunks (128 tokens)

        Args:
            parent_chunks: List of parent chunks
            child_chunks: List of child chunks
            collection_prefix: Prefix for collection names
        """
        if not self.qdrant_client:
            logger.error("Qdrant client not available")
            return

        parent_collection = f"{collection_prefix}_parents"
        child_collection = f"{collection_prefix}_children"

        logger.info(
            f"Storing hierarchical chunks: "
            f"{len(parent_chunks)} parents → {parent_collection}, "
            f"{len(child_chunks)} children → {child_collection}"
        )

        # TODO: Implement Qdrant storage
        # This requires embedding generation which should be done by a separate service
        # For now, just log the intent
        logger.warning("Qdrant storage not yet implemented - needs embedding service integration")

    async def retrieve_with_parent_context(
        self,
        query: str,
        top_k: int = 5,
        collection_prefix: str = "hierarchical"
    ) -> List[Dict]:
        """
        Retrieve with parent context (core innovation)

        Workflow:
        1. Search in child collection (precise matching)
        2. Get parent IDs from child results
        3. Retrieve full parent chunks (rich context)
        4. Return parent content for answer generation

        Args:
            query: Search query
            top_k: Number of results
            collection_prefix: Collection name prefix

        Returns:
            List of parent chunks with full context
        """
        if not self.qdrant_client:
            logger.error("Qdrant client not available")
            return []

        child_collection = f"{collection_prefix}_children"
        parent_collection = f"{collection_prefix}_parents"

        logger.info(f"Searching children for: {query}")

        # TODO: Implement retrieval
        # This requires:
        # 1. Query embedding generation
        # 2. Vector search in child collection
        # 3. Parent chunk retrieval by ID
        logger.warning("Retrieval not yet implemented - needs embedding service integration")

        return []

    def get_statistics(
        self,
        parent_chunks: List[ParentChunk],
        child_chunks: List[ChildChunk]
    ) -> Dict:
        """
        Get statistics about hierarchical chunks

        Returns:
            Dictionary with chunk statistics
        """
        total_parent_tokens = sum(p.token_count for p in parent_chunks)
        total_child_tokens = sum(c.token_count for c in child_chunks)
        avg_children_per_parent = len(child_chunks) / len(parent_chunks) if parent_chunks else 0

        stats = {
            "total_parents": len(parent_chunks),
            "total_children": len(child_chunks),
            "avg_children_per_parent": round(avg_children_per_parent, 2),
            "total_parent_tokens": total_parent_tokens,
            "total_child_tokens": total_child_tokens,
            "avg_parent_tokens": round(total_parent_tokens / len(parent_chunks), 2) if parent_chunks else 0,
            "avg_child_tokens": round(total_child_tokens / len(child_chunks), 2) if child_chunks else 0,
            "parent_chunk_size": self.parent_chunk_size,
            "child_chunk_size": self.child_chunk_size,
        }

        return stats


# Example usage
if __name__ == "__main__":
    import asyncio

    async def main():
        # Sample product document
        document = """
        제품명: 50ml PET 투명 보틀

        용량: 50ml
        재질: PET (폴리에틸렌 테레프탈레이트)
        색상: 투명
        용도: 화장품, 샴플, 토너, 에센스

        상세 스펙:
        - 높이: 120mm
        - 직경: 35mm
        - 무게: 15g
        - 목 규격: 20/410

        가격 정보:
        - 단가: 800원
        - MOQ: 1000개
        - 1000-5000개: 750원
        - 5000개 이상: 700원

        제품 특징:
        - 투명도가 높아 내용물 확인 용이
        - 가볍고 깨지지 않아 안전
        - 재활용 가능한 친환경 소재
        - 다양한 캡과 호환 가능
        """

        # Initialize service
        service = HierarchicalChunkingService(
            parent_chunk_size=512,
            child_chunk_size=128
        )

        # Create hierarchical chunks
        parents, children = await service.create_hierarchical_chunks(
            document,
            metadata={"product_id": "PET_50ML_001", "category": "화장품 용기"}
        )

        # Print statistics
        stats = service.get_statistics(parents, children)
        print("\n=== Hierarchical Chunking Statistics ===")
        for key, value in stats.items():
            print(f"{key}: {value}")

        # Print sample chunks
        print("\n=== Sample Parent Chunk ===")
        if parents:
            parent = parents[0]
            print(f"ID: {parent.id}")
            print(f"Content: {parent.content[:200]}...")
            print(f"Token count: {parent.token_count}")
            print(f"Children: {len(parent.child_ids)}")

        print("\n=== Sample Child Chunks ===")
        for i, child in enumerate(children[:3]):
            print(f"\nChild {i+1}:")
            print(f"ID: {child.id}")
            print(f"Parent ID: {child.parent_id}")
            print(f"Content: {child.content[:100]}...")
            print(f"Token count: {child.token_count}")

    asyncio.run(main())
