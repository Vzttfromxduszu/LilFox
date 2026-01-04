from typing import Optional, Dict, Any, Tuple
from fastapi import Request, Response
from httpx import AsyncClient, HTTPError
import asyncio

from ..config.service_registry import ServiceInstance
from ..config.settings import settings
from .service_discovery import ServiceDiscovery
from .load_balancer import LoadBalancer
from ..monitoring.logger import get_logger

logger = get_logger(__name__)


class RequestRouter:
    """请求路由器"""
    
    def __init__(
        self,
        discovery: ServiceDiscovery,
        load_balancer: LoadBalancer
    ):
        self.discovery = discovery
        self.load_balancer = load_balancer
        self.client = AsyncClient(timeout=30.0)
        self.gateway_prefix = settings.GATEWAY_PREFIX.rstrip('/')
    
    async def route_request(
        self,
        request: Request,
        path: str,
        method: str
    ) -> Response:
        """路由请求到后端服务"""
        try:
            service_name, service_path = self._parse_path(path)
            
            if not service_name:
                return Response(
                    content='{"error": "Invalid path"}',
                    status_code=400,
                    media_type="application/json"
                )
            
            instance = await self.discovery.discover_service(service_name)
            
            if not instance:
                return Response(
                    content=f'{{"error": "Service {service_name} not available"}}',
                    status_code=503,
                    media_type="application/json"
                )
            
            return await self._forward_request(
                instance,
                request,
                service_path,
                method
            )
            
        except Exception as e:
            logger.error(f"Error routing request: {e}")
            return Response(
                content='{"error": "Internal server error"}',
                status_code=500,
                media_type="application/json"
            )
    
    def _parse_path(self, path: str) -> Tuple[Optional[str], str]:
        """解析路径，提取服务名称和服务路径"""
        if path.startswith(self.gateway_prefix):
            path = path[len(self.gateway_prefix):].lstrip('/')
        
        parts = path.split('/', 1)
        
        if len(parts) == 0 or not parts[0]:
            return None, ''
        
        service_name = parts[0]
        service_path = parts[1] if len(parts) > 1 else ''
        
        return service_name, service_path
    
    async def _forward_request(
        self,
        instance: ServiceInstance,
        request: Request,
        service_path: str,
        method: str
    ) -> Response:
        """转发请求到服务实例"""
        try:
            url = f"{instance.url.rstrip('/')}/{service_path}"
            
            headers = dict(request.headers)
            headers.pop('host', None)
            headers['X-Forwarded-For'] = request.client.host if request.client else 'unknown'
            headers['X-Forwarded-Proto'] = request.url.scheme
            headers['X-Forwarded-Host'] = request.url.netloc
            
            body = await request.body()
            
            response = await self.client.request(
                method=method,
                url=url,
                headers=headers,
                content=body if body else None,
                params=request.query_params,
                follow_redirects=False
            )
            
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get('content-type')
            )
            
        except HTTPError as e:
            logger.error(f"HTTP error forwarding request: {e}")
            return Response(
                content=f'{{"error": "Service error: {str(e)}"}}',
                status_code=502,
                media_type="application/json"
            )
        except Exception as e:
            logger.error(f"Error forwarding request: {e}")
            return Response(
                content='{"error": "Failed to forward request"}',
                status_code=502,
                media_type="application/json"
            )
    
    async def route_with_retry(
        self,
        request: Request,
        path: str,
        method: str
    ) -> Response:
        """带重试的请求路由"""
        try:
            service_name, service_path = self._parse_path(path)
            
            if not service_name:
                return Response(
                    content='{"error": "Invalid path"}',
                    status_code=400,
                    media_type="application/json"
                )
            
            instances = await self.discovery.registry.get_service(service_name)
            
            if not instances:
                return Response(
                    content=f'{{"error": "Service {service_name} not found"}}',
                    status_code=404,
                    media_type="application/json"
                )
            
            async def request_func(instance: ServiceInstance):
                return await self._forward_request(instance, request, service_path, method)
            
            return await self.load_balancer.retry_request(
                request_func,
                instances,
                service_name,
                request.client.host if request.client else None
            )
            
        except Exception as e:
            logger.error(f"Error routing with retry: {e}")
            return Response(
                content='{"error": "Service unavailable"}',
                status_code=503,
                media_type="application/json"
            )
    
    async def get_service_info(self, path: str) -> Optional[Dict[str, Any]]:
        """获取服务信息"""
        service_name, _ = self._parse_path(path)
        
        if not service_name:
            return None
        
        return await self.discovery.get_service_status(service_name)
    
    async def close(self):
        """关闭路由器"""
        await self.client.aclose()
        logger.info("Request router closed")
