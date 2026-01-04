from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional
import sys
import os
import logging

from ..config.settings import settings




sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.llm_service import LLMService
from src.prompts.beer_templates import register_beer_templates
from src.routes.beer_schemas import (
    BeerRecommendationRequest,
    BeerRecommendationResponse,
    BeerRecommendation,
    BeerRecommendationOptions,
    BeerKnowledgeRequest,
    BeerKnowledgeResponse,
    BeerPairingRequest,
    BeerPairingResponse,
    BeerStyleGuideRequest,
    BeerStyleGuideResponse,
    BeerChatRequest,
    BeerChatResponse
)
from src.routes.beer_exceptions import (
    ParameterValidationError,
    TemplateNotFoundError,
    TemplateFormatError,
    LLMServiceError,
    RecommendationGenerationError,
    KnowledgeQueryError,
    PairingGenerationError,
    StyleGuideGenerationError,
    handle_beer_exception
)

router = APIRouter()

logger = logging.getLogger(__name__)


def get_llm_service():
    """获取LLM服务实例"""
    from src.services.llm_service import llm_service
    register_beer_templates(llm_service.prompt_manager)
    return llm_service


@router.post("/recommend", response_model=BeerRecommendationResponse, summary="精酿啤酒推荐")
async def recommend_beer(
    request: BeerRecommendationRequest,
    provider: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    llm_service: LLMService = Depends(get_llm_service)
):
    """
    根据用户偏好推荐精酿啤酒
    
    Args:
        request: 用户偏好信息
        provider: 模型提供商（查询参数）
        temperature: 温度参数，控制随机性（查询参数）
        max_tokens: 最大生成token数（查询参数）
        llm_service: LLM服务实例
        
    Returns:
        BeerRecommendationResponse: 推荐结果
    """
    try:
        # 使用 settings 中的默认值
        selected_provider = provider or settings.DEFAULT_MODEL_PROVIDER
        provider_config = settings.get_model_config(selected_provider)
        
        options = BeerRecommendationOptions(
            provider=selected_provider,
            temperature=temperature or provider_config.get("temperature", 0.7),
            max_tokens=max_tokens or provider_config.get("max_tokens", 1500)
        )
        
        template_params = {
            "mood": request.mood,
            "taste": request.taste,
            "hop": request.hop,
            "style": request.style
        }
        
        result = llm_service.chat_with_template(
            template_name="beer_recommendation",
            template_params=template_params,
            provider=options.provider,
            temperature=options.temperature,
            max_tokens=options.max_tokens
        )
        
        content = result.content if hasattr(result, 'content') else str(result.data)
        
        # 直接返回大模型的原始响应内容，暂时跳过解析逻辑
        logger.debug(f"LLM原始响应: {content}")
        
        # 创建一个包含完整响应内容的推荐
        recommendations = [
            BeerRecommendation(
                name="精酿啤酒推荐",
                style=request.style or "根据您的偏好",
                abv="根据具体啤酒",
                reason=content,  # 直接将完整响应内容作为推荐理由
                drinking_scenario="多种场景适用"
            )
        ]
        
        return BeerRecommendationResponse(
            success=True,
            recommendations=recommendations,
            user_preferences=template_params,
            model=result.model if hasattr(result, 'model') else None,
            usage=result.usage if hasattr(result, 'usage') else None
        )
        
    except ValueError as e:
        logger.error(f"参数验证错误: {str(e)}")
        raise handle_beer_exception(ParameterValidationError("request", request, str(e)))
    except Exception as e:
        logger.error(f"推荐生成失败: {str(e)}")
        raise handle_beer_exception(RecommendationGenerationError(
            {"mood": request.mood, "taste": request.taste, "hop": request.hop, "style": request.style},
            str(e)
        ))


@router.post("/knowledge", response_model=BeerKnowledgeResponse, summary="精酿啤酒知识问答")
async def beer_knowledge(
    request: BeerKnowledgeRequest,
    provider: Optional[str] = None,
    llm_service: LLMService = Depends(get_llm_service)
):
    """
    回答关于精酿啤酒的知识问题
    
    Args:
        request: 用户问题
        provider: 模型提供商
        llm_service: LLM服务实例
        
    Returns:
        BeerKnowledgeResponse: 回答结果
    """
    try:
        # 使用 settings 中的默认值
        selected_provider = provider or settings.DEFAULT_MODEL_PROVIDER
        provider_config = settings.get_model_config(selected_provider)
        
        result = llm_service.chat_with_template(
            template_name="beer_knowledge",
            template_params={"question": request.question},
            provider=selected_provider,
            temperature=provider_config.get("temperature", 0.7),
            max_tokens=provider_config.get("max_tokens", 1000)
        )
        
        content = result.content if hasattr(result, 'content') else str(result.data)
        
        return BeerKnowledgeResponse(
            success=True,
            answer=content,
            question=request.question,
            model=result.model if hasattr(result, 'model') else None,
            usage=result.usage if hasattr(result, 'usage') else None
        )
        
    except Exception as e:
        logger.error(f"知识查询失败: {str(e)}")
        raise handle_beer_exception(KnowledgeQueryError(request.question, str(e)))


@router.post("/pairing", response_model=BeerPairingResponse, summary="精酿啤酒与美食搭配")
async def beer_pairing(
    request: BeerPairingRequest,
    provider: Optional[str] = None,
    llm_service: LLMService = Depends(get_llm_service)
):
    """
    推荐精酿啤酒与美食的搭配方案
    
    Args:
        request: 用户上下文信息
        provider: 模型提供商
        llm_service: LLM服务实例
        
    Returns:
        BeerPairingResponse: 搭配方案
    """
    try:
        template_params = {
            "mood": request.mood,
            "taste": request.taste,
            "dining_scenario": request.dining_scenario,
            "food_type": request.food_type
        }
        
        # 使用 settings 中的默认值
        selected_provider = provider or settings.DEFAULT_MODEL_PROVIDER
        provider_config = settings.get_model_config(selected_provider)
        
        result = llm_service.chat_with_template(
            template_name="beer_pairing",
            template_params=template_params,
            provider=selected_provider,
            temperature=provider_config.get("temperature", 0.7),
            max_tokens=provider_config.get("max_tokens", 1000)
        )
        
        content = result.content if hasattr(result, 'content') else str(result.data)
        
        return BeerPairingResponse(
            success=True,
            pairings=[{
                "beer": "推荐啤酒",
                "food": request.food_type,
                "reason": content
            }],
            user_context=template_params,
            model=result.model if hasattr(result, 'model') else None,
            usage=result.usage if hasattr(result, 'usage') else None
        )
        
    except Exception as e:
        logger.error(f"搭配生成失败: {str(e)}")
        raise handle_beer_exception(PairingGenerationError(
            {"mood": request.mood, "taste": request.taste, "dining_scenario": request.dining_scenario, "food_type": request.food_type},
            str(e)
        ))


@router.post("/style-guide", response_model=BeerStyleGuideResponse, summary="精酿啤酒风格指南")
async def beer_style_guide(
    request: BeerStyleGuideRequest,
    provider: Optional[str] = None,
    llm_service: LLMService = Depends(get_llm_service)
):
    """
    生成指定精酿啤酒风格的详细指南
    
    Args:
        request: 啤酒风格名称
        provider: 模型提供商
        llm_service: LLM服务实例
        
    Returns:
        BeerStyleGuideResponse: 风格指南
    """
    try:
        # 使用 settings 中的默认值
        selected_provider = provider or settings.DEFAULT_MODEL_PROVIDER
        provider_config = settings.get_model_config(selected_provider)
        
        result = llm_service.chat_with_template(
            template_name="beer_style_guide",
            template_params={"beer_style": request.beer_style},
            provider=selected_provider,
            temperature=provider_config.get("temperature", 0.7),
            max_tokens=provider_config.get("max_tokens", 1000)
        )
        
        content = result.content if hasattr(result, 'content') else str(result.data)
        
        return BeerStyleGuideResponse(
            success=True,
            guide=content,
            beer_style=request.beer_style,
            model=result.model if hasattr(result, 'model') else None,
            usage=result.usage if hasattr(result, 'usage') else None
        )
        
    except Exception as e:
        logger.error(f"风格指南生成失败: {str(e)}")
        raise handle_beer_exception(StyleGuideGenerationError(request.beer_style, str(e)))


@router.post("/chat", response_model=BeerChatResponse, summary="精酿啤酒通用聊天")
async def beer_chat(
    request: BeerChatRequest,
    llm_service: LLMService = Depends(get_llm_service)
):
    """
    精酿啤酒相关的通用聊天接口
    
    Args:
        request: 聊天请求
        llm_service: LLM服务实例
        
    Returns:
        BeerChatResponse: 聊天响应
    """
    try:
        system_prompt = "你是一位专业的精酿啤酒专家，精通各种精酿啤酒的风格、酿造工艺、风味特征和搭配知识。请用专业但易懂的语言回答用户的问题。"
        
        messages = llm_service.create_conversation(system_prompt)
        
        if request.conversation_history:
            for msg in request.conversation_history:
                messages = llm_service.add_to_conversation(
                    messages,
                    role=msg.get("role", "user"),
                    content=msg.get("content", "")
                )
        
        messages = llm_service.add_to_conversation(
            messages,
            role="user",
            content=request.message
        )
        
        result = llm_service.chat(
            messages=messages,
            provider=request.provider,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        content = result.content if hasattr(result, 'content') else str(result.data)
        
        return BeerChatResponse(
            success=True,
            response=content,
            model=result.model if hasattr(result, 'model') else None,
            usage=result.usage if hasattr(result, 'usage') else None
        )
        
    except Exception as e:
        logger.error(f"聊天请求失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"聊天请求失败: {str(e)}"
        )


@router.get("/templates", summary="列出所有精酿啤酒相关模板")
async def list_beer_templates(llm_service: LLMService = Depends(get_llm_service)):
    """
    列出所有可用的精酿啤酒推荐相关模板
    
    Returns:
        list: 模板名称列表
    """
    try:
        beer_templates = [
            "beer_recommendation",
            "beer_knowledge",
            "beer_pairing",
            "beer_style_guide"
        ]
        
        available_templates = [
            t for t in beer_templates 
            if t in llm_service.list_templates()
        ]
        
        return available_templates
        
    except Exception as e:
        logger.error(f"获取模板列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模板列表失败: {str(e)}"
        )
