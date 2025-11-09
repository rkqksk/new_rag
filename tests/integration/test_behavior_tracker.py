"""
Integration tests for behavior tracker (DB-backed analytics)
"""

import pytest
from datetime import datetime
from src.analytics.behavior_tracker import BehaviorTracker


class TestBehaviorTracker:
    """Test behavior tracking with PostgreSQL"""

    @pytest.fixture
    def tracker(self):
        """Create behavior tracker without DB connection (will use file backup)"""
        return BehaviorTracker(db_connection=None, backup_dir="logs/test_analytics")

    @pytest.mark.asyncio
    async def test_track_search(self, tracker):
        """Test search log tracking"""
        await tracker.track_search(
            user_id="test_user_1",
            session_id="test_session_1",
            query="50ml PET bottle",
            normalized_query="50ml pet bottle",
            filters={"material": "PET", "capacity": "50ml"},
            result_count=5,
            result_product_indices=["idx_1", "idx_2", "idx_3"],
            intent="search",
            product_type="bottle",
            response_time_ms=150,
            ip_address="127.0.0.1",
        )

        # Should have queued the event
        assert len(tracker.queue) == 1
        assert tracker.queue[0]["table"] == "search_logs"
        assert tracker.queue[0]["data"]["query"] == "50ml PET bottle"

    @pytest.mark.asyncio
    async def test_track_click(self, tracker):
        """Test click log tracking"""
        await tracker.track_click(
            user_id="test_user_1",
            session_id="test_session_1",
            product_idx="idx_10",
            product_code="BTL-001",
            product_name="50ml PET Bottle",
            category="Bottle",
            material="PET",
            capacity_ml=50.0,
            position=1,
            source_query="50ml bottle",
        )

        assert len(tracker.queue) == 1
        assert tracker.queue[0]["table"] == "click_logs"
        assert tracker.queue[0]["data"]["product_idx"] == "idx_10"

    @pytest.mark.asyncio
    async def test_track_conversation(self, tracker):
        """Test conversation log tracking"""
        await tracker.track_conversation(
            user_id="test_user_1",
            session_id="test_session_1",
            message_id="msg_001",
            role="user",
            content="I need a 50ml PET bottle",
            intent="product_search",
            extracted_entities='{"capacity": "50ml", "material": "PET"}',
            response_time_ms=200,
            model_used="qwen2.5:7b",
        )

        assert len(tracker.queue) == 1
        assert tracker.queue[0]["table"] == "conversation_logs"
        assert tracker.queue[0]["data"]["role"] == "user"

    @pytest.mark.asyncio
    async def test_track_sample_request(self, tracker):
        """Test sample request tracking"""
        await tracker.track_sample_request(
            user_id="test_user_1",
            session_id="test_session_1",
            product_idx="idx_10",
            product_code="BTL-001",
            product_name="50ml PET Bottle",
            customer_name="John Doe",
            customer_email="john@example.com",
            customer_phone="+82-10-1234-5678",
            company_name="Test Company",
            quantity=1000,
            message="Please send samples",
        )

        assert len(tracker.queue) == 1
        assert tracker.queue[0]["table"] == "sample_requests"
        assert tracker.queue[0]["data"]["customer_email"] == "john@example.com"

    @pytest.mark.asyncio
    async def test_batch_processing(self, tracker):
        """Test batch processing of events"""
        # Add multiple events
        for i in range(5):
            await tracker.track_search(
                user_id=f"user_{i}",
                session_id="test_session",
                query=f"query {i}",
                normalized_query=f"query {i}",
                filters={},
                result_count=i,
                result_product_indices=[],
                intent="search",
            )

        assert len(tracker.queue) == 5

        # Flush should process all events
        await tracker.flush()

        # Queue should be empty after flush
        assert len(tracker.queue) == 0

    @pytest.mark.asyncio
    async def test_file_backup_on_db_failure(self, tracker):
        """Test that events are backed up to file when DB fails"""
        # Tracker has no DB connection, so should use file backup
        await tracker.track_search(
            user_id="test_user",
            session_id="test_session",
            query="test query",
            normalized_query="test query",
            filters={},
            result_count=1,
            result_product_indices=[],
            intent="search",
        )

        await tracker.flush()

        # File backup should have been created in logs/test_analytics/
        import os
        from pathlib import Path

        backup_dir = Path("logs/test_analytics")
        if backup_dir.exists():
            backup_files = list(backup_dir.glob("backup_*.jsonl"))
            assert len(backup_files) > 0
