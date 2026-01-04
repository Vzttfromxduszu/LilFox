from typing import Dict, Any, Optional, Callable, List
from fastapi import Request, Response
import json
import re

from ..monitoring.logger import get_logger

logger = get_logger(__name__)


class RequestTransformer:
    """请求转换器"""
    
    def __init__(self):
        self.transformers: Dict[str, Callable] = {}
        self.global_transformers: List[Callable] = []
    
    def add_transformer(
        self,
        name: str,
        transformer: Callable[[Request], Request]
    ):
        """添加转换器"""
        self.transformers[name] = transformer
        logger.info(f"Added request transformer: {name}")
    
    def add_global_transformer(self, transformer: Callable[[Request], Request]):
        """添加全局转换器"""
        self.global_transformers.append(transformer)
        logger.info("Added global request transformer")
    
    def remove_transformer(self, name: str):
        """移除转换器"""
        if name in self.transformers:
            del self.transformers[name]
            logger.info(f"Removed request transformer: {name}")
    
    async def transform(
        self,
        request: Request,
        transformer_names: Optional[List[str]] = None
    ) -> Request:
        """转换请求"""
        try:
            transformed_request = request
            
            for transformer in self.global_transformers:
                transformed_request = await transformer(transformed_request)
            
            if transformer_names:
                for name in transformer_names:
                    if name in self.transformers:
                        transformed_request = await self.transformers[name](transformed_request)
            
            return transformed_request
            
        except Exception as e:
            logger.error(f"Error transforming request: {e}")
            return request
    
    async def add_headers(
        self,
        request: Request,
        headers: Dict[str, str]
    ) -> Request:
        """添加请求头"""
        request.state.extra_headers = headers
        return request
    
    async def remove_headers(
        self,
        request: Request,
        header_names: List[str]
    ) -> Request:
        """移除请求头"""
        if not hasattr(request.state, 'remove_headers'):
            request.state.remove_headers = []
        request.state.remove_headers.extend(header_names)
        return request
    
    async def replace_headers(
        self,
        request: Request,
        headers: Dict[str, str]
    ) -> Request:
        """替换请求头"""
        if not hasattr(request.state, 'replace_headers'):
            request.state.replace_headers = {}
        request.state.replace_headers.update(headers)
        return request
    
    async def modify_path(
        self,
        request: Request,
        path: str
    ) -> Request:
        """修改路径"""
        request.state.modified_path = path
        return request
    
    async def modify_query_params(
        self,
        request: Request,
        params: Dict[str, Any]
    ) -> Request:
        """修改查询参数"""
        if not hasattr(request.state, 'modify_query_params'):
            request.state.modify_query_params = {}
        request.state.modify_query_params.update(params)
        return request
    
    async def modify_body(
        self,
        request: Request,
        body: Dict[str, Any]
    ) -> Request:
        """修改请求体"""
        request.state.modified_body = body
        return request
    
    async def mask_sensitive_data(
        self,
        request: Request,
        fields: List[str]
    ) -> Request:
        """脱敏敏感数据"""
        try:
            body = await request.json()
            
            for field in fields:
                if field in body:
                    body[field] = "******"
            
            request.state.modified_body = body
            return request
            
        except Exception as e:
            logger.error(f"Error masking sensitive data: {e}")
            return request
    
    async def validate_schema(
        self,
        request: Request,
        schema: Dict[str, Any]
    ) -> Request:
        """验证请求模式"""
        try:
            body = await request.json()
            
            for field, field_type in schema.items():
                if field not in body:
                    continue
                
                if field_type == "string" and not isinstance(body[field], str):
                    body[field] = str(body[field])
                elif field_type == "int" and not isinstance(body[field], int):
                    body[field] = int(body[field])
                elif field_type == "float" and not isinstance(body[field], float):
                    body[field] = float(body[field])
                elif field_type == "bool" and not isinstance(body[field], bool):
                    body[field] = bool(body[field])
            
            request.state.modified_body = body
            return request
            
        except Exception as e:
            logger.error(f"Error validating schema: {e}")
            return request


class ResponseTransformer:
    """响应转换器"""
    
    def __init__(self):
        self.transformers: Dict[str, Callable] = {}
        self.global_transformers: List[Callable] = []
    
    def add_transformer(
        self,
        name: str,
        transformer: Callable[[Response], Response]
    ):
        """添加转换器"""
        self.transformers[name] = transformer
        logger.info(f"Added response transformer: {name}")
    
    def add_global_transformer(self, transformer: Callable[[Response], Response]):
        """添加全局转换器"""
        self.global_transformers.append(transformer)
        logger.info("Added global response transformer")
    
    def remove_transformer(self, name: str):
        """移除转换器"""
        if name in self.transformers:
            del self.transformers[name]
            logger.info(f"Removed response transformer: {name}")
    
    async def transform(
        self,
        response: Response,
        transformer_names: Optional[List[str]] = None
    ) -> Response:
        """转换响应"""
        try:
            transformed_response = response
            
            for transformer in self.global_transformers:
                transformed_response = await transformer(transformed_response)
            
            if transformer_names:
                for name in transformer_names:
                    if name in self.transformers:
                        transformed_response = await self.transformers[name](transformed_response)
            
            return transformed_response
            
        except Exception as e:
            logger.error(f"Error transforming response: {e}")
            return response
    
    async def add_headers(
        self,
        response: Response,
        headers: Dict[str, str]
    ) -> Response:
        """添加响应头"""
        for key, value in headers.items():
            response.headers[key] = value
        return response
    
    async def remove_headers(
        self,
        response: Response,
        header_names: List[str]
    ) -> Response:
        """移除响应头"""
        for name in header_names:
            if name in response.headers:
                del response.headers[name]
        return response
    
    async def replace_headers(
        self,
        response: Response,
        headers: Dict[str, str]
    ) -> Response:
        """替换响应头"""
        for key, value in headers.items():
            response.headers[key] = value
        return response
    
    async def modify_body(
        self,
        response: Response,
        body: Dict[str, Any]
    ) -> Response:
        """修改响应体"""
        response.body = json.dumps(body).encode()
        response.headers["content-length"] = str(len(response.body))
        return response
    
    async def mask_sensitive_data(
        self,
        response: Response,
        fields: List[str]
    ) -> Response:
        """脱敏敏感数据"""
        try:
            if response.headers.get("content-type", "").startswith("application/json"):
                body = json.loads(response.body.decode())
                
                def mask_fields(data):
                    if isinstance(data, dict):
                        return {
                            k: mask_fields(v) if k not in fields else "******"
                            for k, v in data.items()
                        }
                    elif isinstance(data, list):
                        return [mask_fields(item) for item in data]
                    else:
                        return data
                
                masked_body = mask_fields(body)
                response.body = json.dumps(masked_body).encode()
                response.headers["content-length"] = str(len(response.body))
            
            return response
            
        except Exception as e:
            logger.error(f"Error masking sensitive data in response: {e}")
            return response
    
    async def compress_response(
        self,
        response: Response
    ) -> Response:
        """压缩响应"""
        try:
            import gzip
            
            if len(response.body) > 1024:
                compressed = gzip.compress(response.body)
                response.body = compressed
                response.headers["content-encoding"] = "gzip"
                response.headers["content-length"] = str(len(compressed))
            
            return response
            
        except Exception as e:
            logger.error(f"Error compressing response: {e}")
            return response
    
    async def add_cors_headers(
        self,
        response: Response,
        origins: List[str],
        methods: List[str],
        headers: List[str]
    ) -> Response:
        """添加CORS头"""
        response.headers["Access-Control-Allow-Origin"] = ", ".join(origins)
        response.headers["Access-Control-Allow-Methods"] = ", ".join(methods)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(headers)
        response.headers["Access-Control-Max-Age"] = "86400"
        return response
    
    async def standardize_response(
        self,
        response: Response
    ) -> Response:
        """标准化响应格式"""
        try:
            if response.headers.get("content-type", "").startswith("application/json"):
                body = json.loads(response.body.decode())
                
                if not isinstance(body, dict) or "data" not in body:
                    standardized = {
                        "success": response.status_code < 400,
                        "status": response.status_code,
                        "data": body if not isinstance(body, dict) else body,
                        "message": "OK" if response.status_code < 400 else "Error",
                        "timestamp": None
                    }
                    
                    response.body = json.dumps(standardized).encode()
                    response.headers["content-length"] = str(len(response.body))
            
            return response
            
        except Exception as e:
            logger.error(f"Error standardizing response: {e}")
            return response
    
    async def add_version_header(
        self,
        response: Response,
        version: str
    ) -> Response:
        """添加版本头"""
        response.headers["X-API-Version"] = version
        return response
    
    async def add_request_id(
        self,
        response: Response,
        request_id: str
    ) -> Response:
        """添加请求ID"""
        response.headers["X-Request-ID"] = request_id
        return response
    
    async def add_timing_info(
        self,
        response: Response,
        duration_ms: float
    ) -> Response:
        """添加计时信息"""
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        return response
