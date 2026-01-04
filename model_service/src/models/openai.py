from typing import Dict, Any, Optional, List
import httpx
import json
import asyncio
from .base import BaseLLMModel, Message, ModelResponse


class OpenAIModel(BaseLLMModel):
    """OpenAI模型实现类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化OpenAI模型
        
        Args:
            config: 模型配置字典
        """
        super().__init__(config)
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 1000)
        self.validate_config()
    
    def chat_completion(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ModelResponse:
        """
        OpenAI聊天补全接口
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大生成token数
            **kwargs: 其他参数
            
        Returns:
            ModelResponse: 模型响应对象
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": self.prepare_messages(messages),
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
            **kwargs
        }
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data
                )
                response.raise_for_status()
                result = response.json()
                
                return self._parse_chat_response(result)
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"OpenAI API请求失败: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise RuntimeError(f"OpenAI API请求错误: {str(e)}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"解析OpenAI响应失败: {str(e)}")
    
    def text_completion(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ModelResponse:
        """
        OpenAI文本补全接口
        
        Args:
            prompt: 提示词
            temperature: 温度参数
            max_tokens: 最大生成token数
            **kwargs: 其他参数
            
        Returns:
            ModelResponse: 模型响应对象
        """
        messages = [self.create_user_message(prompt)]
        return self.chat_completion(messages, temperature, max_tokens, **kwargs)
    
    def stream_chat_completion(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """
        OpenAI流式聊天补全接口
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大生成token数
            **kwargs: 其他参数
            
        Yields:
            str: 生成的文本片段
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": self.prepare_messages(messages),
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
            "stream": True,
            **kwargs
        }
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data
                ) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_str)
                                if "choices" in chunk and len(chunk["choices"]) > 0:
                                    delta = chunk["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                continue
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"OpenAI API流式请求失败: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise RuntimeError(f"OpenAI API流式请求错误: {str(e)}")
    
    def _parse_chat_response(self, response: Dict[str, Any]) -> ModelResponse:
        """
        解析OpenAI聊天响应
        
        Args:
            response: OpenAI API响应字典
            
        Returns:
            ModelResponse: 解析后的响应对象
        """
        if "choices" not in response or len(response["choices"]) == 0:
            raise RuntimeError("OpenAI响应中没有choices字段")
        
        choice = response["choices"][0]
        message = choice.get("message", {})
        content = message.get("content", "")
        
        usage = response.get("usage", {})
        finish_reason = choice.get("finish_reason")
        
        return ModelResponse(
            content=content,
            model=response.get("model", self.model),
            usage=usage,
            finish_reason=finish_reason,
            raw_response=response
        )
    
    async def async_chat_completion(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ModelResponse:
        """
        异步OpenAI聊天补全接口
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大生成token数
            **kwargs: 其他参数
            
        Returns:
            ModelResponse: 模型响应对象
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": self.prepare_messages(messages),
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
            **kwargs
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data
                )
                response.raise_for_status()
                result = response.json()
                
                return self._parse_chat_response(result)
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"OpenAI API异步请求失败: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise RuntimeError(f"OpenAI API异步请求错误: {str(e)}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"解析OpenAI响应失败: {str(e)}")