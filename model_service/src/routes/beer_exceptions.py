from typing import Optional, Any


class BeerRecommendationError(Exception):
    """精酿啤酒推荐基础异常类"""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        """将异常转换为字典格式"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


class ParameterValidationError(BeerRecommendationError):
    """参数验证错误"""
    
    def __init__(self, field_name: str, field_value: Any, reason: str):
        super().__init__(
            message=f"参数验证失败: {field_name}",
            details={
                "field": field_name,
                "value": field_value,
                "reason": reason
            }
        )


class TemplateNotFoundError(BeerRecommendationError):
    """模板未找到错误"""
    
    def __init__(self, template_name: str):
        super().__init__(
            message=f"未找到提示词模板: {template_name}",
            details={"template_name": template_name}
        )


class TemplateFormatError(BeerRecommendationError):
    """模板格式化错误"""
    
    def __init__(self, template_name: str, missing_params: list):
        super().__init__(
            message=f"模板格式化失败: 缺少必需参数",
            details={
                "template_name": template_name,
                "missing_parameters": missing_params
            }
        )


class LLMServiceError(BeerRecommendationError):
    """大模型服务错误"""
    
    def __init__(self, message: str, provider: Optional[str] = None, original_error: Optional[Exception] = None):
        super().__init__(
            message=f"大模型服务错误: {message}",
            details={
                "provider": provider,
                "original_error": str(original_error) if original_error else None
            }
        )


class ResponseParseError(BeerRecommendationError):
    """响应解析错误"""
    
    def __init__(self, parse_format: str, content: str, reason: str):
        super().__init__(
            message=f"响应解析失败: {reason}",
            details={
                "parse_format": parse_format,
                "content_preview": content[:200] if content else None
            }
        )


class RecommendationGenerationError(BeerRecommendationError):
    """推荐生成错误"""
    
    def __init__(self, user_preferences: dict, reason: str):
        super().__init__(
            message=f"推荐生成失败: {reason}",
            details={
                "user_preferences": user_preferences,
                "reason": reason
            }
        )


class KnowledgeQueryError(BeerRecommendationError):
    """知识查询错误"""
    
    def __init__(self, question: str, reason: str):
        super().__init__(
            message=f"知识查询失败: {reason}",
            details={
                "question": question,
                "reason": reason
            }
        )


class PairingGenerationError(BeerRecommendationError):
    """搭配生成错误"""
    
    def __init__(self, context: dict, reason: str):
        super().__init__(
            message=f"搭配生成失败: {reason}",
            details={
                "context": context,
                "reason": reason
            }
        )


class StyleGuideGenerationError(BeerRecommendationError):
    """风格指南生成错误"""
    
    def __init__(self, beer_style: str, reason: str):
        super().__init__(
            message=f"风格指南生成失败: {reason}",
            details={
                "beer_style": beer_style,
                "reason": reason
            }
        )


def handle_beer_exception(error: Exception) -> BeerRecommendationError:
    """将普通异常转换为精酿啤酒推荐异常"""
    if isinstance(error, BeerRecommendationError):
        return error
    
    if isinstance(error, ValueError):
        return ParameterValidationError("unknown", None, str(error))
    
    if isinstance(error, KeyError):
        return TemplateFormatError("unknown", [str(error)])
    
    return BeerRecommendationError(
        message=f"未知错误: {str(error)}",
        details={"original_error": str(error)}
    )
