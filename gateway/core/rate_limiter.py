from typing import Dict, Optional
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from collections import deque
import time

from ..config.settings import settings
from ..monitoring.logger import get_logger

logger = get_logger(__name__)


class RateLimitStrategy(Enum):
    """限流策略"""
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"


class TokenBucket:
    """令牌桶算法"""
    
    def __init__(self, rate: int, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = asyncio.Lock()
    
    async def consume(self, tokens: int = 1) -> bool:
        """消费令牌"""
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            
            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * self.rate
            )
            self.last_update = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    def get_available_tokens(self) -> int:
        """获取可用令牌数"""
        return int(self.tokens)


class LeakyBucket:
    """漏桶算法"""
    
    def __init__(self, rate: int, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.queue = deque()
        self.last_leak = time.time()
        self.lock = asyncio.Lock()
    
    async def consume(self, tokens: int = 1) -> bool:
        """消费请求"""
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_leak
            
            leaked = int(elapsed * self.rate)
            self.last_leak = now
            
            for _ in range(min(leaked, len(self.queue))):
                self.queue.popleft()
            
            if len(self.queue) + tokens <= self.capacity:
                for _ in range(tokens):
                    self.queue.append(now)
                return True
            
            return False
    
    def get_queue_size(self) -> int:
        """获取队列大小"""
        return len(self.queue)


class FixedWindow:
    """固定窗口算法"""
    
    def __init__(self, requests: int, window_seconds: int):
        self.requests = requests
        self.window_seconds = window_seconds
        self.count = 0
        self.window_start = time.time()
        self.lock = asyncio.Lock()
    
    async def consume(self, tokens: int = 1) -> bool:
        """消费请求"""
        async with self.lock:
            now = time.time()
            
            if now - self.window_start >= self.window_seconds:
                self.count = 0
                self.window_start = now
            
            if self.count + tokens <= self.requests:
                self.count += tokens
                return True
            
            return False
    
    def get_remaining(self) -> int:
        """获取剩余请求数"""
        return max(0, self.requests - self.count)


class SlidingWindow:
    """滑动窗口算法"""
    
    def __init__(self, requests: int, window_seconds: int):
        self.requests = requests
        self.window_seconds = window_seconds
        self.timestamps = deque()
        self.lock = asyncio.Lock()
    
    async def consume(self, tokens: int = 1) -> bool:
        """消费请求"""
        async with self.lock:
            now = time.time()
            
            while self.timestamps and now - self.timestamps[0] >= self.window_seconds:
                self.timestamps.popleft()
            
            if len(self.timestamps) + tokens <= self.requests:
                for _ in range(tokens):
                    self.timestamps.append(now)
                return True
            
            return False
    
    def get_count(self) -> int:
        """获取当前计数"""
        return len(self.timestamps)


class RateLimiter:
    """限流器"""
    
    def __init__(
        self,
        strategy: Optional[RateLimitStrategy] = None,
        requests_per_minute: Optional[int] = None,
        burst_size: Optional[int] = None
    ):
        self.strategy = strategy or RateLimitStrategy(settings.RATE_LIMIT_STRATEGY)
        self.requests_per_minute = requests_per_minute or settings.RATE_LIMIT_REQUESTS_PER_MINUTE
        self.burst_size = burst_size or settings.RATE_LIMIT_BURST_SIZE
        
        self.buckets: Dict[str, TokenBucket] = {}
        self.leaky_buckets: Dict[str, LeakyBucket] = {}
        self.fixed_windows: Dict[str, FixedWindow] = {}
        self.sliding_windows: Dict[str, SlidingWindow] = {}
        
        self.enabled = settings.RATE_LIMIT_ENABLED
    
    def _get_key(self, identifier: str) -> str:
        """获取限流键"""
        return identifier
    
    def _get_token_bucket(self, key: str) -> TokenBucket:
        """获取或创建令牌桶"""
        if key not in self.buckets:
            rate = self.requests_per_minute / 60.0
            self.buckets[key] = TokenBucket(rate, self.burst_size)
        return self.buckets[key]
    
    def _get_leaky_bucket(self, key: str) -> LeakyBucket:
        """获取或创建漏桶"""
        if key not in self.leaky_buckets:
            rate = self.requests_per_minute / 60.0
            self.leaky_buckets[key] = LeakyBucket(rate, self.burst_size)
        return self.leaky_buckets[key]
    
    def _get_fixed_window(self, key: str) -> FixedWindow:
        """获取或创建固定窗口"""
        if key not in self.fixed_windows:
            self.fixed_windows[key] = FixedWindow(self.requests_per_minute, 60)
        return self.fixed_windows[key]
    
    def _get_sliding_window(self, key: str) -> SlidingWindow:
        """获取或创建滑动窗口"""
        if key not in self.sliding_windows:
            self.sliding_windows[key] = SlidingWindow(self.requests_per_minute, 60)
        return self.sliding_windows[key]
    
    async def is_allowed(
        self,
        identifier: str,
        tokens: int = 1
    ) -> bool:
        """检查是否允许请求"""
        if not self.enabled:
            return True
        
        key = self._get_key(identifier)
        
        try:
            if self.strategy == RateLimitStrategy.TOKEN_BUCKET:
                bucket = self._get_token_bucket(key)
                return await bucket.consume(tokens)
            
            elif self.strategy == RateLimitStrategy.LEAKY_BUCKET:
                bucket = self._get_leaky_bucket(key)
                return await bucket.consume(tokens)
            
            elif self.strategy == RateLimitStrategy.FIXED_WINDOW:
                window = self._get_fixed_window(key)
                return await window.consume(tokens)
            
            elif self.strategy == RateLimitStrategy.SLIDING_WINDOW:
                window = self._get_sliding_window(key)
                return await window.consume(tokens)
            
            else:
                return True
                
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return True
    
    async def get_limit_info(self, identifier: str) -> Dict[str, any]:
        """获取限流信息"""
        if not self.enabled:
            return {"enabled": False}
        
        key = self._get_key(identifier)
        info = {
            "enabled": True,
            "strategy": self.strategy.value,
            "requests_per_minute": self.requests_per_minute,
            "burst_size": self.burst_size
        }
        
        try:
            if self.strategy == RateLimitStrategy.TOKEN_BUCKET:
                bucket = self._get_token_bucket(key)
                info["available_tokens"] = bucket.get_available_tokens()
            
            elif self.strategy == RateLimitStrategy.LEAKY_BUCKET:
                bucket = self._get_leaky_bucket(key)
                info["queue_size"] = bucket.get_queue_size()
            
            elif self.strategy == RateLimitStrategy.FIXED_WINDOW:
                window = self._get_fixed_window(key)
                info["remaining_requests"] = window.get_remaining()
            
            elif self.strategy == RateLimitStrategy.SLIDING_WINDOW:
                window = self._get_sliding_window(key)
                info["current_count"] = window.get_count()
            
        except Exception as e:
            logger.error(f"Error getting limit info: {e}")
        
        return info
    
    def cleanup(self):
        """清理过期数据"""
        self.buckets.clear()
        self.leaky_buckets.clear()
        self.fixed_windows.clear()
        self.sliding_windows.clear()
        logger.info("Rate limiter cleaned up")
    
    def set_strategy(self, strategy: RateLimitStrategy):
        """设置限流策略"""
        self.strategy = strategy
        logger.info(f"Rate limit strategy changed to: {strategy.value}")
