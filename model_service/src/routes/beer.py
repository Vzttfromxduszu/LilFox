from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional
import logging

from src.services.beer_service import BeerService, beer_service
from src.schema.beer_schemas import (
    BeerRecommendationRequest,
    BeerRecommendationResponse,
    BeerKnowledgeRequest,
    BeerKnowledgeResponse,
    BeerPairingRequest,
    BeerPairingResponse,
    BeerStyleGuideRequest,
    BeerStyleGuideResponse,
    BeerChatRequest,
    BeerChatResponse
)
from src.schema.beer_exceptions import handle_beer_exception

router = APIRouter()

logger = logging.getLogger(__name__)


def get_beer_service():
    """获取啤酒服务实例"""
    return beer_service


@router.post("/recommend", response_model=BeerRecommendationResponse, summary="精酿啤酒推荐")
async def recommend_beer(
    request: BeerRecommendationRequest,
    provider: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    beer_service: BeerService = Depends(get_beer_service)
):
    """
    根据用户偏好推荐精酿啤酒
    
    Args:
        request: 用户偏好信息
        provider: 模型提供商（查询参数）
        temperature: 温度参数，控制随机性（查询参数）
        max_tokens: 最大生成token数（查询参数）
        beer_service: 啤酒服务实例
        
    Returns:
        BeerRecommendationResponse: 推荐结果
    """
    try:
        return beer_service.get_recommendation(
            request=request,
            provider=provider,
            temperature=temperature,
            max_tokens=max_tokens
        )
    except Exception as e:
        logger.error(f"推荐接口错误: {str(e)}")
        raise handle_beer_exception(e)


@router.post("/knowledge", response_model=BeerKnowledgeResponse, summary="精酿啤酒知识问答")
async def beer_knowledge(
    request: BeerKnowledgeRequest,
    provider: Optional[str] = None,
    beer_service: BeerService = Depends(get_beer_service)
):
    """
    回答关于精酿啤酒的知识问题
    
    Args:
        request: 用户问题
        provider: 模型提供商
        beer_service: 啤酒服务实例
        
    Returns:
        BeerKnowledgeResponse: 回答结果
    """
    try:
        return beer_service.get_knowledge(
            request=request,
            provider=provider
        )
    except Exception as e:
        logger.error(f"知识接口错误: {str(e)}")
        raise handle_beer_exception(e)


@router.post("/pairing", response_model=BeerPairingResponse, summary="精酿啤酒与美食搭配")
async def beer_pairing(
    request: BeerPairingRequest,
    provider: Optional[str] = None,
    beer_service: BeerService = Depends(get_beer_service)
):
    """
    推荐精酿啤酒与美食的搭配方案
    
    Args:
        request: 用户上下文信息
        provider: 模型提供商
        beer_service: 啤酒服务实例
        
    Returns:
        BeerPairingResponse: 搭配方案
    """
    try:
        return beer_service.get_pairing(
            request=request,
            provider=provider
        )
    except Exception as e:
        logger.error(f"搭配接口错误: {str(e)}")
        raise handle_beer_exception(e)


@router.post("/style-guide", response_model=BeerStyleGuideResponse, summary="精酿啤酒风格指南")
async def beer_style_guide(
    request: BeerStyleGuideRequest,
    provider: Optional[str] = None,
    beer_service: BeerService = Depends(get_beer_service)
):
    """
    生成指定精酿啤酒风格的详细指南
    
    Args:
        request: 啤酒风格名称
        provider: 模型提供商
        beer_service: 啤酒服务实例
        
    Returns:
        BeerStyleGuideResponse: 风格指南
    """
    try:
        return beer_service.get_style_guide(
            request=request,
            provider=provider
        )
    except Exception as e:
        logger.error(f"风格指南接口错误: {str(e)}")
        raise handle_beer_exception(e)


@router.post("/chat", response_model=BeerChatResponse, summary="精酿啤酒通用聊天")
async def beer_chat(
    request: BeerChatRequest,
    beer_service: BeerService = Depends(get_beer_service)
):
    """
    精酿啤酒相关的通用聊天接口
    
    Args:
        request: 聊天请求
        beer_service: 啤酒服务实例
        
    Returns:
        BeerChatResponse: 聊天响应
    """
    try:
        return beer_service.chat(
            request=request
        )
    except Exception as e:
        logger.error(f"聊天接口错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"聊天请求失败: {str(e)}"
        )


@router.get("/templates", summary="列出所有精酿啤酒相关模板")
async def list_beer_templates(beer_service: BeerService = Depends(get_beer_service)):
    """
    列出所有可用的精酿啤酒推荐相关模板
    
    Returns:
        list: 模板名称列表
    """
    try:
        return beer_service.list_templates()
    except Exception as e:
        logger.error(f"获取模板列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模板列表失败: {str(e)}"
        )
