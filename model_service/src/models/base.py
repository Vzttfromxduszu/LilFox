from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class Message:
    """消息类，用于表示对话中的单条消息"""
    role: str  # system, user, assistant
    content: str
    
    def to_dict(self) -> Dict[str, str]:
        """转换为字典格式"""
        return {"role": self.role, "content": self.content}


@dataclass
class ModelResponse:
    """模型响应类"""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "content": self.content,
            "model": self.model,
            "usage": self.usage,
            "finish_reason": self.finish_reason,
            "raw_response": self.raw_response
        }


class BaseLLMModel(ABC):
    """大模型交互抽象基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化模型
        
        Args:
            config: 模型配置字典，包含api_key、base_url等
        """
        self.config = config
        self.api_key = config.get("api_key", "")
        self.base_url = config.get("base_url", "")
        self.model = config.get("model", "")
        self.timeout = config.get("timeout", 30)
    
    @abstractmethod
    def chat_completion(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ModelResponse:
        """
        聊天补全接口
        
        Args:
            messages: 消息列表
            temperature: 温度参数，控制随机性
            max_tokens: 最大生成token数
            **kwargs: 其他参数
            
        Returns:
            ModelResponse: 模型响应对象
        """
        pass
    
    @abstractmethod
    def text_completion(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ModelResponse:
        """
        文本补全接口
        
        Args:
            prompt: 提示词
            temperature: 温度参数，控制随机性
            max_tokens: 最大生成token数
            **kwargs: 其他参数
            
        Returns:
            ModelResponse: 模型响应对象
        """
        pass
    
    @abstractmethod
    def stream_chat_completion(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """
        流式聊天补全接口
        
        Args:
            messages: 消息列表
            temperature: 温度参数，控制随机性
            max_tokens: 最大生成token数
            **kwargs: 其他参数
            
        Yields:
            str: 生成的文本片段
        """
        pass
    
    def validate_config(self) -> bool:
        """
        验证配置是否有效
        
        Returns:
            bool: 配置是否有效
        """
        if not self.api_key:
            raise ValueError("API密钥不能为空")
        if not self.base_url:
            raise ValueError("Base URL不能为空")
        if not self.model:
            raise ValueError("模型名称不能为空")
        return True
    
    def prepare_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        """
        准备消息列表
        
        Args:
            messages: Message对象列表
            
        Returns:
            List[Dict[str, str]]: 字典格式的消息列表
        """
        return [msg.to_dict() for msg in messages]
    
    def create_system_message(self, content: str) -> Message:
        """创建系统消息"""
        return Message(role="system", content=content)
    
    def create_user_message(self, content: str) -> Message:
        """创建用户消息"""
        return Message(role="user", content=content)
    
    def create_assistant_message(self, content: str) -> Message:
        """创建助手消息"""
        return Message(role="assistant", content=content)