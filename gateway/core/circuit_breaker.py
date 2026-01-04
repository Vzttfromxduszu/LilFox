from typing import Dict, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from dataclasses import dataclass, field

from ..config.settings import settings
from ..monitoring.logger import get_logger

logger = get_logger(__name__)


class CircuitBreakerState(Enum):
    """熔断器状态"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout: int = 60
    half_open_max_calls: int = 3


@dataclass
class CircuitBreakerStats:
    """熔断器统计"""
    total_calls: int = 0
    success_calls: int = 0
    failure_calls: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    last_state_change: Optional[datetime] = None


class CircuitBreaker:
    """熔断器"""
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig(
            failure_threshold=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            success_threshold=settings.CIRCUIT_BREAKER_SUCCESS_THRESHOLD,
            timeout=settings.CIRCUIT_BREAKER_TIMEOUT,
            half_open_max_calls=settings.CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS
        )
        
        self.state = CircuitBreakerState.CLOSED
        self.stats = CircuitBreakerStats()
        self.half_open_calls = 0
        self.lock = asyncio.Lock()
        self.enabled = settings.CIRCUIT_BREAKER_ENABLED
        
        self.on_state_change: Optional[Callable[[CircuitBreakerState, CircuitBreakerState], None]] = None
    
    async def call(self, func: Callable, *args, **kwargs):
        """执行函数调用"""
        if not self.enabled:
            return await func(*args, **kwargs)
        
        if not await self._can_execute():
            raise CircuitBreakerOpenError(
                f"Circuit breaker {self.name} is OPEN"
            )
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise e
    
    async def _can_execute(self) -> bool:
        """检查是否可以执行"""
        async with self.lock:
            if self.state == CircuitBreakerState.CLOSED:
                return True
            
            elif self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    await self._transition_to_half_open()
                    return True
                return False
            
            elif self.state == CircuitBreakerState.HALF_OPEN:
                return self.half_open_calls < self.config.half_open_max_calls
            
            return False
    
    def _should_attempt_reset(self) -> bool:
        """检查是否应该尝试重置"""
        if not self.stats.last_failure_time:
            return False
        
        elapsed = datetime.utcnow() - self.stats.last_failure_time
        return elapsed.total_seconds() >= self.config.timeout
    
    async def _on_success(self):
        """成功回调"""
        async with self.lock:
            self.stats.total_calls += 1
            self.stats.success_calls += 1
            self.stats.consecutive_successes += 1
            self.stats.consecutive_failures = 0
            self.stats.last_success_time = datetime.utcnow()
            
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.half_open_calls += 1
                
                if self.stats.consecutive_successes >= self.config.success_threshold:
                    await self._transition_to_closed()
    
    async def _on_failure(self):
        """失败回调"""
        async with self.lock:
            self.stats.total_calls += 1
            self.stats.failure_calls += 1
            self.stats.consecutive_failures += 1
            self.stats.consecutive_successes = 0
            self.stats.last_failure_time = datetime.utcnow()
            
            if self.state == CircuitBreakerState.CLOSED:
                if self.stats.consecutive_failures >= self.config.failure_threshold:
                    await self._transition_to_open()
            
            elif self.state == CircuitBreakerState.HALF_OPEN:
                await self._transition_to_open()
    
    async def _transition_to_open(self):
        """转换到开启状态"""
        old_state = self.state
        self.state = CircuitBreakerState.OPEN
        self.stats.last_state_change = datetime.utcnow()
        self.half_open_calls = 0
        
        logger.warning(
            f"Circuit breaker {self.name} transitioned from {old_state.value} to OPEN"
        )
        
        if self.on_state_change:
            self.on_state_change(old_state, self.state)
    
    async def _transition_to_half_open(self):
        """转换到半开启状态"""
        old_state = self.state
        self.state = CircuitBreakerState.HALF_OPEN
        self.stats.last_state_change = datetime.utcnow()
        self.half_open_calls = 0
        self.stats.consecutive_successes = 0
        
        logger.info(
            f"Circuit breaker {self.name} transitioned from {old_state.value} to HALF_OPEN"
        )
        
        if self.on_state_change:
            self.on_state_change(old_state, self.state)
    
    async def _transition_to_closed(self):
        """转换到关闭状态"""
        old_state = self.state
        self.state = CircuitBreakerState.CLOSED
        self.stats.last_state_change = datetime.utcnow()
        self.half_open_calls = 0
        self.stats.consecutive_failures = 0
        
        logger.info(
            f"Circuit breaker {self.name} transitioned from {old_state.value} to CLOSED"
        )
        
        if self.on_state_change:
            self.on_state_change(old_state, self.state)
    
    async def reset(self):
        """重置熔断器"""
        async with self.lock:
            old_state = self.state
            self.state = CircuitBreakerState.CLOSED
            self.stats = CircuitBreakerStats()
            self.half_open_calls = 0
            
            logger.info(f"Circuit breaker {self.name} reset from {old_state.value}")
    
    def get_state(self) -> CircuitBreakerState:
        """获取当前状态"""
        return self.state
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "name": self.name,
            "state": self.state.value,
            "total_calls": self.stats.total_calls,
            "success_calls": self.stats.success_calls,
            "failure_calls": self.stats.failure_calls,
            "consecutive_failures": self.stats.consecutive_failures,
            "consecutive_successes": self.stats.consecutive_successes,
            "last_failure_time": self.stats.last_failure_time.isoformat() if self.stats.last_failure_time else None,
            "last_success_time": self.stats.last_success_time.isoformat() if self.stats.last_success_time else None,
            "last_state_change": self.stats.last_state_change.isoformat() if self.stats.last_state_change else None,
            "half_open_calls": self.half_open_calls,
            "enabled": self.enabled
        }
    
    def is_open(self) -> bool:
        """检查是否开启"""
        return self.state == CircuitBreakerState.OPEN
    
    def is_closed(self) -> bool:
        """检查是否关闭"""
        return self.state == CircuitBreakerState.CLOSED
    
    def is_half_open(self) -> bool:
        """检查是否半开启"""
        return self.state == CircuitBreakerState.HALF_OPEN


class CircuitBreakerOpenError(Exception):
    """熔断器开启异常"""
    pass


class CircuitBreakerManager:
    """熔断器管理器"""
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
        self.lock = asyncio.Lock()
    
    async def get_breaker(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """获取或创建熔断器"""
        async with self.lock:
            if name not in self.breakers:
                self.breakers[name] = CircuitBreaker(name, config)
            return self.breakers[name]
    
    async def remove_breaker(self, name: str):
        """移除熔断器"""
        async with self.lock:
            if name in self.breakers:
                del self.breakers[name]
                logger.info(f"Removed circuit breaker: {name}")
    
    async def reset_all(self):
        """重置所有熔断器"""
        async with self.lock:
            for breaker in self.breakers.values():
                await breaker.reset()
            logger.info("All circuit breakers reset")
    
    def get_all_stats(self) -> Dict[str, Dict]:
        """获取所有熔断器统计"""
        return {
            name: breaker.get_stats()
            for name, breaker in self.breakers.items()
        }
    
    def get_all_states(self) -> Dict[str, str]:
        """获取所有熔断器状态"""
        return {
            name: breaker.get_state().value
            for name, breaker in self.breakers.items()
        }
