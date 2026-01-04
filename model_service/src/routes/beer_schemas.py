from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class BeerRecommendationRequest(BaseModel):
    """精酿啤酒推荐请求模型"""
    mood: str = Field(..., description="心情状态（如：放松、兴奋、疲惫等）")
    taste: str = Field(..., description="口味偏好（如：甜、苦、酸、平衡等）")
    hop: str = Field(..., description="酒花偏好（如：柑橘味、热带水果味、松针味等）")
    style: str = Field(..., description="精酿风格偏好（如：IPA、世涛、酸艾尔、拉格等）")


class BeerRecommendationOptions(BaseModel):
    """精酿啤酒推荐选项模型"""
    provider: Optional[str] = Field(None, description="模型提供商")
    temperature: Optional[float] = Field(0.7, description="温度参数，控制随机性")
    max_tokens: Optional[int] = Field(1000, description="最大生成token数")


class BeerRecommendation(BaseModel):
    """单个啤酒推荐模型"""
    name: str = Field(..., description="啤酒名称")
    style: str = Field(..., description="啤酒风格")
    abv: str = Field(..., description="酒精度（ABV）")
    reason: str = Field(..., description="推荐理由")
    drinking_scenario: str = Field(..., description="适合的饮用场景")


class BeerRecommendationResponse(BaseModel):
    """精酿啤酒推荐响应模型"""
    success: bool = Field(..., description="是否推荐成功")
    recommendations: List[BeerRecommendation] = Field(..., description="推荐列表")
    user_preferences: Dict[str, str] = Field(..., description="用户偏好信息")
    model: Optional[str] = Field(None, description="使用的模型")
    usage: Optional[Dict[str, Any]] = Field(None, description="使用情况")


class BeerKnowledgeRequest(BaseModel):
    """精酿啤酒知识问答请求模型"""
    question: str = Field(..., description="用户问题")


class BeerKnowledgeResponse(BaseModel):
    """精酿啤酒知识问答响应模型"""
    success: bool = Field(..., description="是否回答成功")
    answer: str = Field(..., description="回答内容")
    question: str = Field(..., description="用户问题")
    model: Optional[str] = Field(None, description="使用的模型")
    usage: Optional[Dict[str, Any]] = Field(None, description="使用情况")


class BeerPairingRequest(BaseModel):
    """精酿啤酒与美食搭配请求模型"""
    mood: str = Field(..., description="心情状态")
    taste: str = Field(..., description="口味偏好")
    dining_scenario: str = Field(..., description="餐饮场景")
    food_type: str = Field(..., description="食物类型")


class BeerPairingResponse(BaseModel):
    """精酿啤酒与美食搭配响应模型"""
    success: bool = Field(..., description="是否搭配成功")
    pairings: List[Dict[str, Any]] = Field(..., description="搭配方案列表")
    user_context: Dict[str, str] = Field(..., description="用户上下文信息")
    model: Optional[str] = Field(None, description="使用的模型")
    usage: Optional[Dict[str, Any]] = Field(None, description="使用情况")


class BeerStyleGuideRequest(BaseModel):
    """精酿啤酒风格指南请求模型"""
    beer_style: str = Field(..., description="精酿啤酒风格名称")


class BeerStyleGuideResponse(BaseModel):
    """精酿啤酒风格指南响应模型"""
    success: bool = Field(..., description="是否生成成功")
    guide: str = Field(..., description="风格指南内容")
    beer_style: str = Field(..., description="精酿啤酒风格名称")
    model: Optional[str] = Field(None, description="使用的模型")
    usage: Optional[Dict[str, Any]] = Field(None, description="使用情况")


class BeerChatRequest(BaseModel):
    """精酿啤酒通用聊天请求模型"""
    message: str = Field(..., description="用户消息")
    conversation_history: Optional[List[Dict[str, str]]] = Field(None, description="对话历史")
    provider: Optional[str] = Field(None, description="模型提供商")
    temperature: Optional[float] = Field(0.7, description="温度参数")
    max_tokens: Optional[int] = Field(1000, description="最大生成token数")


class BeerChatResponse(BaseModel):
    """精酿啤酒通用聊天响应模型"""
    success: bool = Field(..., description="是否响应成功")
    response: str = Field(..., description="响应内容")
    model: Optional[str] = Field(None, description="使用的模型")
    usage: Optional[Dict[str, Any]] = Field(None, description="使用情况")
