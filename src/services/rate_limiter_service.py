"""
Rate Limiter Service
Redis-based rate limiting with multiple algorithms
Version: v8.5.0
"""

import logging
import os
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
import redis.asyncio as redis
from enum import Enum

logger = logging.getLogger(__name__)


class RateLimitAlgorithm(str, Enum):
    """Rate limiting algorithms"""
    TOKEN_BUCKET = 'token_bucket'
    SLIDING_WINDOW = 'sliding_window'
    FIXED_WINDOW = 'fixed_window'
    LEAKY_BUCKET = 'leaky_bucket'


class RateLimitTier(str, Enum):
    """Rate limit tiers"""
    FREE = 'free'
    BASIC = 'basic'
    PREMIUM = 'premium'
    ENTERPRISE = 'enterprise'


class RateLimiterService:
    """Redis-based rate limiting service"""

    # Rate limit configurations (requests per minute)
    RATE_LIMITS = {
        RateLimitTier.FREE: {
            'requests_per_minute': 10,
            'requests_per_hour': 100,
            'requests_per_day': 1000,
        },
        RateLimitTier.BASIC: {
            'requests_per_minute': 60,
            'requests_per_hour': 1000,
            'requests_per_day': 10000,
        },
        RateLimitTier.PREMIUM: {
            'requests_per_minute': 300,
            'requests_per_hour': 10000,
            'requests_per_day': 100000,
        },
        RateLimitTier.ENTERPRISE: {
            'requests_per_minute': 1000,
            'requests_per_hour': 50000,
            'requests_per_day': 500000,
        },
    }

    def __init__(self, redis_url: str = None):
        """
        Initialize rate limiter service

        Args:
            redis_url: Redis connection URL
        """
        if redis_url is None:
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = os.getenv("REDIS_PORT", "6379")
            redis_url = f"redis://{redis_host}:{redis_port}/1"
        self.redis_url = redis_url
        self.redis_client = None

    async def connect_redis(self):
        """Connect to Redis"""
        if self.redis_client is None:
            try:
                self.redis_client = await redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=False  # Important for binary operations
                )
                logger.info("Connected to Redis for rate limiting")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Closed Redis connection")

    async def check_rate_limit(
        self,
        identifier: str,
        tier: RateLimitTier = RateLimitTier.FREE,
        algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW,
        custom_limit: Optional[int] = None,
        window_seconds: int = 60
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is within rate limit

        Args:
            identifier: Unique identifier (user_id, IP address, API key)
            tier: Rate limit tier
            algorithm: Rate limiting algorithm
            custom_limit: Optional custom limit override
            window_seconds: Time window in seconds

        Returns:
            (allowed, metadata) tuple where:
            - allowed: True if request is allowed
            - metadata: Dict with limit info (current, limit, reset_time, retry_after)
        """
        await self.connect_redis()

        if algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            return await self._sliding_window_check(identifier, tier, custom_limit, window_seconds)
        elif algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            return await self._token_bucket_check(identifier, tier, custom_limit)
        elif algorithm == RateLimitAlgorithm.FIXED_WINDOW:
            return await self._fixed_window_check(identifier, tier, custom_limit, window_seconds)
        elif algorithm == RateLimitAlgorithm.LEAKY_BUCKET:
            return await self._leaky_bucket_check(identifier, tier, custom_limit)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

    async def _sliding_window_check(
        self,
        identifier: str,
        tier: RateLimitTier,
        custom_limit: Optional[int],
        window_seconds: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Sliding window rate limit check

        Uses Redis sorted set with timestamps
        """
        key = f"rate_limit:sliding:{identifier}"
        now = datetime.now().timestamp()
        window_start = now - window_seconds

        # Get limit
        limit = custom_limit or self.RATE_LIMITS[tier]['requests_per_minute']
        if window_seconds == 3600:  # 1 hour
            limit = custom_limit or self.RATE_LIMITS[tier]['requests_per_hour']
        elif window_seconds == 86400:  # 1 day
            limit = custom_limit or self.RATE_LIMITS[tier]['requests_per_day']

        try:
            # Remove old entries
            await self.redis_client.zremrangebyscore(key, 0, window_start)

            # Count current requests
            current = await self.redis_client.zcard(key)

            if current < limit:
                # Add new request
                await self.redis_client.zadd(key, {str(now): now})
                await self.redis_client.expire(key, window_seconds)

                return True, {
                    'allowed': True,
                    'current': current + 1,
                    'limit': limit,
                    'remaining': limit - current - 1,
                    'reset_time': int(now + window_seconds),
                    'retry_after': None,
                }
            else:
                # Rate limit exceeded
                oldest = await self.redis_client.zrange(key, 0, 0, withscores=True)
                if oldest:
                    oldest_timestamp = oldest[0][1]
                    retry_after = int(oldest_timestamp + window_seconds - now)
                else:
                    retry_after = window_seconds

                return False, {
                    'allowed': False,
                    'current': current,
                    'limit': limit,
                    'remaining': 0,
                    'reset_time': int(now + retry_after),
                    'retry_after': retry_after,
                }

        except Exception as e:
            logger.error(f"Sliding window check failed: {e}")
            # Fail open (allow request on error)
            return True, {
                'allowed': True,
                'current': 0,
                'limit': limit,
                'remaining': limit,
                'error': str(e),
            }

    async def _token_bucket_check(
        self,
        identifier: str,
        tier: RateLimitTier,
        custom_limit: Optional[int]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Token bucket rate limit check

        Tokens refill at constant rate
        """
        key = f"rate_limit:token:{identifier}"
        limit = custom_limit or self.RATE_LIMITS[tier]['requests_per_minute']
        refill_rate = limit / 60  # Tokens per second

        try:
            # Get current state
            bucket_data = await self.redis_client.hgetall(key)

            if not bucket_data:
                # Initialize bucket
                tokens = limit - 1
                last_refill = datetime.now().timestamp()
                await self.redis_client.hset(key, mapping={
                    b'tokens': str(tokens).encode(),
                    b'last_refill': str(last_refill).encode(),
                })
                await self.redis_client.expire(key, 120)  # 2 minutes

                return True, {
                    'allowed': True,
                    'current': 1,
                    'limit': limit,
                    'remaining': tokens,
                    'reset_time': int(last_refill + 60),
                }

            # Decode bucket data
            tokens = float(bucket_data[b'tokens'].decode())
            last_refill = float(bucket_data[b'last_refill'].decode())

            # Calculate token refill
            now = datetime.now().timestamp()
            elapsed = now - last_refill
            refilled_tokens = elapsed * refill_rate
            tokens = min(limit, tokens + refilled_tokens)

            if tokens >= 1:
                # Consume token
                tokens -= 1
                await self.redis_client.hset(key, mapping={
                    b'tokens': str(tokens).encode(),
                    b'last_refill': str(now).encode(),
                })
                await self.redis_client.expire(key, 120)

                return True, {
                    'allowed': True,
                    'current': limit - int(tokens),
                    'limit': limit,
                    'remaining': int(tokens),
                    'reset_time': int(now + (1 / refill_rate)),
                }
            else:
                # No tokens available
                retry_after = int((1 - tokens) / refill_rate)

                return False, {
                    'allowed': False,
                    'current': limit,
                    'limit': limit,
                    'remaining': 0,
                    'reset_time': int(now + retry_after),
                    'retry_after': retry_after,
                }

        except Exception as e:
            logger.error(f"Token bucket check failed: {e}")
            return True, {'allowed': True, 'error': str(e)}

    async def _fixed_window_check(
        self,
        identifier: str,
        tier: RateLimitTier,
        custom_limit: Optional[int],
        window_seconds: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Fixed window rate limit check

        Simple counter with fixed time window
        """
        now = datetime.now()
        window_key = int(now.timestamp() / window_seconds)
        key = f"rate_limit:fixed:{identifier}:{window_key}"

        limit = custom_limit or self.RATE_LIMITS[tier]['requests_per_minute']

        try:
            # Increment counter
            current = await self.redis_client.incr(key)

            if current == 1:
                # First request in window, set expiry
                await self.redis_client.expire(key, window_seconds)

            if current <= limit:
                return True, {
                    'allowed': True,
                    'current': current,
                    'limit': limit,
                    'remaining': limit - current,
                    'reset_time': (window_key + 1) * window_seconds,
                }
            else:
                retry_after = ((window_key + 1) * window_seconds) - int(now.timestamp())

                return False, {
                    'allowed': False,
                    'current': current,
                    'limit': limit,
                    'remaining': 0,
                    'reset_time': (window_key + 1) * window_seconds,
                    'retry_after': retry_after,
                }

        except Exception as e:
            logger.error(f"Fixed window check failed: {e}")
            return True, {'allowed': True, 'error': str(e)}

    async def _leaky_bucket_check(
        self,
        identifier: str,
        tier: RateLimitTier,
        custom_limit: Optional[int]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Leaky bucket rate limit check

        Requests leak at constant rate
        """
        key = f"rate_limit:leaky:{identifier}"
        limit = custom_limit or self.RATE_LIMITS[tier]['requests_per_minute']
        leak_rate = limit / 60  # Requests per second

        try:
            bucket_data = await self.redis_client.hgetall(key)

            if not bucket_data:
                # Initialize bucket
                await self.redis_client.hset(key, mapping={
                    b'water': b'1',
                    b'last_leak': str(datetime.now().timestamp()).encode(),
                })
                await self.redis_client.expire(key, 120)

                return True, {
                    'allowed': True,
                    'current': 1,
                    'limit': limit,
                    'remaining': limit - 1,
                }

            # Decode bucket data
            water = float(bucket_data[b'water'].decode())
            last_leak = float(bucket_data[b'last_leak'].decode())

            # Calculate leaked water
            now = datetime.now().timestamp()
            elapsed = now - last_leak
            leaked = elapsed * leak_rate
            water = max(0, water - leaked)

            if water < limit:
                # Add new request
                water += 1
                await self.redis_client.hset(key, mapping={
                    b'water': str(water).encode(),
                    b'last_leak': str(now).encode(),
                })
                await self.redis_client.expire(key, 120)

                return True, {
                    'allowed': True,
                    'current': int(water),
                    'limit': limit,
                    'remaining': limit - int(water),
                }
            else:
                # Bucket full
                retry_after = int((water - limit + 1) / leak_rate)

                return False, {
                    'allowed': False,
                    'current': limit,
                    'limit': limit,
                    'remaining': 0,
                    'retry_after': retry_after,
                }

        except Exception as e:
            logger.error(f"Leaky bucket check failed: {e}")
            return True, {'allowed': True, 'error': str(e)}

    async def reset_limit(self, identifier: str):
        """
        Reset rate limit for identifier

        Args:
            identifier: Unique identifier to reset
        """
        await self.connect_redis()

        try:
            # Delete all rate limit keys for identifier
            patterns = [
                f"rate_limit:sliding:{identifier}",
                f"rate_limit:token:{identifier}",
                f"rate_limit:fixed:{identifier}:*",
                f"rate_limit:leaky:{identifier}",
            ]

            for pattern in patterns:
                if '*' in pattern:
                    keys = await self.redis_client.keys(pattern)
                    if keys:
                        await self.redis_client.delete(*keys)
                else:
                    await self.redis_client.delete(pattern)

            logger.info(f"Reset rate limit for {identifier}")

        except Exception as e:
            logger.error(f"Failed to reset rate limit: {e}")

    async def get_current_usage(self, identifier: str) -> Dict[str, Any]:
        """
        Get current rate limit usage

        Args:
            identifier: Unique identifier

        Returns:
            Usage statistics
        """
        await self.connect_redis()

        usage = {
            'identifier': identifier,
            'sliding_window': 0,
            'token_bucket': 0,
            'fixed_window': 0,
            'leaky_bucket': 0,
        }

        try:
            # Sliding window
            key = f"rate_limit:sliding:{identifier}"
            usage['sliding_window'] = await self.redis_client.zcard(key)

            # Token bucket
            key = f"rate_limit:token:{identifier}"
            bucket_data = await self.redis_client.hgetall(key)
            if bucket_data and b'tokens' in bucket_data:
                limit = self.RATE_LIMITS[RateLimitTier.FREE]['requests_per_minute']
                tokens = float(bucket_data[b'tokens'].decode())
                usage['token_bucket'] = limit - int(tokens)

            # Fixed window (current window)
            now = datetime.now()
            window_key = int(now.timestamp() / 60)
            key = f"rate_limit:fixed:{identifier}:{window_key}"
            current = await self.redis_client.get(key)
            usage['fixed_window'] = int(current) if current else 0

            # Leaky bucket
            key = f"rate_limit:leaky:{identifier}"
            bucket_data = await self.redis_client.hgetall(key)
            if bucket_data and b'water' in bucket_data:
                water = float(bucket_data[b'water'].decode())
                usage['leaky_bucket'] = int(water)

        except Exception as e:
            logger.error(f"Failed to get current usage: {e}")

        return usage


# Singleton instance
_rate_limiter = None


def get_rate_limiter(redis_url: str = None) -> RateLimiterService:
    """Get rate limiter service singleton"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiterService(redis_url)
    return _rate_limiter
