from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum


logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """服务状态枚举"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DISABLED = "disabled"
    UNKNOWN = "unknown"


@dataclass
class ServiceInstance:
    """服务实例"""
    id: str
    name: str
    url: str
    health_check: str = "/"
    weight: int = 1
    enabled: bool = True
    status: ServiceStatus = ServiceStatus.UNKNOWN
    last_health_check: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "health_check": self.health_check,
            "weight": self.weight,
            "enabled": self.enabled,
            "status": self.status.value,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "metadata": self.metadata
        }


class ServiceRegistry:
    """服务注册表"""
    
    def __init__(self):
        self.services: Dict[str, List[ServiceInstance]] = {}
        self.service_lock = asyncio.Lock()
        self.health_check_task: Optional[asyncio.Task] = None
    
    async def register_service(
        self,
        name: str,
        url: str,
        health_check: str = "/",
        weight: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ServiceInstance:
        """注册服务"""
        async with self.service_lock:
            instance_id = f"{name}_{url}_{datetime.now().timestamp()}"
            
            instance = ServiceInstance(
                id=instance_id,
                name=name,
                url=url,
                health_check=health_check,
                weight=weight,
                enabled=True,
                status=ServiceStatus.UNKNOWN,
                metadata=metadata or {}
            )
            
            if name not in self.services:
                self.services[name] = []
            
            self.services[name].append(instance)
            logger.info(f"Registered service: {name} at {url}")
            
            return instance
    
    async def unregister_service(self, service_name: str, instance_id: str) -> bool:
        """注销服务"""
        async with self.service_lock:
            if service_name not in self.services:
                return False
            
            instances = self.services[service_name]
            for i, instance in enumerate(instances):
                if instance.id == instance_id:
                    instances.pop(i)
                    logger.info(f"Unregistered service: {service_name} - {instance_id}")
                    
                    if not instances:
                        del self.services[service_name]
                    
                    return True
            
            return False
    
    async def get_service(self, service_name: str) -> Optional[List[ServiceInstance]]:
        """获取服务的所有实例"""
        async with self.service_lock:
            instances = self.services.get(service_name, [])
            return [inst for inst in instances if inst.enabled]
    
    async def get_healthy_services(self, service_name: str) -> List[ServiceInstance]:
        """获取健康的实例"""
        instances = await self.get_service(service_name)
        return [inst for inst in instances if inst.status == ServiceStatus.HEALTHY]
    
    async def disable_service(self, service_name: str, instance_id: str) -> bool:
        """禁用服务实例"""
        async with self.service_lock:
            if service_name not in self.services:
                return False
            
            instances = self.services[service_name]
            for instance in instances:
                if instance.id == instance_id:
                    instance.enabled = False
                    instance.status = ServiceStatus.DISABLED
                    logger.warning(f"Disabled service: {service_name} - {instance_id}")
                    return True
            
            return False
    
    async def enable_service(self, service_name: str, instance_id: str) -> bool:
        """启用服务实例"""
        async with self.service_lock:
            if service_name not in self.services:
                return False
            
            instances = self.services[service_name]
            for instance in instances:
                if instance.id == instance_id:
                    instance.enabled = True
                    instance.status = ServiceStatus.UNKNOWN
                    logger.info(f"Enabled service: {service_name} - {instance_id}")
                    return True
            
            return False
    
    async def update_service_status(
        self,
        service_name: str,
        instance_id: str,
        status: ServiceStatus
    ) -> bool:
        """更新服务状态"""
        async with self.service_lock:
            if service_name not in self.services:
                return False
            
            instances = self.services[service_name]
            for instance in instances:
                if instance.id == instance_id:
                    instance.status = status
                    instance.last_health_check = datetime.now()
                    
                    if status == ServiceStatus.HEALTHY:
                        instance.consecutive_failures = 0
                        instance.consecutive_successes += 1
                    else:
                        instance.consecutive_failures += 1
                        instance.consecutive_successes = 0
                    
                    return True
            
            return False
    
    def get_all_services(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取所有服务"""
        result = {}
        for name, instances in self.services.items():
            result[name] = [inst.to_dict() for inst in instances]
        return result
    
    def get_service_count(self) -> int:
        """获取服务数量"""
        return len(self.services)
    
    def get_instance_count(self) -> int:
        """获取实例数量"""
        return sum(len(instances) for instances in self.services.values())
    
    async def start_health_check(self, check_interval: int = 30):
        """启动健康检查"""
        if self.health_check_task and not self.health_check_task.done():
            return
        
        self.health_check_task = asyncio.create_task(self._health_check_loop(check_interval))
        logger.info("Health check started")
    
    async def stop_health_check(self):
        """停止健康检查"""
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
            logger.info("Health check stopped")
    
    async def _health_check_loop(self, check_interval: int):
        """健康检查循环"""
        import httpx
        
        while True:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {str(e)}")
                await asyncio.sleep(check_interval)
    
    async def _perform_health_checks(self):
        """执行健康检查"""
        import httpx
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            for service_name, instances in self.services.items():
                for instance in instances:
                    if not instance.enabled:
                        continue
                    
                    try:
                        health_url = f"{instance.url.rstrip('/')}/{instance.health_check.lstrip('/')}"
                        response = await client.get(health_url)
                        
                        if response.status_code == 200:
                            await self.update_service_status(
                                service_name,
                                instance.id,
                                ServiceStatus.HEALTHY
                            )
                        else:
                            await self.update_service_status(
                                service_name,
                                instance.id,
                                ServiceStatus.UNHEALTHY
                            )
                    except Exception as e:
                        logger.warning(f"Health check failed for {service_name} - {instance.url}: {str(e)}")
                        await self.update_service_status(
                            service_name,
                            instance.id,
                            ServiceStatus.UNHEALTHY
                        )


# 全局服务注册表实例
service_registry = ServiceRegistry()
