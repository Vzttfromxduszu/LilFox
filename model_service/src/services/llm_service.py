from typing import Dict, Any, Optional, List, Union
from ..config.settings import settings
from ..prompts import PromptManager, initialize_prompt_manager
from ..models import BaseLLMModel, Message, ModelResponse, OpenAIModel
from ..parsers import ResponseParser, ParsedResult


class LLMService:
    """大模型服务类，整合所有组件提供统一的服务接口"""
    
    def __init__(self, prompt_manager: Optional[PromptManager] = None):
        """
        初始化LLM服务
        
        Args:
            prompt_manager: 提示词管理器，如果不提供则使用默认的
        """
        self.prompt_manager = prompt_manager or initialize_prompt_manager()
        self.response_parser = ResponseParser()
        self.models: Dict[str, BaseLLMModel] = {}
        self._initialize_models()
    
    def _initialize_models(self) -> None:
        """初始化所有配置的模型"""
        provider = settings.DEFAULT_MODEL_PROVIDER.lower()
        
        if provider == "openai":
            config = settings.get_model_config("openai")
            if config["api_key"]:
                self.models["openai"] = OpenAIModel(config)
        
        # 可以在这里添加其他模型提供商的初始化
        # elif provider == "anthropic":
        #     config = settings.get_model_config("anthropic")
        #     if config["api_key"]:
        #         self.models["anthropic"] = AnthropicModel(config)
    
    def get_model(self, provider: Optional[str] = None) -> BaseLLMModel:
        """
        获取指定提供商的模型
        
        Args:
            provider: 模型提供商名称，如果不提供则使用默认的
            
        Returns:
            BaseLLMModel: 模型实例
            
        Raises:
            ValueError: 如果模型未初始化
        """
        if provider is None:
            provider = settings.DEFAULT_MODEL_PROVIDER.lower()
        
        model = self.models.get(provider)
        if not model:
            raise ValueError(f"模型 {provider} 未初始化，请检查API密钥配置")
        
        return model
    
    def chat(
        self,
        messages: List[Message],
        provider: Optional[str] = None,
        parse_format: Optional[str] = None,
        **kwargs
    ) -> Union[ModelResponse, ParsedResult]:
        """
        聊天接口
        
        Args:
            messages: 消息列表
            provider: 模型提供商
            parse_format: 响应解析格式 (json, code, list, key_value, markdown, text)
            **kwargs: 其他参数
            
        Returns:
            Union[ModelResponse, ParsedResult]: 模型响应或解析结果
        """
        model = self.get_model(provider)
        response = model.chat_completion(messages, **kwargs)
        
        if parse_format:
            return self.response_parser.parse(response.content, parse_format)
        
        return response
    
    def complete(
        self,
        prompt: str,
        provider: Optional[str] = None,
        parse_format: Optional[str] = None,
        **kwargs
    ) -> Union[ModelResponse, ParsedResult]:
        """
        文本补全接口
        
        Args:
            prompt: 提示词
            provider: 模型提供商
            parse_format: 响应解析格式
            **kwargs: 其他参数
            
        Returns:
            Union[ModelResponse, ParsedResult]: 模型响应或解析结果
        """
        model = self.get_model(provider)
        response = model.text_completion(prompt, **kwargs)
        
        if parse_format:
            return self.response_parser.parse(response.content, parse_format)
        
        return response
    
    def chat_with_template(
        self,
        template_name: str,
        template_params: Dict[str, Any],
        provider: Optional[str] = None,
        parse_format: Optional[str] = None,
        **kwargs
    ) -> Union[ModelResponse, ParsedResult]:
        """
        使用模板进行聊天
        
        Args:
            template_name: 模板名称
            template_params: 模板参数
            provider: 模型提供商
            parse_format: 响应解析格式
            **kwargs: 其他参数
            
        Returns:
            Union[ModelResponse, ParsedResult]: 模型响应或解析结果
        """
        prompt = self.prompt_manager.format_template(template_name, **template_params)
        return self.complete(prompt, provider, parse_format, **kwargs)
    
    def stream_chat(
        self,
        messages: List[Message],
        provider: Optional[str] = None,
        **kwargs
    ):
        """
        流式聊天接口
        
        Args:
            messages: 消息列表
            provider: 模型提供商
            **kwargs: 其他参数
            
        Yields:
            str: 生成的文本片段
        """
        model = self.get_model(provider)
        for chunk in model.stream_chat_completion(messages, **kwargs):
            yield chunk
    
    def stream_with_template(
        self,
        template_name: str,
        template_params: Dict[str, Any],
        provider: Optional[str] = None,
        **kwargs
    ):
        """
        使用模板进行流式聊天
        
        Args:
            template_name: 模板名称
            template_params: 模板参数
            provider: 模型提供商
            **kwargs: 其他参数
            
        Yields:
            str: 生成的文本片段
        """
        prompt = self.prompt_manager.format_template(template_name, **template_params)
        model = self.get_model(provider)
        messages = [model.create_user_message(prompt)]
        for chunk in model.stream_chat_completion(messages, **kwargs):
            yield chunk
    
    def register_template(self, name: str, template: str, description: str = "", **kwargs) -> None:
        """
        注册自定义提示词模板
        
        Args:
            name: 模板名称
            template: 模板内容
            description: 模板描述
            **kwargs: 其他参数
        """
        from ..prompts import PromptTemplate
        template_obj = PromptTemplate(
            name=name,
            template=template,
            description=description,
            **kwargs
        )
        self.prompt_manager.register_template(template_obj)
    
    def list_templates(self) -> List[str]:
        """
        列出所有可用的模板
        
        Returns:
            List[str]: 模板名称列表
        """
        return self.prompt_manager.list_templates()
    
    def get_template_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取模板信息
        
        Args:
            name: 模板名称
            
        Returns:
            Optional[Dict[str, Any]]: 模板信息字典
        """
        template = self.prompt_manager.get_template(name)
        if not template:
            return None
        
        return {
            "name": template.name,
            "description": template.description,
            "required_parameters": template.get_required_parameters(),
            "parameters": template.parameters
        }
    
    def parse_response(self, content: str, format_type: Optional[str] = None) -> ParsedResult:
        """
        解析响应内容
        
        Args:
            content: 响应内容
            format_type: 解析格式，如果不提供则自动检测
            
        Returns:
            ParsedResult: 解析结果
        """
        if format_type:
            return self.response_parser.parse(content, format_type)
        else:
            return self.response_parser.parse_with_auto_detection(content)
    
    def create_message(self, role: str, content: str) -> Message:
        """
        创建消息对象
        
        Args:
            role: 消息角色 (system, user, assistant)
            content: 消息内容
            
        Returns:
            Message: 消息对象
        """
        return Message(role=role, content=content)
    
    def create_conversation(self, system_prompt: Optional[str] = None) -> List[Message]:
        """
        创建对话上下文
        
        Args:
            system_prompt: 系统提示词
            
        Returns:
            List[Message]: 消息列表
        """
        messages = []
        if system_prompt:
            messages.append(self.create_message("system", system_prompt))
        return messages
    
    def add_to_conversation(
        self,
        conversation: List[Message],
        role: str,
        content: str
    ) -> List[Message]:
        """
        向对话中添加消息
        
        Args:
            conversation: 对话消息列表
            role: 消息角色
            content: 消息内容
            
        Returns:
            List[Message]: 更新后的对话消息列表
        """
        conversation.append(self.create_message(role, content))
        return conversation


# 创建全局服务实例
llm_service = LLMService()