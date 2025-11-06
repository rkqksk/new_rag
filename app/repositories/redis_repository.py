"""Redis Repository for Caching"""
import redis.asyncio as redis
import json
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)

class RedisRepository:
    """
    Redis cache repository
    
    Features:
    - Get/Set with TTL
    - JSON serialization
    - Batch operations
    - Cache invalidation
    """
    
    def __init__(
        self,
        host: str,
        port: int,
        db: int = 0,
        password: Optional[str] = None,
        max_connections: int = 50
    ):
        """Initialize Redis client"""
        self.pool = redis.ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            max_connections=max_connections,
            decode_responses=True
        )
        self.client = redis.Redis(connection_pool=self.pool)
        logger.info(f"✅ RedisRepository connected to {host}:{port}")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600
    ) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds
        
        Returns:
            Success status
        """
        try:
            serialized = json.dumps(value)
            await self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        try:
            return await self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis increment error: {e}")
            return 0
    
    async def get_many(self, keys: list) -> dict:
        """Get multiple keys"""
        try:
            values = await self.client.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value:
                    result[key] = json.loads(value)
            return result
        except Exception as e:
            logger.error(f"Redis get_many error: {e}")
            return {}
    
    async def flush_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        try:
            keys = []
            async for key in self.client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis flush_pattern error: {e}")
            return 0
    
    async def close(self):
        """Close connection"""
        await self.client.close()
        await self.pool.disconnect()
