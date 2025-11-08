"""
Usage Tracker Service

Track API usage, enforce quotas, and manage rate limiting for SaaS platform.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

import redis

from src.models.saas_models import PLAN_LIMITS, PlanTier, QuotaUsage, Tenant, UsageLog

logger = logging.getLogger(__name__)


class UsageTracker:
    """
    Track and enforce usage limits

    Features:
    - API call tracking (Redis + PostgreSQL)
    - Quota enforcement (per plan tier)
    - Rate limiting (per minute)
    - Usage analytics
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """
        Initialize usage tracker

        Args:
            redis_url: Redis connection URL
        """
        self.redis = redis.from_url(redis_url, decode_responses=True)

    def track_api_call(
        self,
        tenant_id: str,
        endpoint: str,
        method: str = "GET",
        status_code: int = 200,
        response_time_ms: float = 0,
        user_id: Optional[str] = None,
        api_key_id: Optional[str] = None,
    ):
        """
        Track API call

        Stores in both Redis (fast, temporary) and PostgreSQL (permanent)

        Args:
            tenant_id: Tenant UUID
            endpoint: API endpoint path
            method: HTTP method
            status_code: Response status code
            response_time_ms: Response time in milliseconds
            user_id: User ID (if JWT auth)
            api_key_id: API key ID (if API key auth)
        """
        # 1. Increment Redis counters
        today = datetime.utcnow().date().isoformat()
        month = datetime.utcnow().strftime("%Y-%m")

        # Daily counter
        daily_key = f"usage:{tenant_id}:{today}:api_calls"
        self.redis.incr(daily_key)
        self.redis.expire(daily_key, 86400 * 31)  # Keep for 31 days

        # Monthly counter
        monthly_key = f"usage:{tenant_id}:{month}:api_calls"
        self.redis.incr(monthly_key)
        self.redis.expire(monthly_key, 86400 * 365)  # Keep for 1 year

        # Endpoint-specific counter
        endpoint_key = f"usage:{tenant_id}:{today}:endpoint:{endpoint}"
        self.redis.incr(endpoint_key)
        self.redis.expire(endpoint_key, 86400 * 7)  # Keep for 7 days

        # 2. Store in PostgreSQL for long-term analytics
        from src.db.session import SessionLocal

        db = SessionLocal()
        try:
            usage_log = UsageLog(
                tenant_id=tenant_id,
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                response_time_ms=response_time_ms,
                user_id=user_id,
                api_key_id=api_key_id,
                timestamp=datetime.utcnow(),
            )
            db.add(usage_log)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log usage to PostgreSQL: {e}")
        finally:
            db.close()

        # 3. Update daily quota usage (aggregated)
        self._update_quota_usage(tenant_id)

    def check_quota(self, tenant_id: str) -> Dict:
        """
        Check if tenant is within quota

        Args:
            tenant_id: Tenant UUID

        Returns:
            dict with quota status
        """
        from src.db.session import SessionLocal

        db = SessionLocal()
        try:
            # Get tenant and plan
            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if not tenant:
                return {"within_quota": False, "error": "Tenant not found"}

            plan_tier = tenant.plan_tier

            # Get plan limits
            max_calls = PLAN_LIMITS[plan_tier]["max_api_calls_per_month"]

            # Unlimited plan
            if max_calls == -1:
                return {
                    "within_quota": True,
                    "current_usage": 0,
                    "quota_limit": -1,
                    "usage_percentage": 0,
                }

            # Get current usage
            month = datetime.utcnow().strftime("%Y-%m")
            monthly_key = f"usage:{tenant_id}:{month}:api_calls"
            current_usage = int(self.redis.get(monthly_key) or 0)

            # Check quota
            within_quota = current_usage < max_calls

            return {
                "within_quota": within_quota,
                "current_usage": current_usage,
                "quota_limit": max_calls,
                "usage_percentage": (current_usage / max_calls * 100) if max_calls > 0 else 0,
                "remaining": max_calls - current_usage,
            }

        finally:
            db.close()

    def check_rate_limit(self, tenant_id: str) -> Dict:
        """
        Check rate limit (requests per minute)

        Args:
            tenant_id: Tenant UUID

        Returns:
            dict with rate limit status
        """
        from src.db.session import SessionLocal

        db = SessionLocal()
        try:
            # Get tenant plan
            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if not tenant:
                return {"allowed": False, "error": "Tenant not found"}

            plan_tier = tenant.plan_tier

            # Get rate limit for plan
            max_per_minute = PLAN_LIMITS[plan_tier]["rate_limit_per_minute"]

            # Sliding window rate limiting
            import time

            now = int(time.time())
            window = 60  # 1 minute

            key = f"rate_limit:{tenant_id}:{now // window}"

            # Increment counter
            count = self.redis.incr(key)
            if count == 1:
                self.redis.expire(key, window)

            # Check limit
            allowed = count <= max_per_minute

            return {
                "allowed": allowed,
                "current_count": count,
                "limit": max_per_minute,
                "remaining": max(0, max_per_minute - count),
                "reset_at": (now // window + 1) * window,  # Unix timestamp
            }

        finally:
            db.close()

    def get_usage_stats(
        self,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict:
        """
        Get usage statistics for tenant

        Args:
            tenant_id: Tenant UUID
            start_date: Start date (defaults to 30 days ago)
            end_date: End date (defaults to today)

        Returns:
            Usage statistics
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        from src.db.session import SessionLocal

        db = SessionLocal()
        try:
            # Get usage logs from PostgreSQL
            logs = (
                db.query(UsageLog)
                .filter(
                    UsageLog.tenant_id == tenant_id,
                    UsageLog.timestamp >= start_date,
                    UsageLog.timestamp <= end_date,
                )
                .all()
            )

            # Calculate statistics
            total_calls = len(logs)
            successful_calls = len([l for l in logs if l.status_code < 400])
            failed_calls = total_calls - successful_calls

            avg_response_time = (
                sum(l.response_time_ms for l in logs) / total_calls if total_calls > 0 else 0
            )

            # Endpoint breakdown
            endpoint_counts = {}
            for log in logs:
                endpoint_counts[log.endpoint] = endpoint_counts.get(log.endpoint, 0) + 1

            # Daily breakdown
            daily_counts = {}
            for log in logs:
                day = log.timestamp.date().isoformat()
                daily_counts[day] = daily_counts.get(day, 0) + 1

            return {
                "total_calls": total_calls,
                "successful_calls": successful_calls,
                "failed_calls": failed_calls,
                "success_rate": (successful_calls / total_calls * 100) if total_calls > 0 else 0,
                "avg_response_time_ms": avg_response_time,
                "endpoint_breakdown": endpoint_counts,
                "daily_breakdown": daily_counts,
                "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            }

        finally:
            db.close()

    def _update_quota_usage(self, tenant_id: str):
        """Update aggregated quota usage in database"""
        from src.db.session import SessionLocal

        db = SessionLocal()
        try:
            today = datetime.utcnow()
            year = today.year
            month = today.month
            day = today.day

            # Get or create quota record
            quota = (
                db.query(QuotaUsage)
                .filter(
                    QuotaUsage.tenant_id == tenant_id,
                    QuotaUsage.year == year,
                    QuotaUsage.month == month,
                    QuotaUsage.day == day,
                )
                .first()
            )

            if not quota:
                quota = QuotaUsage(
                    tenant_id=tenant_id,
                    year=year,
                    month=month,
                    day=day,
                    api_calls=0,
                    storage_bytes=0,
                    vector_count=0,
                )
                db.add(quota)

            # Increment API calls
            quota.api_calls += 1
            quota.updated_at = datetime.utcnow()

            db.commit()

        except Exception as e:
            logger.error(f"Failed to update quota usage: {e}")
            db.rollback()
        finally:
            db.close()

    def reset_monthly_usage(self, tenant_id: str):
        """
        Reset monthly usage counters (called at start of month)

        Args:
            tenant_id: Tenant UUID
        """
        # Archive current month's data
        month = datetime.utcnow().strftime("%Y-%m")
        monthly_key = f"usage:{tenant_id}:{month}:api_calls"

        current_usage = int(self.redis.get(monthly_key) or 0)

        # Log reset
        logger.info(f"Resetting usage for tenant {tenant_id}: {current_usage} API calls last month")

        # Delete Redis key (will auto-create on next API call)
        # Note: We don't actually delete - let it expire naturally
        # This allows for overlap period at month boundaries


# Convenience singleton
usage_tracker = UsageTracker()
