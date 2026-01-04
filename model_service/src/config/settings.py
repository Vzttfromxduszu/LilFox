from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Dict, Any, Optional, List, Union
import os
import json


class Settings(BaseSettings):
    # 应用基础配置
    APP_NAME: str = "LilFox Model Service"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
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
    
    # 其他模型配置
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_BASE_URL: str = "https://api.anthropic.com"
    ANTHROPIC_MODEL: str = "claude-3-sonnet-20240229"
    
    # 默认模型配置
    DEFAULT_MODEL_PROVIDER: str = "openai"  # openai, anthropic, etc.
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = None
    
    # 安全配置
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost", "http://localhost:3000", "http://localhost:5173", "http://localhost:8000"]
    
    # 缓存配置
    CACHE_TTL: int = 3600  # 缓存时间(秒)
    ENABLE_CACHE: bool = True
    
    # 请求限制
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # 提示词配置
    PROMPT_TEMPLATES_DIR: str = "src/prompts/templates"
    
    # 响应解析配置
    RESPONSE_PARSER_TIMEOUT: int = 10
    
    # 环境配置
    ENVIRONMENT: str = "development"  # development, staging, production
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(',')]
        return v
        
    def get_model_config(self, provider: str) -> Dict[str, Any]:
        """获取指定模型提供商的配置"""
        if provider.lower() == "openai":
            return {
                "api_key": self.OPENAI_API_KEY,
                "base_url": self.OPENAI_BASE_URL,
                "model": self.OPENAI_MODEL,
                "temperature": self.OPENAI_TEMPERATURE,
                "max_tokens": self.OPENAI_MAX_TOKENS,
                "timeout": self.OPENAI_TIMEOUT,
            }
        elif provider.lower() == "anthropic":
            return {
                "api_key": self.ANTHROPIC_API_KEY,
                "base_url": self.ANTHROPIC_BASE_URL,
                "model": self.ANTHROPIC_MODEL,
                "timeout": self.OPENAI_TIMEOUT,
            }
        else:
            raise ValueError(f"不支持的模型提供商: {provider}")
    
    def is_production(self) -> bool:
        """判断是否为生产环境"""
        return self.ENVIRONMENT.lower() == "production"
    
    def is_development(self) -> bool:
        """判断是否为开发环境"""
        return self.ENVIRONMENT.lower() == "development"


settings = Settings()