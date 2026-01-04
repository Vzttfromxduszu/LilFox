"""配置管理器"""

from typing import Dict, Any, Optional, Type, TypeVar
from pathlib import Path
import os
import json
from .base_config import BaseConfig
from .environment import Environment, get_environment, load_env_config
from .validator import ConfigValidator, CompositeValidator, ValidationError


T = TypeVar('T', bound=BaseConfig)


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent
        self.configs: Dict[str, BaseConfig] = {}
        self.validators: Dict[str, ConfigValidator] = {}
        self.environment = get_environment()
    
    def load_environment(self, env: Optional[Environment] = None):
        """加载环境配置"""
        if env:
            self.environment = env
        load_env_config(self.environment)
    
    def register_config(self, name: str, config_class: Type[T], **kwargs) -> T:
        """注册配置类"""
        config = config_class(**kwargs)
        self.configs[name] = config
        return config
    
    def register_validator(self, config_name: str, validator: ConfigValidator):
        """注册配置验证器"""
        self.validators[config_name] = validator
    
    def get_config(self, name: str) -> Optional[BaseConfig]:
        """获取配置"""
        return self.configs.get(name)
    
    def get_all_configs(self) -> Dict[str, BaseConfig]:
        """获取所有配置"""
        return self.configs.copy()
    
    def validate_config(self, name: str) -> bool:
        """验证指定配置"""
        config = self.configs.get(name)
        if not config:
            return False
        
        if name in self.validators:
            return self.validators[name].validate(config.get_config_dict())
        
        return config.validate_config()
    
    def validate_all_configs(self) -> Dict[str, bool]:
        """验证所有配置"""
        results = {}
        for name in self.configs:
            results[name] = self.validate_config(name)
        return results
    
    def get_validation_errors(self, name: str) -> list[ValidationError]:
        """获取验证错误"""
        if name in self.validators:
            return self.validators[name].get_errors()
        return []
    
    def reload_config(self, name: str) -> bool:
        """重新加载配置"""
        config = self.configs.get(name)
        if not config:
            return False
        
        config_class = type(config)
        new_config = config_class()
        self.configs[name] = new_config
        return True
    
    def reload_all_configs(self) -> Dict[str, bool]:
        """重新加载所有配置"""
        results = {}
        for name in self.configs:
            results[name] = self.reload_config(name)
        return results
    
    def export_config(self, name: str, format: str = "json") -> str:
        """导出配置"""
        config = self.configs.get(name)
        if not config:
            return ""
        
        if format == "json":
            return config.get_config_json()
        elif format == "dict":
            return str(config.get_config_dict())
        else:
            return ""
    
    def export_all_configs(self, format: str = "json") -> Dict[str, str]:
        """导出所有配置"""
        results = {}
        for name in self.configs:
            results[name] = self.export_config(name, format)
        return results
    
    def save_config_to_file(self, name: str, file_path: str, format: str = "json"):
        """保存配置到文件"""
        config = self.configs.get(name)
        if not config:
            return False
        
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "json":
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(config.get_config_json())
        elif format == "env":
            with open(file_path, 'w', encoding='utf-8') as f:
                config_dict = config.get_config_dict()
                for key, value in config_dict.items():
                    if isinstance(value, (list, dict)):
                        value = json.dumps(value)
                    f.write(f"{key}={value}\n")
        else:
            return False
        
        return True
    
    def load_config_from_file(self, name: str, file_path: str, config_class: Type[T]) -> bool:
        """从文件加载配置"""
        file_path = Path(file_path)
        if not file_path.exists():
            return False
        
        if file_path.suffix == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            config = config_class(**config_data)
        elif file_path.suffix == '.env':
            config_data = {}
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config_data[key] = value
            config = config_class(**config_data)
        else:
            return False
        
        self.configs[name] = config
        return True
    
    def get_service_urls(self) -> Dict[str, str]:
        """获取所有服务URL"""
        urls = {}
        
        gateway_config = self.configs.get("gateway")
        if gateway_config:
            urls["gateway"] = f"http://{gateway_config.GATEWAY_HOST}:{gateway_config.GATEWAY_PORT}"
        
        backend_config = self.configs.get("backend")
        if backend_config:
            urls["backend"] = f"http://{backend_config.API_HOST}:{backend_config.API_PORT}"
        
        model_service_config = self.configs.get("model_service")
        if model_service_config:
            urls["model_service"] = f"http://{model_service_config.API_HOST}:{model_service_config.API_PORT}"
        
        return urls
    
    def get_environment_info(self) -> Dict[str, Any]:
        """获取环境信息"""
        return {
            "environment": self.environment.value,
            "is_production": self.environment.is_production(),
            "is_development": self.environment.is_development(),
            "is_staging": self.environment.is_staging(),
            "configs": list(self.configs.keys()),
            "service_urls": self.get_service_urls(),
        }


_global_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigManager()
    return _global_config_manager


def init_configs() -> ConfigManager:
    """初始化所有配置"""
    manager = get_config_manager()
    
    from .gateway_config import gateway_config
    from .backend_config import backend_config
    from .model_service_config import model_service_config
    
    manager.configs["gateway"] = gateway_config
    manager.configs["backend"] = backend_config
    manager.configs["model_service"] = model_service_config
    
    return manager
