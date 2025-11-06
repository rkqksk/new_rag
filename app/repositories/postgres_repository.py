"""Postgres Repository for Analytics Data"""
from typing import List, Dict, Any, Optional
import asyncpg
import logging

logger = logging.getLogger(__name__)

class PostgresRepository:
    """
    PostgreSQL repository for analytics
    
    Features:
    - Connection pooling
    - Analytics queries
    - Batch inserts
    """
    
    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
        pool_size: int = 20
    ):
        """Initialize Postgres connection"""
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.pool_size = pool_size
        self.pool = None
    
    async def connect(self):
        """Create connection pool"""
        if self.pool is None:
            self.pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.username,
                password=self.password,
                min_size=5,
                max_size=self.pool_size
            )
            logger.info(f"✅ PostgresRepository connected to {self.host}:{self.port}")
    
    async def execute(self, query: str, *args) -> str:
        """Execute query"""
        await self.connect()
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
        """Fetch multiple rows"""
        await self.connect()
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]
    
    async def fetchrow(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Fetch single row"""
        await self.connect()
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None
    
    async def insert_search_event(
        self,
        session_id: str,
        query: str,
        keywords: List[str],
        results_count: int
    ) -> bool:
        """Insert search event"""
        try:
            await self.execute(
                """
                INSERT INTO search_events (session_id, query, parsed_keywords, results_count)
                VALUES ($1, $2, $3, $4)
                """,
                session_id,
                query,
                json.dumps(keywords),
                results_count
            )
            return True
        except Exception as e:
            logger.error(f"Insert search event error: {e}")
            return False
    
    async def insert_product_event(
        self,
        session_id: str,
        product_id: str,
        event_type: str,
        product_data: Dict[str, Any]
    ) -> bool:
        """Insert product event"""
        try:
            await self.execute(
                """
                INSERT INTO product_events 
                (session_id, product_id, event_type, product_category, product_name)
                VALUES ($1, $2, $3, $4, $5)
                """,
                session_id,
                product_id,
                event_type,
                product_data.get("category"),
                product_data.get("name")
            )
            return True
        except Exception as e:
            logger.error(f"Insert product event error: {e}")
            return False
    
    async def get_top_keywords(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get top keywords"""
        try:
            return await self.fetch(
                """
                SELECT keyword, search_count 
                FROM keyword_stats 
                ORDER BY search_count DESC 
                LIMIT $1
                """,
                limit
            )
        except Exception as e:
            logger.error(f"Get top keywords error: {e}")
            return []
    
    async def get_top_products(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get top products"""
        try:
            return await self.fetch(
                """
                SELECT product_id, name, category, click_count, view_count
                FROM product_stats 
                ORDER BY click_count DESC 
                LIMIT $1
                """,
                limit
            )
        except Exception as e:
            logger.error(f"Get top products error: {e}")
            return []
    
    async def close(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
