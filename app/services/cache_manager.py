```python
# app/services/cache_manager.py
"""
Phase 3 분산 캐싱 시스템
L1(인메모리) → L2(Redis) → L3(Disk) 계층 캐시 관리
"""

import asyncio
import json
import logging
import pickle
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from functools import wraps

import aioredis
import aiofiles

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """캐시 항목"""
    key: str
    value: Any
    created_at: float = field(default_factory=time.time)
    ttl: Optional[int] = None  # 초 단위
    size: int = 0
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)

    def is_expired(self) -> bool:
        """TTL 만료 여부 확인"""
        if self.ttl is None:
            return False
        elapsed = time.time() - self.created_at
        return elapsed > self.ttl

    def update_access(self) -> None:
        """접근 시간 업데이트"""
        self.last_accessed = time.time()
        self.access_count += 1


@dataclass
class CacheStats:
    """캐시 통계"""
    l1_hits: int = 0
    l2_hits: int = 0
    l3_hits: int = 0
    misses: int = 0
    total_requests: int = 0
    l1_size: int = 0
    l2_size: int = 0
    l3_size: int = 0
    evictions: int = 0

    @property
    def hit_rate(self) -> float:
        """히트율 계산"""
        if self.total_requests == 0:
            return 0.0
        hits = self.l1_hits + self.l2_hits + self.l3_hits
        return (hits / self.total_requests) * 100

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "l1_hits": self.l1_hits,
            "l2_hits": self.l2_hits,
            "l3_hits": self.l3_hits,
            "misses": self.misses,
            "total_requests": self.total_requests,
            "hit_rate": f"{self.hit_rate:.2f}%",
            "l1_size_mb": f"{self.l1_size / 1024 / 1024:.2f}",
            "l2_size_mb": f"{self.l2_size / 1024 / 1024:.2f}",
            "l3_size_mb": f"{self.l3_size / 1024 / 1024:.2f}",
            "evictions": self.evictions,
        }


class CacheManager:
    """계층 캐시 관리자"""

    def __init__(
        self,
        redis_url: str = "redis://localhost",
        disk_path: str = "./cache",
        l1_max_size: int = 100 * 1024 * 1024,  # 100MB
        l1_max_items: int = 10000,
        ttl_default: int = 3600,  # 1시간
    ):
        """
        초기화

        Args:
            redis_url: Redis 연결 URL
            disk_path: 디스크 캐시 경로
            l1_max_size: L1 최대 크기 (바이트)
            l1_max_items: L1 최대 항목 수
            ttl_default: 기본 TTL (초)
        """
        self.redis_url = redis_url
        self.disk_path = Path(disk_path)
        self.l1_max_size = l1_max_size
        self.l1_max_items = l1_max_items
        self.ttl_default = ttl_default

        # L1 캐시 (인메모리, LRU)
        self.l1_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.l1_lock = asyncio.Lock()

        # L2 캐시 (Redis)
        self.redis: Optional[aioredis.Redis] = None
        self.redis_available = False

        # 통계
        self.stats = CacheStats()
        self.stats_lock = asyncio.Lock()

        # 디스크 캐시 초기화
        self.disk_path.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"CacheManager 초기화: "
            f"L1={l1_max_size / 1024 / 1024:.0f}MB, "
            f"Redis={redis_url}, "
            f"Disk={disk_path}"
        )

    async def initialize(self) -> None:
        """Redis 연결 초기화"""
        try:
            self.redis = await aioredis.create_redis_pool(self.redis_url)
            self.redis_available = True
            logger.info("Redis 연결 성공")
        except Exception as e:
            logger.warning(f"Redis 연결 실패: {e}. 폴백 모드 활성화")
            self.redis_available = False

    async def close(self) -> None:
        """리소스 정리"""
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()
            logger.info("Redis 연결 종료")

    async def get(self, key: str) -> Optional[Any]:
        """
        계층적 캐시 조회 (L1 → L2 → L3)

        Args:
            key: 캐시 키

        Returns:
            캐시 값 또는 None
        """
        async with self.stats_lock:
            self.stats.total_requests += 1

        # L1 조회
        value = await self._get_from_l1(key)
        if value is not None:
            async with self.stats_lock:
                self.stats.l1_hits += 1
            logger.debug(f"L1 히트: {key}")
            return value

        # L2 조회
        if self.redis_available:
            value = await self._get_from_l2(key)
            if value is not None:
                async with self.stats_lock:
                    self.stats.l2_hits += 1
                # L1에 승격
                await self._set_to_l1(key, value)
                logger.debug(f"L2 히트: {key}")
                return value

        # L3 조회
        value = await self._get_from_l3(key)
        if value is not None:
            async with self.stats_lock:
                self.stats.l3_hits += 1
            # L1, L2에 승격
            await self._set_to_l1(key, value)
            if self.redis_available:
                await self._set_to_l2(key, value)
            logger.debug(f"L3 히트: {key}")
            return value

        # 미스
        async with self.stats_lock:
            self.stats.misses += 1
        logger.debug(f"캐시 미스: {key}")
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """
        계층적 캐시 저장

        Args:
            key: 캐시 키
            value: 캐시 값
            ttl: TTL (초), None이면 기본값 사용
        """
        ttl = ttl or self.ttl_default

        # L1에 저장
        await self._set_to_l1(key, value, ttl)

        # L2에 저장 (메타데이터)
        if self.redis_available:
            await self._set_to_l2(key, value, ttl)

        # L3에 저장 (전체 문서)
        await self._set_to_l3(key, value, ttl)

        logger.debug(f"캐시 저장: {key} (TTL={ttl}s)")

    async def _get_from_l1(self, key: str) -> Optional[Any]:
        """L1 캐시에서 조회"""
        async with self.l1_lock:
            if key not in self.l1_cache:
                return None

            entry = self.l1_cache[key]

            # 만료 확인
            if entry.is_expired():
                del self.l1_cache[key]
                logger.debug(f"L1 항목 만료: {key}")
                return None

            # LRU 업데이트 (최근 사용으로 이동)
            entry.update_access()
            self.l1_cache.move_to_end(key)

            return entry.value

    async def _set_to_l1(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """L1 캐시에 저장"""
        async with self.l1_lock:
            # 기존 항목 제거
            if key in self.l1_cache:
                del self.l1_cache[key]

            # 새 항목 생성
            size = len(pickle.dumps(value))
            entry = CacheEntry(key=key, value=value, ttl=ttl, size=size)

            # 용량 확인 및 LRU 제거
            await self._evict_l1_if_needed(size)

            self.l1_cache[key] = entry
            async with self.stats_lock:
                self.stats.l1_size += size

    async def _evict_l1_if_needed(self, required_size: int) -> None:
        """필요시 L1 캐시 항목 제거 (LRU)"""
        current_size = sum(e.size for e in self.l1_cache.values())
        current_items = len(self.l1_cache)

        while (
            current_size + required_size > self.l1_max_size
            or current_items >= self.l1_max_items
        ) and self.l1_cache:
            # 가장 오래된 항목 제거
            key, entry = self.l1_cache.popitem(last=False)
            current_size -= entry.size
            async with self.stats_lock:
                self.stats.l1_size -= entry.size
                self.stats.evictions += 1
            logger.debug(f"L1 제거 (LRU): {key}")

    async def _get_from_l2(self, key: str) -> Optional[Any]:
        """L2 캐시(Redis)에서 조회"""
        try:
            data = await self.redis.get(f"cache:{key}")
            if data:
                entry_dict = json.loads(data)
                # TTL 확인
                if entry_dict.get("ttl"):
                    elapsed = time.time() - entry_dict["created_at"]
                    if elapsed > entry_dict["ttl"]:
                        await self.redis.delete(f"cache:{key}")
                        return None
                return entry_dict.get("value")
        except Exception as e:
            logger.warning(f"L2 조회 실패: {e}")
            self.redis_available = False
        return None

    async def _set_to_l2(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """L2 캐시(Redis)에 저장"""
        if not self.redis_available:
            return

        try:
            entry_dict = {
                "value": value,
                "created_at": time.time(),
                "ttl": ttl,
            }
            await self.redis.setex(
                f"cache:{key}",
                ttl or self.ttl_default,
                json.dumps(entry_dict, default=str),
            )
            async with self.stats_lock:
                self.stats.l2_size += len(json.dumps(entry_dict))
        except Exception as e:
            logger.warning(f"L2 저장 실패: {e}")
            self.redis_available = False

    async def _get_from_l3(self, key: str) -> Optional[Any]:
        """L3 캐시(Disk)에서 조회"""
        try:
            file_path = self.disk_path / f"{key}.cache"
            if not file_path.exists():
                return None

            async with aiofiles.open(file_path, "rb") as f:
                data = await f.read()
                entry_dict = pickle.loads(data)

                # TTL 확인
                if entry_dict.get("ttl"):
                    elapsed = time.time() - entry_dict["created_at"]
                    if elapsed > entry_dict["ttl"]:
                        file_path.unlink()
                        return None