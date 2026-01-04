"""配置验证器"""

from typing import Dict, Any, List, Optional, Callable
from abc import ABC, abstractmethod


class ValidationError(Exception):
    """配置验证错误"""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"Validation error for field '{field}': {message}")


class ConfigValidator(ABC):
    """配置验证器基类"""
    
    def __init__(self):
        self.errors: List[ValidationError] = []
    
    @abstractmethod
    def validate(self, config: Dict[str, Any]) -> bool:
        """验证配置"""
        pass
    
    def add_error(self, field: str, message: str):
        """添加验证错误"""
        self.errors.append(ValidationError(field, message))
    
    def get_errors(self) -> List[ValidationError]:
        """获取所有错误"""
        return self.errors
    
    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.errors) > 0
    
    def clear_errors(self):
        """清除错误"""
        self.errors.clear()


class RequiredFieldValidator(ConfigValidator):
    """必填字段验证器"""
    
    def __init__(self, required_fields: List[str]):
        super().__init__()
        self.required_fields = required_fields
    
    def validate(self, config: Dict[str, Any]) -> bool:
        """验证必填字段"""
        self.clear_errors()
        
        for field in self.required_fields:
            if field not in config or config[field] is None or config[field] == "":
                self.add_error(field, "字段为必填项")
        
        return not self.has_errors()


class TypeValidator(ConfigValidator):
    """类型验证器"""
    
    def __init__(self, field_types: Dict[str, type]):
        super().__init__()
        self.field_types = field_types
    
    def validate(self, config: Dict[str, Any]) -> bool:
        """验证字段类型"""
        self.clear_errors()
        
        for field, expected_type in self.field_types.items():
            if field in config:
                value = config[field]
                if not isinstance(value, expected_type):
                    self.add_error(field, f"期望类型 {expected_type.__name__}, 实际类型 {type(value).__name__}")
        
        return not self.has_errors()


class RangeValidator(ConfigValidator):
    """范围验证器"""
    
    def __init__(self, field_ranges: Dict[str, Dict[str, Any]]):
        super().__init__()
        self.field_ranges = field_ranges
    
    def validate(self, config: Dict[str, Any]) -> bool:
        """验证字段范围"""
        self.clear_errors()
        
        for field, range_config in self.field_ranges.items():
            if field in config:
                value = config[field]
                
                if "min" in range_config and value < range_config["min"]:
                    self.add_error(field, f"值不能小于 {range_config['min']}")
                
                if "max" in range_config and value > range_config["max"]:
                    self.add_error(field, f"值不能大于 {range_config['max']}")
                
                if "options" in range_config and value not in range_config["options"]:
                    self.add_error(field, f"值必须是以下之一: {range_config['options']}")
        
        return not self.has_errors()


class URLValidator(ConfigValidator):
    """URL验证器"""
    
    def __init__(self, url_fields: List[str]):
        super().__init__()
        self.url_fields = url_fields
    
    def validate(self, config: Dict[str, Any]) -> bool:
        """验证URL格式"""
        self.clear_errors()
        
        from urllib.parse import urlparse
        
        for field in self.url_fields:
            if field in config:
                url = config[field]
                try:
                    result = urlparse(url)
                    if not all([result.scheme, result.netloc]):
                        self.add_error(field, "URL格式不正确")
                except Exception:
                    self.add_error(field, "URL格式不正确")
        
        return not self.has_errors()


class CustomValidator(ConfigValidator):
    """自定义验证器"""
    
    def __init__(self, validators: Dict[str, Callable[[Any], bool]]):
        super().__init__()
        self.validators = validators
    
    def validate(self, config: Dict[str, Any]) -> bool:
        """执行自定义验证"""
        self.clear_errors()
        
        for field, validator_func in self.validators.items():
            if field in config:
                try:
                    if not validator_func(config[field]):
                        self.add_error(field, "自定义验证失败")
                except Exception as e:
                    self.add_error(field, f"验证错误: {str(e)}")
        
        return not self.has_errors()


class CompositeValidator(ConfigValidator):
    """组合验证器"""
    
    def __init__(self, validators: List[ConfigValidator]):
        super().__init__()
        self.validators = validators
    
    def validate(self, config: Dict[str, Any]) -> bool:
        """执行所有验证器"""
        self.clear_errors()
        
        all_valid = True
        for validator in self.validators:
            if not validator.validate(config):
                all_valid = False
                self.errors.extend(validator.get_errors())
        
        return all_valid
