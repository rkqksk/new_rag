"""
Unit Tests: Hierarchical Chunking Service

Tests for Parent-Child chunking implementation (Phase 1, Week 1)

**Test Coverage**:
- Parent chunk creation
- Child chunk creation
- Hierarchical structure validation
- Token count accuracy
- Overlap verification
- Statistics calculation

**Expected Results** (from RAG_ADVANCEMENT_PLAN.md):
- Search precision: 0.88 → 0.92 (+4.5%)
- Context completeness: +30%
- Missing information: -40%

**Version**: v10.5.0
**Created**: 2025-11-17
"""

import pytest
from apps.api.services.hierarchical_chunking_service import (
    HierarchicalChunkingService,
    ParentChunk,
    ChildChunk
)


@pytest.fixture
def service():
    """Create hierarchical chunking service"""
    return HierarchicalChunkingService(
        parent_chunk_size=512,
        child_chunk_size=128
    )


@pytest.fixture
def sample_document():
    """Sample product document"""
    return """
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


class TestHierarchicalChunkingService:
    """Test hierarchical chunking service"""

    def test_initialization(self, service):
        """Test service initialization"""
        assert service.parent_chunk_size == 512
        assert service.child_chunk_size == 128
        assert service.parent_overlap == 50
        assert service.child_overlap == 20

    def test_token_estimation(self, service):
        """Test token count estimation"""
        text = "This is a test sentence."
        tokens = service.estimate_token_count(text)
        assert tokens > 0
        assert tokens == len(text) // 2  # Conservative estimate

    def test_create_parent_chunks(self, service, sample_document):
        """Test parent chunk creation"""
        metadata = {"product_id": "TEST_001"}
        parents = service.create_parent_chunks(sample_document, metadata)

        # Verify parents created
        assert len(parents) > 0

        # Verify each parent
        for parent in parents:
            assert isinstance(parent, ParentChunk)
            assert parent.id
            assert parent.content
            assert parent.token_count > 0
            assert parent.token_count <= service.parent_chunk_size + 100  # Allow some buffer
            assert parent.metadata == metadata
            assert isinstance(parent.child_ids, list)

        # Verify no empty parents
        for parent in parents:
            assert parent.content.strip()

    def test_create_child_chunks(self, service, sample_document):
        """Test child chunk creation"""
        # Create parent first
        metadata = {"product_id": "TEST_001"}
        parents = service.create_parent_chunks(sample_document, metadata)
        assert len(parents) > 0

        parent = parents[0]

        # Create children
        children = service.create_child_chunks(parent)

        # Verify children created
        assert len(children) > 0

        # Verify each child
        for child in children:
            assert isinstance(child, ChildChunk)
            assert child.id
            assert child.content
            assert child.token_count > 0
            assert child.token_count <= service.child_chunk_size + 50  # Allow some buffer
            assert child.parent_id == parent.id
            assert child.metadata == metadata

        # Verify parent knows children
        assert len(parent.child_ids) == len(children)
        for child in children:
            assert child.id in parent.child_ids

    @pytest.mark.asyncio
    async def test_create_hierarchical_chunks(self, service, sample_document):
        """Test complete hierarchical chunk creation"""
        metadata = {"product_id": "TEST_001", "category": "화장품 용기"}

        parents, children = await service.create_hierarchical_chunks(
            sample_document,
            metadata
        )

        # Verify structure
        assert len(parents) > 0
        assert len(children) > 0
        assert len(children) >= len(parents)  # More children than parents

        # Verify linking
        all_child_ids = set()
        for parent in parents:
            all_child_ids.update(parent.child_ids)

        actual_child_ids = {child.id for child in children}
        assert all_child_ids == actual_child_ids

        # Verify metadata propagation
        for parent in parents:
            assert parent.metadata == metadata
        for child in children:
            assert child.metadata == metadata

    def test_statistics(self, service, sample_document):
        """Test statistics calculation"""
        import asyncio

        parents, children = asyncio.run(
            service.create_hierarchical_chunks(sample_document)
        )

        stats = service.get_statistics(parents, children)

        # Verify stats structure
        assert 'total_parents' in stats
        assert 'total_children' in stats
        assert 'avg_children_per_parent' in stats
        assert 'total_parent_tokens' in stats
        assert 'total_child_tokens' in stats
        assert 'avg_parent_tokens' in stats
        assert 'avg_child_tokens' in stats

        # Verify stats values
        assert stats['total_parents'] == len(parents)
        assert stats['total_children'] == len(children)
        assert stats['total_parent_tokens'] > 0
        assert stats['total_child_tokens'] > 0
        assert stats['avg_children_per_parent'] > 0

    @pytest.mark.asyncio
    async def test_empty_document(self, service):
        """Test handling of empty document"""
        parents, children = await service.create_hierarchical_chunks("")

        # Should handle gracefully
        assert len(parents) == 0
        assert len(children) == 0

    @pytest.mark.asyncio
    async def test_short_document(self, service):
        """Test handling of very short document"""
        short_doc = "짧은 문장."

        parents, children = await service.create_hierarchical_chunks(short_doc)

        # Should create at least one parent and child
        assert len(parents) >= 1
        assert len(children) >= 1

    @pytest.mark.asyncio
    async def test_long_document(self, service):
        """Test handling of very long document"""
        # Create long document (repeat sample 10 times)
        long_doc = "\n\n".join([f"Section {i}. " + "문장. " * 200 for i in range(10)])

        parents, children = await service.create_hierarchical_chunks(long_doc)

        # Should create many chunks
        assert len(parents) > 5
        assert len(children) > len(parents)

        # Verify all parents have children
        for parent in parents:
            assert len(parent.child_ids) > 0


@pytest.mark.benchmark
class TestHierarchicalChunkingPerformance:
    """Performance benchmarks for hierarchical chunking"""

    @pytest.mark.asyncio
    async def test_chunking_speed(self, service, sample_document, benchmark):
        """Benchmark chunking speed"""

        async def create_chunks():
            return await service.create_hierarchical_chunks(sample_document)

        # Run benchmark
        import asyncio
        result = benchmark(lambda: asyncio.run(create_chunks()))

        parents, children = result
        assert len(parents) > 0
        assert len(children) > 0

    @pytest.mark.asyncio
    async def test_scalability(self, service):
        """Test scalability with many documents"""
        import time

        documents = [
            f"문서 {i}. " + "문장. " * 100
            for i in range(100)
        ]

        start_time = time.time()

        for doc in documents:
            await service.create_hierarchical_chunks(doc)

        elapsed = time.time() - start_time

        # Should complete in reasonable time
        assert elapsed < 60  # Less than 1 minute for 100 docs
        print(f"\nProcessed 100 documents in {elapsed:.2f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
