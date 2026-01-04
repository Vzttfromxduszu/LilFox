"""基础配置类"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic_settings import BaseSettings
from pydantic import field_validator
import json
import os


class BaseConfig(BaseSettings, ABC):
    """基础配置类，所有配置类的父类"""
    
    # 环境配置
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # 应用基础信息
    APP_NAME: str = "LilFox"
    VERSION: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"
    
    @abstractmethod
    def get_service_name(self) -> str:
        """获取服务名称"""
        pass
    
    @abstractmethod
    def get_service_port(self) -> int:
        """获取服务端口"""
        pass
    
    @abstractmethod
    def get_service_host(self) -> str:
        """获取服务主机"""
        pass
    
    def is_production(self) -> bool:
        """判断是否为生产环境"""
        return self.ENVIRONMENT.lower() == "production"
    
    def is_development(self) -> bool:
        """判断是否为开发环境"""
        return self.ENVIRONMENT.lower() == "development"
    
    def is_staging(self) -> bool:
        """判断是否为预发布环境"""
        return self.ENVIRONMENT.lower() == "staging"
    
    @field_validator('ENVIRONMENT', mode='before')
    @classmethod
    def normalize_environment(cls, v):
        """规范化环境名称"""
        if isinstance(v, str):
            return v.lower()
        return v
    
    @classmethod
    def parse_list_field(cls, value: Any) -> List[str]:
        """解析列表字段"""
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return [item.strip() for item in value.split(',')]
        return []
    
    @classmethod
    def parse_dict_field(cls, value: Any) -> Dict[str, Any]:
        """解析字典字段"""
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def get_config_dict(self) -> Dict[str, Any]:
        """获取配置字典"""
        return self.model_dump()
    
    def get_config_json(self) -> str:
        """获取配置JSON字符串"""
        return self.model_dump_json()
    
    def update_config(self, **kwargs):
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def validate_config(self) -> bool:
        """验证配置"""
        try:
            self.model_validate(self.get_config_dict())
            return True
        except Exception as e:
            print(f"配置验证失败: {e}")
            return False
