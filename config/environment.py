"""环境管理模块"""

from enum import Enum
from typing import Dict, Any, Optional
import os


class Environment(str, Enum):
    """环境枚举"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"
    
    @classmethod
    def from_string(cls, value: str) -> 'Environment':
        """从字符串创建环境枚举"""
        value = value.lower()
        for env in cls:
            if env.value == value:
                return env
        return cls.DEVELOPMENT
    
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self == self.DEVELOPMENT
    
    def is_staging(self) -> bool:
        """是否为预发布环境"""
        return self == self.STAGING
    
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self == self.PRODUCTION
    
    def is_test(self) -> bool:
        """是否为测试环境"""
        return self == self.TEST


def get_environment() -> Environment:
    """获取当前环境"""
    env_str = os.getenv("ENVIRONMENT", "development")
    return Environment.from_string(env_str)


def get_env_config_path(env: Optional[Environment] = None) -> str:
    """获取环境配置文件路径"""
    if env is None:
        env = get_environment()
    return f".env.{env.value}"


def get_env_config_content(env: Optional[Environment] = None) -> Dict[str, str]:
    """获取环境配置内容"""
    if env is None:
        env = get_environment()
    
    config_path = get_env_config_path(env)
    config = {}
    
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    
    return config


def load_env_config(env: Optional[Environment] = None):
    """加载环境配置到环境变量"""
    if env is None:
        env = get_environment()
    
    config = get_env_config_content(env)
    for key, value in config.items():
        os.environ[key] = value


class EnvironmentConfig:
    """环境配置管理器"""
    
    def __init__(self, env: Optional[Environment] = None):
        self.env = env or get_environment()
        self.config = get_env_config_content(self.env)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: str):
        """设置配置值"""
        self.config[key] = value
    
    def get_all(self) -> Dict[str, str]:
        """获取所有配置"""
        return self.config.copy()
    
    def update(self, config: Dict[str, str]):
        """更新配置"""
        self.config.update(config)
    
    def save(self):
        """保存配置到文件"""
        config_path = get_env_config_path(self.env)
        with open(config_path, 'w', encoding='utf-8') as f:
            for key, value in self.config.items():
                f.write(f"{key}={value}\n")
    
    def switch_environment(self, env: Environment):
        """切换环境"""
        self.env = env
        self.config = get_env_config_content(env)
