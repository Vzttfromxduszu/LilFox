"""后端服务配置"""

from ..base_config import BaseConfig
from ..validator import RequiredFieldValidator, TypeValidator, RangeValidator, URLValidator, CompositeValidator
from typing import List, Optional


class BackendConfig(BaseConfig):
    """后端服务配置类"""
    
    # 应用配置
    APP_NAME: str = "LilFox Backend Service"
    VERSION: str = "1.0.0"
    
    # API配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./app.db"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS配置
    CORS_ORIGINS: List[str] = ["http://localhost", "http://localhost:3000", "http://localhost:5173"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: Optional[str] = None
    LOG_MAX_BYTES: int = 10485760
    LOG_BACKUP_COUNT: int = 5
    
    # 安全配置
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = False
    
    # 用户配置
    USER_DEFAULT_ACTIVE: bool = True
    USER_EMAIL_VERIFICATION: bool = False
    USER_MAX_LOGIN_ATTEMPTS: int = 5
    USER_LOCKOUT_DURATION: int = 30
    
    # 限流配置
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST_SIZE: int = 10
    
    # 缓存配置
    CACHE_ENABLED: bool = True
    CACHE_TYPE: str = "memory"
    CACHE_TTL: int = 300
    CACHE_MAX_SIZE: int = 1000
    
    # 会话配置
    SESSION_ENABLED: bool = True
    SESSION_EXPIRE_MINUTES: int = 60
    SESSION_MAX_AGE: int = 86400
    
    # 监控配置
    METRICS_ENABLED: bool = True
    METRICS_PORT: int = 9091
    METRICS_PATH: str = "/metrics"
    
    # 健康检查配置
    HEALTH_CHECK_ENABLED: bool = True
    HEALTH_CHECK_PATH: str = "/health"
    
    def get_service_name(self) -> str:
        """获取服务名称"""
        return self.APP_NAME
    
    def get_service_port(self) -> int:
        """获取服务端口"""
        return self.API_PORT
    
    def get_service_host(self) -> str:
        """获取服务主机"""
        return self.API_HOST
    
    def validate_config(self) -> bool:
        """验证配置"""
        validator = CompositeValidator([
            RequiredFieldValidator([
                "API_HOST",
                "API_PORT",
                "DATABASE_URL",
                "SECRET_KEY"
            ]),
            TypeValidator({
                "API_PORT": int,
                "ACCESS_TOKEN_EXPIRE_MINUTES": int,
                "REFRESH_TOKEN_EXPIRE_DAYS": int,
                "PASSWORD_MIN_LENGTH": int,
                "USER_MAX_LOGIN_ATTEMPTS": int,
                "USER_LOCKOUT_DURATION": int,
                "RATE_LIMIT_PER_MINUTE": int,
                "CACHE_TTL": int,
            }),
            RangeValidator({
                "API_PORT": {"min": 1, "max": 65535},
                "ACCESS_TOKEN_EXPIRE_MINUTES": {"min": 1, "max": 1440},
                "REFRESH_TOKEN_EXPIRE_DAYS": {"min": 1, "max": 365},
                "PASSWORD_MIN_LENGTH": {"min": 6, "max": 128},
                "USER_MAX_LOGIN_ATTEMPTS": {"min": 1, "max": 100},
                "USER_LOCKOUT_DURATION": {"min": 1, "max": 1440},
                "RATE_LIMIT_PER_MINUTE": {"min": 1, "max": 10000},
                "CACHE_TTL": {"min": 1, "max": 86400},
                "LOG_LEVEL": {"options": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]},
                "LOG_FORMAT": {"options": ["json", "text"]},
                "CACHE_TYPE": {"options": ["memory", "redis"]},
            }),
            URLValidator([
                "DATABASE_URL"
            ])
        ])
        
        config = self.get_config_dict()
        return validator.validate(config)


backend_config = BackendConfig()
