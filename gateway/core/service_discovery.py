from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
from enum import Enum

from ..config.service_registry import ServiceRegistry, ServiceInstance, ServiceStatus
from ..config.settings import settings
from ..monitoring.logger import get_logger

logger = get_logger(__name__)


class DiscoveryStrategy(Enum):
    """服务发现策略"""
    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED = "weighted"


class ServiceDiscovery:
    """服务发现"""
    
    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self.strategy = DiscoveryStrategy(settings.LOAD_BALANCER_STRATEGY)
        self.round_robin_index: Dict[str, int] = {}
        self.discovery_lock = asyncio.Lock()
    
    async def discover_service(
        self,
        service_name: str,
        strategy: Optional[DiscoveryStrategy] = None
    ) -> Optional[ServiceInstance]:
        """发现服务实例"""
        try:
            instances = await self.registry.get_service(service_name)
            
            if not instances:
                logger.warning(f"No instances found for service: {service_name}")
                return None
            
            healthy_instances = [
                inst for inst in instances
                if inst.status == ServiceStatus.HEALTHY and inst.enabled
            ]
            
            if not healthy_instances:
                logger.warning(f"No healthy instances found for service: {service_name}")
                return None
            
            selected_strategy = strategy or self.strategy
            instance = await self._select_instance(healthy_instances, service_name, selected_strategy)
            
            if instance:
                logger.debug(f"Selected instance {instance.id} for service {service_name}")
            
            return instance
            
        except Exception as e:
            logger.error(f"Error discovering service {service_name}: {e}")
            return None
    
    async def _select_instance(
        self,
        instances: List[ServiceInstance],
        service_name: str,
        strategy: DiscoveryStrategy
    ) -> Optional[ServiceInstance]:
        """选择服务实例"""
        if not instances:
            return None
        
        if strategy == DiscoveryStrategy.ROUND_ROBIN:
            return await self._round_robin_select(instances, service_name)
        elif strategy == DiscoveryStrategy.RANDOM:
            return await self._random_select(instances)
        elif strategy == DiscoveryStrategy.LEAST_CONNECTIONS:
            return await self._least_connections_select(instances)
        elif strategy == DiscoveryStrategy.WEIGHTED:
            return await self._weighted_select(instances)
        else:
            return instances[0]
    
    async def _round_robin_select(
        self,
        instances: List[ServiceInstance],
        service_name: str
    ) -> ServiceInstance:
        """轮询选择"""
        async with self.discovery_lock:
            if service_name not in self.round_robin_index:
                self.round_robin_index[service_name] = 0
            
            index = self.round_robin_index[service_name] % len(instances)
            self.round_robin_index[service_name] = index + 1
            
            return instances[index]
    
    async def _random_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """随机选择"""
        import random
        return random.choice(instances)
    
    async def _least_connections_select(
        self,
        instances: List[ServiceInstance]
    ) -> ServiceInstance:
        """最少连接选择"""
        return min(instances, key=lambda x: x.metadata.get('active_connections', 0))
    
    async def _weighted_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """加权选择"""
        total_weight = sum(inst.weight for inst in instances)
        if total_weight == 0:
            return instances[0]
        
        import random
        rand = random.uniform(0, total_weight)
        current_weight = 0
        
        for instance in instances:
            current_weight += instance.weight
            if rand <= current_weight:
                return instance
        
        return instances[-1]
    
    async def discover_all_services(self) -> Dict[str, List[ServiceInstance]]:
        """发现所有服务"""
        try:
            services = await self.registry.get_all_services()
            result = {}
            
            for service_name, instances in services.items():
                healthy_instances = [
                    inst for inst in instances
                    if inst.status == ServiceStatus.HEALTHY and inst.enabled
                ]
                if healthy_instances:
                    result[service_name] = healthy_instances
            
            return result
            
        except Exception as e:
            logger.error(f"Error discovering all services: {e}")
            return {}
    
    async def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """获取服务状态"""
        try:
            instances = await self.registry.get_service(service_name)
            
            if not instances:
                return {
                    "service": service_name,
                    "status": "unknown",
                    "instances": []
                }
            
            healthy_count = sum(
                1 for inst in instances
                if inst.status == ServiceStatus.HEALTHY and inst.enabled
            )
            
            return {
                "service": service_name,
                "status": "healthy" if healthy_count > 0 else "unhealthy",
                "total_instances": len(instances),
                "healthy_instances": healthy_count,
                "instances": [
                    {
                        "id": inst.id,
                        "url": inst.url,
                        "status": inst.status.value,
                        "enabled": inst.enabled,
                        "weight": inst.weight,
                        "last_health_check": inst.last_health_check.isoformat() if inst.last_health_check else None
                    }
                    for inst in instances
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            return {
                "service": service_name,
                "status": "error",
                "error": str(e)
            }
    
    async def get_all_services_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有服务状态"""
        try:
            services = await self.registry.get_all_services()
            result = {}
            
            for service_name in services.keys():
                result[service_name] = await self.get_service_status(service_name)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting all services status: {e}")
            return {}
    
    def set_strategy(self, strategy: DiscoveryStrategy):
        """设置发现策略"""
        self.strategy = strategy
        logger.info(f"Discovery strategy changed to: {strategy.value}")
