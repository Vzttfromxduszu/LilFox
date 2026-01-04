"""模型服务配置"""

from ..base_config import BaseConfig
from ..validator import RequiredFieldValidator, TypeValidator, RangeValidator, URLValidator, CompositeValidator
from typing import Dict, Any, Optional, List


class ModelServiceConfig(BaseConfig):
    """模型服务配置类"""
    
    # 应用配置
    APP_NAME: str = "LilFox Model Service"
    VERSION: str = "1.0.0"
    
    # API配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    API_PREFIX: str = "/api/v1"
    
    # OpenAI配置
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_MAX_TOKENS: int = 1000
    OPENAI_TIMEOUT: int = 30
    
    # Anthropic配置
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_BASE_URL: str = "https://api.anthropic.com"
    ANTHROPIC_MODEL: str = "claude-3-sonnet-20240229"
    ANTHROPIC_TIMEOUT: int = 30
    
    # 其他模型配置
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_VERSION: str = "2023-05-15"
    AZURE_OPENAI_DEPLOYMENT: str = ""
    
    # 默认模型配置
    DEFAULT_MODEL_PROVIDER: str = "openai"
    DEFAULT_MODEL_NAME: str = "gpt-3.5-turbo"
    
    # 模型参数配置
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_MAX_TOKENS: int = 1000
    DEFAULT_TOP_P: float = 1.0
    DEFAULT_FREQUENCY_PENALTY: float = 0.0
    DEFAULT_PRESENCE_PENALTY: float = 0.0
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: Optional[str] = None
    LOG_MAX_BYTES: int = 10485760
    LOG_BACKUP_COUNT: int = 5
    
    # 安全配置
    CORS_ORIGINS: List[str] = ["http://localhost", "http://localhost:3000", "http://localhost:5173"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # 缓存配置
    CACHE_TTL: int = 3600
    ENABLE_CACHE: bool = True
    CACHE_TYPE: str = "memory"
    CACHE_MAX_SIZE: int = 1000
    
    # 请求限制
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST_SIZE: int = 10
    
    # 提示词配置
    PROMPT_TEMPLATES_DIR: str = "src/prompts/templates"
    PROMPT_MAX_LENGTH: int = 10000
    
    # 响应解析配置
    RESPONSE_PARSER_TIMEOUT: int = 10
    RESPONSE_MAX_LENGTH: int = 50000
    
    # 流式响应配置
    STREAM_ENABLED: bool = True
    STREAM_CHUNK_SIZE: int = 100
    STREAM_TIMEOUT: int = 60
    
    # 重试配置
    RETRY_ENABLED: bool = True
    RETRY_MAX_ATTEMPTS: int = 3
    RETRY_BACKOFF_FACTOR: float = 0.5
    RETRY_STATUS_CODES: List[int] = [429, 500, 502, 503, 504]
    
    # 监控配置
    METRICS_ENABLED: bool = True
    METRICS_PORT: int = 9092
    METRICS_PATH: str = "/metrics"
    
    # 健康检查配置
    HEALTH_CHECK_ENABLED: bool = True
    HEALTH_CHECK_PATH: str = "/health"
    
    # 成本控制配置
    COST_TRACKING_ENABLED: bool = True
    MAX_DAILY_COST: float = 100.0
    COST_ALERT_THRESHOLD: float = 80.0
    
    def get_service_name(self) -> str:
        """获取服务名称"""
        return self.APP_NAME
    
    def get_service_port(self) -> int:
        """获取服务端口"""
        return self.API_PORT
    
    def get_service_host(self) -> str:
        """获取服务主机"""
        return self.API_HOST
    
    def get_model_config(self, provider: str) -> Dict[str, Any]:
        """获取指定模型提供商的配置"""
        provider = provider.lower()
        
        if provider == "openai":
            return {
                "api_key": self.OPENAI_API_KEY,
                "base_url": self.OPENAI_BASE_URL,
                "model": self.OPENAI_MODEL,
                "temperature": self.OPENAI_TEMPERATURE,
                "max_tokens": self.OPENAI_MAX_TOKENS,
                "timeout": self.OPENAI_TIMEOUT,
            }
        elif provider == "anthropic":
            return {
                "api_key": self.ANTHROPIC_API_KEY,
                "base_url": self.ANTHROPIC_BASE_URL,
                "model": self.ANTHROPIC_MODEL,
                "timeout": self.ANTHROPIC_TIMEOUT,
            }
        elif provider == "azure":
            return {
                "api_key": self.AZURE_OPENAI_API_KEY,
                "endpoint": self.AZURE_OPENAI_ENDPOINT,
                "api_version": self.AZURE_OPENAI_API_VERSION,
                "deployment": self.AZURE_OPENAI_DEPLOYMENT,
                "timeout": self.OPENAI_TIMEOUT,
            }
        else:
            raise ValueError(f"不支持的模型提供商: {provider}")
    
    def get_available_providers(self) -> List[str]:
        """获取可用的模型提供商列表"""
        providers = []
        
        if self.OPENAI_API_KEY:
            providers.append("openai")
        
        if self.ANTHROPIC_API_KEY:
            providers.append("anthropic")
        
        if self.AZURE_OPENAI_API_KEY and self.AZURE_OPENAI_ENDPOINT:
            providers.append("azure")
        
        return providers
    
    def validate_config(self) -> bool:
        """验证配置"""
        validator = CompositeValidator([
            RequiredFieldValidator([
                "API_HOST",
                "API_PORT",
                "DEFAULT_MODEL_PROVIDER"
            ]),
            TypeValidator({
                "API_PORT": int,
                "OPENAI_MAX_TOKENS": int,
                "OPENAI_TIMEOUT": int,
                "ANTHROPIC_TIMEOUT": int,
                "DEFAULT_TEMPERATURE": float,
                "DEFAULT_MAX_TOKENS": int,
                "DEFAULT_TOP_P": float,
                "CACHE_TTL": int,
                "PROMPT_MAX_LENGTH": int,
                "RESPONSE_PARSER_TIMEOUT": int,
                "RESPONSE_MAX_LENGTH": int,
                "STREAM_CHUNK_SIZE": int,
                "STREAM_TIMEOUT": int,
            }),
            RangeValidator({
                "API_PORT": {"min": 1, "max": 65535},
                "OPENAI_MAX_TOKENS": {"min": 1, "max": 100000},
                "OPENAI_TIMEOUT": {"min": 1, "max": 300},
                "DEFAULT_TEMPERATURE": {"min": 0.0, "max": 2.0},
                "DEFAULT_MAX_TOKENS": {"min": 1, "max": 100000},
                "DEFAULT_TOP_P": {"min": 0.0, "max": 1.0},
                "CACHE_TTL": {"min": 1, "max": 86400},
                "PROMPT_MAX_LENGTH": {"min": 100, "max": 100000},
                "RESPONSE_MAX_LENGTH": {"min": 100, "max": 1000000},
                "STREAM_CHUNK_SIZE": {"min": 10, "max": 10000},
                "STREAM_TIMEOUT": {"min": 1, "max": 300},
                "DEFAULT_MODEL_PROVIDER": {"options": ["openai", "anthropic", "azure"]},
                "LOG_LEVEL": {"options": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]},
                "LOG_FORMAT": {"options": ["json", "text"]},
                "CACHE_TYPE": {"options": ["memory", "redis"]},
            }),
            URLValidator([
                "OPENAI_BASE_URL",
                "ANTHROPIC_BASE_URL",
                "AZURE_OPENAI_ENDPOINT"
            ])
        ])
        
        config = self.get_config_dict()
        return validator.validate(config)


model_service_config = ModelServiceConfig()
