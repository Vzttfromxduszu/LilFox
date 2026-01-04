from fastapi import APIRouter, HTTPException, status
from typing import Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services import llm_service
from src.routes.schemas import (
    ChatRequest,
    CompletionRequest,
    TemplateChatRequest,
    TemplateRegisterRequest,
    ParseRequest,
    ModelResponse,
    ParsedResponse,
    TemplateInfo,
    HealthResponse
)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    健康检查接口
    
    Returns:
        HealthResponse: 服务状态信息
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        models_available=list(llm_service.models.keys()),
        templates_available=llm_service.list_templates()
    )


@router.post("/chat", response_model=ModelResponse)
async def chat(request: ChatRequest):
    """
    聊天接口
    
    Args:
        request: 聊天请求
        
    Returns:
        ModelResponse: 模型响应
    """
    try:
        from src.models import Message
        messages = [Message(role=msg.role, content=msg.content) for msg in request.messages]
        
        result = llm_service.chat(
            messages=messages,
            provider=request.provider,
            parse_format=request.parse_format,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        if hasattr(result, 'content'):
            return ModelResponse(
                content=result.content,
                model=result.model,
                usage=result.usage,
                finish_reason=result.finish_reason
            )
        else:
            return ModelResponse(
                content=str(result.data),
                model="unknown",
                usage=None,
                finish_reason=None
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"聊天请求失败: {str(e)}"
        )


@router.post("/complete", response_model=ModelResponse)
async def complete(request: CompletionRequest):
    """
    文本补全接口
    
    Args:
        request: 补全请求
        
    Returns:
        ModelResponse: 模型响应
    """
    try:
        result = llm_service.complete(
            prompt=request.prompt,
            provider=request.provider,
            parse_format=request.parse_format,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        if hasattr(result, 'content'):
            return ModelResponse(
                content=result.content,
                model=result.model,
                usage=result.usage,
                finish_reason=result.finish_reason
            )
        else:
            return ModelResponse(
                content=str(result.data),
                model="unknown",
                usage=None,
                finish_reason=None
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"补全请求失败: {str(e)}"
        )


@router.post("/chat/template", response_model=ModelResponse)
async def chat_with_template(request: TemplateChatRequest):
    """
    使用模板进行聊天
    
    Args:
        request: 模板聊天请求
        
    Returns:
        ModelResponse: 模型响应
    """
    try:
        result = llm_service.chat_with_template(
            template_name=request.template_name,
            template_params=request.template_params,
            provider=request.provider,
            parse_format=request.parse_format,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        if hasattr(result, 'content'):
            return ModelResponse(
                content=result.content,
                model=result.model,
                usage=result.usage,
                finish_reason=result.finish_reason
            )
        else:
            return ModelResponse(
                content=str(result.data),
                model="unknown",
                usage=None,
                finish_reason=None
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"模板聊天请求失败: {str(e)}"
        )


@router.post("/parse", response_model=ParsedResponse)
async def parse_response(request: ParseRequest):
    """
    解析响应内容
    
    Args:
        request: 解析请求
        
    Returns:
        ParsedResponse: 解析结果
    """
    try:
        result = llm_service.parse_response(
            content=request.content,
            format_type=request.format_type
        )
        
        return ParsedResponse(
            success=result.success,
            data=result.data,
            error=result.error,
            raw_content=result.raw_content
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"解析请求失败: {str(e)}"
        )


@router.get("/templates", response_model=list)
async def list_templates():
    """
    列出所有可用的模板
    
    Returns:
        list: 模板名称列表
    """
    try:
        return llm_service.list_templates()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模板列表失败: {str(e)}"
        )


@router.get("/templates/{template_name}", response_model=TemplateInfo)
async def get_template_info(template_name: str):
    """
    获取模板信息
    
    Args:
        template_name: 模板名称
        
    Returns:
        TemplateInfo: 模板信息
    """
    try:
        info = llm_service.get_template_info(template_name)
        if not info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"模板 {template_name} 不存在"
            )
        
        return TemplateInfo(**info)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模板信息失败: {str(e)}"
        )


@router.post("/templates", status_code=status.HTTP_201_CREATED)
async def register_template(request: TemplateRegisterRequest):
    """
    注册自定义模板
    
    Args:
        request: 模板注册请求
        
    Returns:
        dict: 成功消息
    """
    try:
        llm_service.register_template(
            name=request.name,
            template=request.template,
            description=request.description,
            parameters=request.parameters or {}
        )
        
        return {"message": f"模板 {request.name} 注册成功"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册模板失败: {str(e)}"
        )