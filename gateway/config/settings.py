from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Dict, List, Optional, Any
import json
import os


class Settings(BaseSettings):
    """网关配置类"""
    
    # 应用配置
    APP_NAME: str = "LilFox API Gateway"
    VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    # 网关配置
    GATEWAY_HOST: str = "0.0.0.0"
    GATEWAY_PORT: int = 8080
    GATEWAY_PREFIX: str = "/api"
    
    # 服务发现配置
    SERVICE_DISCOVERY_ENABLED: bool = True
    SERVICE_REGISTRY_TYPE: str = "memory"  # memory, redis, etcd
    SERVICE_HEALTH_CHECK_INTERVAL: int = 30  # 秒
    SERVICE_HEALTH_CHECK_TIMEOUT: int = 5  # 秒
    
    # 负载均衡配置
    LOAD_BALANCER_STRATEGY: str = "round_robin"  # round_robin, random, least_connections
    LOAD_BALANCER_RETRY_COUNT: int = 3
    LOAD_BALANCER_RETRY_DELAY: float = 0.5  # 秒
    
    # 认证配置
    AUTH_ENABLED: bool = True
    AUTH_TYPE: str = "jwt"  # jwt, api_key, oauth2
    JWT_SECRET_KEY: str = "your-secret-key-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    API_KEY_HEADER: str = "X-API-Key"
    
    # 限流配置
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_STRATEGY: str = "token_bucket"  # token_bucket, leaky_bucket, fixed_window
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 100
    RATE_LIMIT_BURST_SIZE: int = 10
    
    # 熔断器配置
    CIRCUIT_BREAKER_ENABLED: bool = True
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_SUCCESS_THRESHOLD: int = 2
    CIRCUIT_BREAKER_TIMEOUT: int = 60  # 秒
    CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS: int = 3
    
    # 超时配置
    REQUEST_TIMEOUT: int = 30  # 秒
    CONNECT_TIMEOUT: int = 5  # 秒
    READ_TIMEOUT: int = 25  # 秒
    
    # 重试配置
    RETRY_ENABLED: bool = True
    RETRY_MAX_ATTEMPTS: int = 3
    RETRY_BACKOFF_FACTOR: float = 0.5
    RETRY_STATUS_CODES: List[int] = [500, 502, 503, 504]
    
    # CORS 配置
    CORS_ENABLED: bool = True
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json, text
    LOG_FILE: Optional[str] = None
    LOG_MAX_BYTES: int = 10485760  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # 监控配置
    METRICS_ENABLED: bool = True
    METRICS_PORT: int = 9090
    METRICS_PATH: str = "/metrics"
    
    # 缓存配置
    CACHE_ENABLED: bool = True
    CACHE_TYPE: str = "memory"  # memory, redis
    CACHE_TTL: int = 300  # 秒
    CACHE_MAX_SIZE: int = 1000
    
    # 转换配置
    TRANSFORM_ENABLED: bool = True
    TRANSFORM_REQUEST_ENABLED: bool = True
    TRANSFORM_RESPONSE_ENABLED: bool = True
    
    # 健康检查配置
    HEALTH_CHECK_ENABLED: bool = True
    HEALTH_CHECK_PATH: str = "/health"
    
    # 默认后端服务
    DEFAULT_BACKENDS: Dict[str, Any] = {
        "auth": {
            "name": "auth-service",
            "url": "http://localhost:8000",
            "health_check": "/",
            "weight": 1,
            "enabled": True
        },
        "model": {
            "name": "model-service",
            "url": "http://localhost:8001",
            "health_check": "/",
            "weight": 1,
            "enabled": True
        }
    }
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"
    
    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(',')]
        return v
    
    @field_validator('DEFAULT_BACKENDS', mode='before')
    @classmethod
    def parse_default_backends(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v
    
    def is_production(self) -> bool:
        """判断是否为生产环境"""
        return not self.DEBUG
    
    def is_development(self) -> bool:
        """判断是否为开发环境"""
        return self.DEBUG


settings = Settings()
