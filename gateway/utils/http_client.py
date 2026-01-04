from typing import Optional
from httpx import AsyncClient, HTTPError
import asyncio

from ..monitoring.logger import get_logger

logger = get_logger(__name__)


class HTTPClient:
    """HTTP客户端"""
    
    def __init__(
        self,
        timeout: float = 30.0,
        max_connections: int = 100,
        max_keepalive_connections: int = 20
    ):
        self.timeout = timeout
        self.max_connections = max_connections
        self.max_keepalive_connections = max_keepalive_connections
        self.client: Optional[AsyncClient] = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.client = AsyncClient(
            timeout=self.timeout,
            limits=self._get_limits()
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.client:
            await self.client.aclose()
    
    def _get_limits(self):
        """获取连接限制"""
        from httpx import Limits
        return Limits(
            max_connections=self.max_connections,
            max_keepalive_connections=self.max_keepalive_connections
        )
    
    async def get(
        self,
        url: str,
        headers: Optional[dict] = None,
        params: Optional[dict] = None,
        timeout: Optional[float] = None
    ):
        """GET请求"""
        if not self.client:
            raise RuntimeError("HTTPClient not initialized. Use async context manager.")
        
        try:
            response = await self.client.get(
                url,
                headers=headers,
                params=params,
                timeout=timeout or self.timeout
            )
            return response
        except HTTPError as e:
            logger.error(f"HTTP GET error: {e}")
            raise
    
    async def post(
        self,
        url: str,
        json: Optional[dict] = None,
        data: Optional[dict] = None,
        headers: Optional[dict] = None,
        timeout: Optional[float] = None
    ):
        """POST请求"""
        if not self.client:
            raise RuntimeError("HTTPClient not initialized. Use async context manager.")
        
        try:
            response = await self.client.post(
                url,
                json=json,
                data=data,
                headers=headers,
                timeout=timeout or self.timeout
            )
            return response
        except HTTPError as e:
            logger.error(f"HTTP POST error: {e}")
            raise
    
    async def put(
        self,
        url: str,
        json: Optional[dict] = None,
        data: Optional[dict] = None,
        headers: Optional[dict] = None,
        timeout: Optional[float] = None
    ):
        """PUT请求"""
        if not self.client:
            raise RuntimeError("HTTPClient not initialized. Use async context manager.")
        
        try:
            response = await self.client.put(
                url,
                json=json,
                data=data,
                headers=headers,
                timeout=timeout or self.timeout
            )
            return response
        except HTTPError as e:
            logger.error(f"HTTP PUT error: {e}")
            raise
    
    async def delete(
        self,
        url: str,
        headers: Optional[dict] = None,
        timeout: Optional[float] = None
    ):
        """DELETE请求"""
        if not self.client:
            raise RuntimeError("HTTPClient not initialized. Use async context manager.")
        
        try:
            response = await self.client.delete(
                url,
                headers=headers,
                timeout=timeout or self.timeout
            )
            return response
        except HTTPError as e:
            logger.error(f"HTTP DELETE error: {e}")
            raise
    
    async def patch(
        self,
        url: str,
        json: Optional[dict] = None,
        data: Optional[dict] = None,
        headers: Optional[dict] = None,
        timeout: Optional[float] = None
    ):
        """PATCH请求"""
        if not self.client:
            raise RuntimeError("HTTPClient not initialized. Use async context manager.")
        
        try:
            response = await self.client.patch(
                url,
                json=json,
                data=data,
                headers=headers,
                timeout=timeout or self.timeout
            )
            return response
        except HTTPError as e:
            logger.error(f"HTTP PATCH error: {e}")
            raise
