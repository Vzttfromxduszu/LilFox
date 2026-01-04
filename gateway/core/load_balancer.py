from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import asyncio

from ..config.service_registry import ServiceInstance, ServiceStatus
from ..config.settings import settings
from ..monitoring.logger import get_logger

logger = get_logger(__name__)


class LoadBalancingStrategy(Enum):
    """负载均衡策略"""
    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED = "weighted"
    IP_HASH = "ip_hash"


class LoadBalancer:
    """负载均衡器"""
    
    def __init__(self, strategy: Optional[LoadBalancingStrategy] = None):
        self.strategy = strategy or LoadBalancingStrategy(settings.LOAD_BALANCER_STRATEGY)
        self.round_robin_index: Dict[str, int] = {}
        self.connection_counts: Dict[str, int] = {}
        self.balancer_lock = asyncio.Lock()
        self.retry_count = settings.LOAD_BALANCER_RETRY_COUNT
        self.retry_delay = settings.LOAD_BALANCER_RETRY_DELAY
    
    async def select_instance(
        self,
        instances: List[ServiceInstance],
        service_name: str,
        client_ip: Optional[str] = None
    ) -> Optional[ServiceInstance]:
        """选择服务实例"""
        try:
            healthy_instances = [
                inst for inst in instances
                if inst.status == ServiceStatus.HEALTHY and inst.enabled
            ]
            
            if not healthy_instances:
                logger.warning(f"No healthy instances for service: {service_name}")
                return None
            
            instance = await self._select_by_strategy(
                healthy_instances,
                service_name,
                client_ip
            )
            
            if instance:
                await self._increment_connection(instance.id)
                logger.debug(
                    f"Selected instance {instance.id} for service {service_name} "
                    f"using {self.strategy.value} strategy"
                )
            
            return instance
            
        except Exception as e:
            logger.error(f"Error selecting instance: {e}")
            return None
    
    async def _select_by_strategy(
        self,
        instances: List[ServiceInstance],
        service_name: str,
        client_ip: Optional[str]
    ) -> ServiceInstance:
        """根据策略选择实例"""
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return await self._round_robin(instances, service_name)
        elif self.strategy == LoadBalancingStrategy.RANDOM:
            return await self._random(instances)
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return await self._least_connections(instances)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED:
            return await self._weighted(instances)
        elif self.strategy == LoadBalancingStrategy.IP_HASH:
            return await self._ip_hash(instances, client_ip)
        else:
            return instances[0]
    
    async def _round_robin(
        self,
        instances: List[ServiceInstance],
        service_name: str
    ) -> ServiceInstance:
        """轮询策略"""
        async with self.balancer_lock:
            if service_name not in self.round_robin_index:
                self.round_robin_index[service_name] = 0
            
            index = self.round_robin_index[service_name] % len(instances)
            self.round_robin_index[service_name] = index + 1
            
            return instances[index]
    
    async def _random(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """随机策略"""
        import random
        return random.choice(instances)
    
    async def _least_connections(
        self,
        instances: List[ServiceInstance]
    ) -> ServiceInstance:
        """最少连接策略"""
        instance_counts = [
            (inst, self.connection_counts.get(inst.id, 0))
            for inst in instances
        ]
        return min(instance_counts, key=lambda x: x[1])[0]
    
    async def _weighted(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """加权策略"""
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
    
    async def _ip_hash(
        self,
        instances: List[ServiceInstance],
        client_ip: Optional[str]
    ) -> ServiceInstance:
        """IP哈希策略"""
        if not client_ip:
            return instances[0]
        
        import hashlib
        hash_value = int(hashlib.md5(client_ip.encode()).hexdigest(), 16)
        index = hash_value % len(instances)
        
        return instances[index]
    
    async def _increment_connection(self, instance_id: str):
        """增加连接计数"""
        async with self.balancer_lock:
            self.connection_counts[instance_id] = self.connection_counts.get(instance_id, 0) + 1
    
    async def _decrement_connection(self, instance_id: str):
        """减少连接计数"""
        async with self.balancer_lock:
            if instance_id in self.connection_counts:
                self.connection_counts[instance_id] -= 1
                if self.connection_counts[instance_id] <= 0:
                    del self.connection_counts[instance_id]
    
    async def release_instance(self, instance: ServiceInstance):
        """释放实例"""
        await self._decrement_connection(instance.id)
    
    async def get_connection_counts(self) -> Dict[str, int]:
        """获取连接计数"""
        async with self.balancer_lock:
            return self.connection_counts.copy()
    
    async def retry_request(
        self,
        request_func,
        instances: List[ServiceInstance],
        service_name: str,
        client_ip: Optional[str] = None
    ) -> Any:
        """重试请求"""
        last_error = None
        
        for attempt in range(self.retry_count):
            instance = await self.select_instance(instances, service_name, client_ip)
            
            if not instance:
                logger.error(f"No available instance for service: {service_name}")
                continue
            
            try:
                result = await request_func(instance)
                await self.release_instance(instance)
                return result
                
            except Exception as e:
                last_error = e
                await self.release_instance(instance)
                logger.warning(
                    f"Request failed for instance {instance.id}, "
                    f"attempt {attempt + 1}/{self.retry_count}: {e}"
                )
                
                if attempt < self.retry_count - 1:
                    await asyncio.sleep(self.retry_delay)
        
        raise last_error or Exception("All retry attempts failed")
    
    def set_strategy(self, strategy: LoadBalancingStrategy):
        """设置负载均衡策略"""
        self.strategy = strategy
        logger.info(f"Load balancing strategy changed to: {strategy.value}")
    
    def reset(self):
        """重置负载均衡器状态"""
        self.round_robin_index.clear()
        self.connection_counts.clear()
        logger.info("Load balancer state reset")
