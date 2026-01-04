from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class Message(BaseModel):
    """消息模型"""
    role: str = Field(..., description="消息角色: system, user, assistant")
    content: str = Field(..., description="消息内容")


class ChatRequest(BaseModel):
    """聊天请求模型"""
    messages: List[Message] = Field(..., description="消息列表")
    provider: Optional[str] = Field(None, description="模型提供商: openai, anthropic")
    parse_format: Optional[str] = Field(None, description="响应解析格式: json, code, list, key_value, markdown, text")
    temperature: Optional[float] = Field(None, description="温度参数，控制随机性")
    max_tokens: Optional[int] = Field(None, description="最大生成token数")


class CompletionRequest(BaseModel):
    """文本补全请求模型"""
    prompt: str = Field(..., description="提示词")
    provider: Optional[str] = Field(None, description="模型提供商")
    parse_format: Optional[str] = Field(None, description="响应解析格式")
    temperature: Optional[float] = Field(None, description="温度参数")
    max_tokens: Optional[int] = Field(None, description="最大生成token数")


class TemplateChatRequest(BaseModel):
    """模板聊天请求模型"""
    template_name: str = Field(..., description="模板名称")
    template_params: Dict[str, Any] = Field(..., description="模板参数")
    provider: Optional[str] = Field(None, description="模型提供商")
    parse_format: Optional[str] = Field(None, description="响应解析格式")
    temperature: Optional[float] = Field(None, description="温度参数")
    max_tokens: Optional[int] = Field(None, description="最大生成token数")


class TemplateRegisterRequest(BaseModel):
    """模板注册请求模型"""
    name: str = Field(..., description="模板名称")
    template: str = Field(..., description="模板内容")
    description: Optional[str] = Field("", description="模板描述")
    parameters: Optional[Dict[str, Any]] = Field(None, description="模板参数")


class ParseRequest(BaseModel):
    """响应解析请求模型"""
    content: str = Field(..., description="待解析的内容")
    format_type: Optional[str] = Field(None, description="解析格式，不提供则自动检测")


class ModelResponse(BaseModel):
    """模型响应模型"""
    content: str = Field(..., description="响应内容")
    model: str = Field(..., description="使用的模型")
    usage: Optional[Dict[str, int]] = Field(None, description="使用情况")
    finish_reason: Optional[str] = Field(None, description="完成原因")


class ParsedResponse(BaseModel):
    """解析响应模型"""
    success: bool = Field(..., description="是否解析成功")
    data: Any = Field(None, description="解析后的数据")
    error: Optional[str] = Field(None, description="错误信息")
    raw_content: Optional[str] = Field(None, description="原始内容")


class TemplateInfo(BaseModel):
    """模板信息模型"""
    name: str = Field(..., description="模板名称")
    description: str = Field(..., description="模板描述")
    required_parameters: List[str] = Field(..., description="必需参数列表")
    parameters: Dict[str, Any] = Field(..., description="所有参数")


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="服务版本")
    models_available: List[str] = Field(..., description="可用的模型列表")
    templates_available: List[str] = Field(..., description="可用的模板列表")