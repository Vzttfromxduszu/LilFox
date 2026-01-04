from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import asyncio

from ..config.service_registry import ServiceInstance, ServiceStatus
from ..monitoring.logger import get_logger

logger = get_logger(__name__)


class HealthStatus(Enum):
    """健康状态"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class HealthCheck:
    """健康检查"""
    
    def __init__(
        self,
        name: str,
        check_func: Optional[callable] = None,
        timeout: float = 5.0,
        interval: int = 30
    ):
        self.name = name
        self.check_func = check_func or self._default_check
        self.timeout = timeout
        self.interval = interval
        self.status = HealthStatus.UNKNOWN
        self.last_check: Optional[datetime] = None
        self.last_error: Optional[str] = None
        self.consecutive_failures = 0
        self.consecutive_successes = 0
    
    async def _default_check(self) -> bool:
        """默认检查函数"""
        return True
    
    async def check(self) -> bool:
        """执行健康检查"""
        try:
            result = await asyncio.wait_for(
                self.check_func(),
                timeout=self.timeout
            )
            
            self.last_check = datetime.utcnow()
            
            if result:
                self.status = HealthStatus.HEALTHY
                self.consecutive_successes += 1
                self.consecutive_failures = 0
                self.last_error = None
                return True
            else:
                self.status = HealthStatus.UNHEALTHY
                self.consecutive_failures += 1
                self.consecutive_successes = 0
                self.last_error = "Check returned False"
                return False
                
        except asyncio.TimeoutError:
            self.status = HealthStatus.UNHEALTHY
            self.consecutive_failures += 1
            self.consecutive_successes = 0
            self.last_error = "Health check timed out"
            self.last_check = datetime.utcnow()
            return False
        except Exception as e:
            self.status = HealthStatus.UNHEALTHY
            self.consecutive_failures += 1
            self.consecutive_successes = 0
            self.last_error = str(e)
            self.last_check = datetime.utcnow()
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "name": self.name,
            "status": self.status.value,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "last_error": self.last_error,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes
        }


class HealthChecker:
    """健康检查器"""
    
    def __init__(self):
        self.checks: Dict[str, HealthCheck] = {}
        self.check_task: Optional[asyncio.Task] = None
        self.running = False
    
    def add_check(
        self,
        name: str,
        check_func: Optional[callable] = None,
        timeout: float = 5.0,
        interval: int = 30
    ) -> HealthCheck:
        """添加健康检查"""
        check = HealthCheck(name, check_func, timeout, interval)
        self.checks[name] = check
        logger.info(f"Added health check: {name}")
        return check
    
    def remove_check(self, name: str):
        """移除健康检查"""
        if name in self.checks:
            del self.checks[name]
            logger.info(f"Removed health check: {name}")
    
    async def check_all(self) -> Dict[str, Dict[str, Any]]:
        """检查所有"""
        results = {}
        
        for name, check in self.checks.items():
            results[name] = await check.check()
        
        return results
    
    async def check_one(self, name: str) -> Optional[Dict[str, Any]]:
        """检查单个"""
        if name not in self.checks:
            return None
        
        check = self.checks[name]
        result = await check.check()
        
        return {
            "name": name,
            "result": result,
            "status": check.get_status()
        }
    
    async def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有状态"""
        return {
            name: check.get_status()
            for name, check in self.checks.items()
        }
    
    async def get_overall_status(self) -> Dict[str, Any]:
        """获取整体状态"""
        if not self.checks:
            return {
                "status": "unknown",
                "message": "No health checks configured"
            }
        
        all_status = await self.get_all_status()
        
        healthy_count = sum(
            1 for status in all_status.values()
            if status["status"] == HealthStatus.HEALTHY.value
        )
        unhealthy_count = sum(
            1 for status in all_status.values()
            if status["status"] == HealthStatus.UNHEALTHY.value
        )
        
        total_count = len(all_status)
        
        if healthy_count == total_count:
            overall_status = HealthStatus.HEALTHY
            message = "All systems operational"
        elif unhealthy_count == total_count:
            overall_status = HealthStatus.UNHEALTHY
            message = "All systems down"
        elif unhealthy_count > total_count / 2:
            overall_status = HealthStatus.UNHEALTHY
            message = "Major systems down"
        else:
            overall_status = HealthStatus.DEGRADED
            message = "Some systems degraded"
        
        return {
            "status": overall_status.value,
            "message": message,
            "total_checks": total_count,
            "healthy_checks": healthy_count,
            "unhealthy_checks": unhealthy_count,
            "checks": all_status
        }
    
    async def start_periodic_checks(self):
        """启动定期检查"""
        if self.running:
            logger.warning("Health checks already running")
            return
        
        self.running = True
        self.check_task = asyncio.create_task(self._periodic_check_loop())
        logger.info("Started periodic health checks")
    
    async def stop_periodic_checks(self):
        """停止定期检查"""
        if not self.running:
            return
        
        self.running = False
        
        if self.check_task:
            self.check_task.cancel()
            try:
                await self.check_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped periodic health checks")
    
    async def _periodic_check_loop(self):
        """定期检查循环"""
        while self.running:
            try:
                await self.check_all()
                
                if self.checks:
                    intervals = [check.interval for check in self.checks.values()]
                    min_interval = min(intervals) if intervals else 30
                else:
                    min_interval = 30
                
                await asyncio.sleep(min_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic health check: {e}")
                await asyncio.sleep(5)
    
    async def check_service_instance(
        self,
        instance: ServiceInstance,
        health_check_timeout: float = 5.0
    ) -> bool:
        """检查服务实例"""
        try:
            import httpx
            
            url = f"{instance.url.rstrip('/')}/{instance.health_check.lstrip('/')}"
            
            async with httpx.AsyncClient(timeout=health_check_timeout) as client:
                response = await client.get(url)
                
                if response.status_code < 500:
                    return True
                else:
                    return False
                    
        except Exception as e:
            logger.error(f"Health check failed for {instance.id}: {e}")
            return False
    
    async def check_service_instances(
        self,
        instances: List[ServiceInstance],
        health_check_timeout: float = 5.0
    ) -> Dict[str, bool]:
        """检查多个服务实例"""
        results = {}
        
        tasks = [
            self.check_service_instance(instance, health_check_timeout)
            for instance in instances
        ]
        
        check_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for instance, result in zip(instances, check_results):
            if isinstance(result, Exception):
                results[instance.id] = False
            else:
                results[instance.id] = result
        
        return results
    
    def reset_all(self):
        """重置所有检查"""
        for check in self.checks.values():
            check.status = HealthStatus.UNKNOWN
            check.last_check = None
            check.last_error = None
            check.consecutive_failures = 0
            check.consecutive_successes = 0
        
        logger.info("All health checks reset")
