from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import asyncio
import hashlib
import json

from ..monitoring.logger import get_logger

logger = get_logger(__name__)


class CacheEntry:
    """缓存条目"""
    
    def __init__(self, value: Any, ttl: Optional[float] = None):
        self.value = value
        self.created_at = datetime.utcnow()
        self.ttl = ttl
        self.expires_at = self.created_at + timedelta(seconds=ttl) if ttl else None
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def get_age(self) -> float:
        """获取年龄（秒）"""
        return (datetime.utcnow() - self.created_at).total_seconds()
    
    def get_ttl_remaining(self) -> Optional[float]:
        """获取剩余TTL"""
        if self.expires_at is None:
            return None
        remaining = (self.expires_at - datetime.utcnow()).total_seconds()
        return max(0, remaining)


class Cache:
    """内存缓存"""
    
    def __init__(self, default_ttl: Optional[float] = None, max_size: int = 1000):
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.cache: Dict[str, CacheEntry] = {}
        self.lock = asyncio.Lock()
        self.hits = 0
        self.misses = 0
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        async with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None
            
            entry = self.cache[key]
            
            if entry.is_expired():
                del self.cache[key]
                self.misses += 1
                return None
            
            self.hits += 1
            return entry.value
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None
    ):
        """设置缓存值"""
        async with self.lock:
            if len(self.cache) >= self.max_size and key not in self.cache:
                await self._evict()
            
            ttl = ttl or self.default_ttl
            self.cache[key] = CacheEntry(value, ttl)
    
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        async with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        async with self.lock:
            if key not in self.cache:
                return False
            
            entry = self.cache[key]
            if entry.is_expired():
                del self.cache[key]
                return False
            
            return True
    
    async def clear(self):
        """清空缓存"""
        async with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
            logger.info("Cache cleared")
    
    async def _evict(self):
        """驱逐缓存"""
        if not self.cache:
            return
        
        oldest_key = min(
            self.cache.keys(),
            key=lambda k: self.cache[k].created_at
        )
        del self.cache[oldest_key]
    
    async def cleanup_expired(self):
        """清理过期缓存"""
        async with self.lock:
            expired_keys = [
                key for key, entry in self.cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self.cache[key]
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        async with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = self.hits / total_requests if total_requests > 0 else 0
            
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
                "default_ttl": self.default_ttl
            }
    
    async def get_keys(self) -> list:
        """获取所有键"""
        async with self.lock:
            return list(self.cache.keys())
    
    async def get_size(self) -> int:
        """获取缓存大小"""
        async with self.lock:
            return len(self.cache)


class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        self.caches: Dict[str, Cache] = {}
        self.lock = asyncio.Lock()
        self.cleanup_task: Optional[asyncio.Task] = None
    
    async def get_cache(
        self,
        name: str,
        default_ttl: Optional[float] = None,
        max_size: int = 1000
    ) -> Cache:
        """获取或创建缓存"""
        async with self.lock:
            if name not in self.caches:
                self.caches[name] = Cache(default_ttl, max_size)
                logger.info(f"Created cache: {name}")
            
            return self.caches[name]
    
    async def remove_cache(self, name: str):
        """移除缓存"""
        async with self.lock:
            if name in self.caches:
                del self.caches[name]
                logger.info(f"Removed cache: {name}")
    
    async def clear_all(self):
        """清空所有缓存"""
        async with self.lock:
            for cache in self.caches.values():
                await cache.clear()
            logger.info("All caches cleared")
    
    async def cleanup_all_expired(self):
        """清理所有过期缓存"""
        async with self.lock:
            for cache in self.caches.values():
                await cache.cleanup_expired()
    
    async def start_cleanup_task(self, interval: int = 60):
        """启动清理任务"""
        if self.cleanup_task and not self.cleanup_task.done():
            return
        
        self.cleanup_task = asyncio.create_task(self._cleanup_loop(interval))
        logger.info("Started cache cleanup task")
    
    async def stop_cleanup_task(self):
        """停止清理任务"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info("Stopped cache cleanup task")
    
    async def _cleanup_loop(self, interval: int):
        """清理循环"""
        while True:
            try:
                await self.cleanup_all_expired()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache cleanup loop: {e}")
                await asyncio.sleep(5)
    
    def generate_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        key_parts = []
        
        for arg in args:
            if isinstance(arg, (dict, list)):
                key_parts.append(json.dumps(arg, sort_keys=True))
            else:
                key_parts.append(str(arg))
        
        for k, v in sorted(kwargs.items()):
            if isinstance(v, (dict, list)):
                key_parts.append(f"{k}={json.dumps(v, sort_keys=True)}")
            else:
                key_parts.append(f"{k}={v}")
        
        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
