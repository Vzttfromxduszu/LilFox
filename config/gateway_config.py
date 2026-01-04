"""网关配置"""

from ..base_config import BaseConfig
from ..validator import RequiredFieldValidator, TypeValidator, RangeValidator, URLValidator, CompositeValidator
from typing import Dict, List, Optional, Any


class GatewayConfig(BaseConfig):
    """网关配置类"""
    
    # 应用配置
    APP_NAME: str = "LilFox API Gateway"
    VERSION: str = "2.0.0"
    
    # 网关配置
    GATEWAY_HOST: str = "0.0.0.0"
    GATEWAY_PORT: int = 8080
    GATEWAY_PREFIX: str = "/api"
    
    # 服务发现配置
    SERVICE_DISCOVERY_ENABLED: bool = True
    SERVICE_REGISTRY_TYPE: str = "memory"
    SERVICE_HEALTH_CHECK_INTERVAL: int = 30
    SERVICE_HEALTH_CHECK_TIMEOUT: int = 5
    
    # 负载均衡配置
    LOAD_BALANCER_STRATEGY: str = "round_robin"
    LOAD_BALANCER_RETRY_COUNT: int = 3
    LOAD_BALANCER_RETRY_DELAY: float = 0.5
    
    # 认证配置
    AUTH_ENABLED: bool = True
    AUTH_TYPE: str = "jwt"
    JWT_SECRET_KEY: str = "your-secret-key-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    API_KEY_HEADER: str = "X-API-Key"
    
    # 限流配置
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_STRATEGY: str = "token_bucket"
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 100
    RATE_LIMIT_BURST_SIZE: int = 10
    
    # 熔断器配置
    CIRCUIT_BREAKER_ENABLED: bool = True
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_SUCCESS_THRESHOLD: int = 2
    CIRCUIT_BREAKER_TIMEOUT: int = 60
    CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS: int = 3
    
    # 超时配置
    REQUEST_TIMEOUT: int = 30
    CONNECT_TIMEOUT: int = 5
    READ_TIMEOUT: int = 25
    
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
    LOG_FORMAT: str = "json"
    LOG_FILE: Optional[str] = None
    LOG_MAX_BYTES: int = 10485760
    LOG_BACKUP_COUNT: int = 5
    
    # 监控配置
    METRICS_ENABLED: bool = True
    METRICS_PORT: int = 9090
    METRICS_PATH: str = "/metrics"
    
    # 缓存配置
    CACHE_ENABLED: bool = True
    CACHE_TYPE: str = "memory"
    CACHE_TTL: int = 300
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
    
    def get_service_name(self) -> str:
        """获取服务名称"""
        return self.APP_NAME
    
    def get_service_port(self) -> int:
        """获取服务端口"""
        return self.GATEWAY_PORT
    
    def get_service_host(self) -> str:
        """获取服务主机"""
        return self.GATEWAY_HOST
    
    def validate_config(self) -> bool:
        """验证配置"""
        validator = CompositeValidator([
            RequiredFieldValidator([
                "GATEWAY_HOST",
                "GATEWAY_PORT",
                "JWT_SECRET_KEY"
            ]),
            TypeValidator({
                "GATEWAY_PORT": int,
                "SERVICE_HEALTH_CHECK_INTERVAL": int,
                "LOAD_BALANCER_RETRY_COUNT": int,
                "RATE_LIMIT_REQUESTS_PER_MINUTE": int,
                "REQUEST_TIMEOUT": int,
                "METRICS_PORT": int,
                "CACHE_TTL": int,
            }),
            RangeValidator({
                "GATEWAY_PORT": {"min": 1, "max": 65535},
                "SERVICE_HEALTH_CHECK_INTERVAL": {"min": 1, "max": 3600},
                "RATE_LIMIT_REQUESTS_PER_MINUTE": {"min": 1, "max": 10000},
                "REQUEST_TIMEOUT": {"min": 1, "max": 300},
                "LOAD_BALANCER_STRATEGY": {"options": ["round_robin", "random", "least_connections"]},
                "RATE_LIMIT_STRATEGY": {"options": ["token_bucket", "leaky_bucket", "fixed_window", "sliding_window"]},
                "AUTH_TYPE": {"options": ["jwt", "api_key", "oauth2"]},
                "SERVICE_REGISTRY_TYPE": {"options": ["memory", "redis", "etcd"]},
                "CACHE_TYPE": {"options": ["memory", "redis"]},
                "LOG_LEVEL": {"options": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]},
                "LOG_FORMAT": {"options": ["json", "text"]},
            }),
            URLValidator([
                "DEFAULT_BACKENDS.auth.url",
                "DEFAULT_BACKENDS.model.url"
            ])
        ])
        
        config = self.get_config_dict()
        return validator.validate(config)


gateway_config = GatewayConfig()
