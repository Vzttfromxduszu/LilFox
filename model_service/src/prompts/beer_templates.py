from typing import Dict, Any
from .template import PromptTemplate, PromptManager


def create_beer_recommendation_templates() -> Dict[str, PromptTemplate]:
    """创建精酿啤酒推荐相关的提示词模板"""
    
    templates = {}
    
    templates["beer_recommendation"] = PromptTemplate(
        name="beer_recommendation",
        template="""你是一位专业的精酿啤酒推荐师。请根据用户提供的偏好信息，推荐合适的精酿啤酒。

用户偏好信息：
- 心情状态：{mood}
- 口味偏好：{taste}
- 酒花偏好：{hop}
- 精酿风格偏好：{style}

请基于以上信息，为用户推荐1-3款精酿啤酒，每款推荐包含：
1. 啤酒名称（产地+酒厂+啤酒名称）
2. 啤酒风格
3. 酒精度（ABV）
4. 推荐理由（结合用户的心情、口味、酒花偏好进行说明）
5. 适合的饮用场景

推荐要求：
- 推荐结果应包含起码两种中国精酿啤酒
- 推荐结果应准确反映用户提供的所有偏好信息
- 推荐理由要详细说明为什么这款啤酒适合用户当前的心情和口味
- 保持上下文连贯性，推荐之间要有逻辑关联
- 使用专业但易懂的语言描述
- 返回的啤酒一定是具体的啤酒名称""",
        description="精酿啤酒推荐模板",
        parameters={
            "mood": "心情状态（如：放松、兴奋、疲惫等）",
            "taste": "口味偏好（如：甜、苦、酸、平衡等）",
            "hop": "酒花偏好（如：柑橘味、热带水果味、松针味等）",
            "style": "精酿风格偏好（如：IPA、世涛、酸艾尔、拉格等）"
        }
    )
    
    templates["beer_knowledge"] = PromptTemplate(
        name="beer_knowledge",
        template="""请详细解释以下精酿啤酒相关的知识：

{question}

请提供专业、准确、易懂的解释，包括：
1. 基本定义和特点
2. 风味特征
3. 适合的饮用场景
4. 推荐搭配的食物""",
        description="精酿啤酒知识问答模板",
        parameters={
            "question": "用户关于精酿啤酒的问题"
        }
    )
    
    templates["beer_pairing"] = PromptTemplate(
        name="beer_pairing",
        template="""你是一位专业的精酿啤酒与美食搭配专家。

用户信息：
- 心情状态：{mood}
- 口味偏好：{taste}
- 餐饮场景：{dining_scenario}
- 食物类型：{food_type}

请为用户推荐合适的精酿啤酒与美食搭配方案，包括：
1. 推荐的精酿啤酒（1-2款）
2. 搭配的美食建议
3. 搭配理由（说明为什么这种搭配效果好）
4. 饮用建议（温度、杯型等）

要求：
- 推荐要考虑用户的心情和口味偏好
- 搭配方案要有创新性和实用性
- 解释要专业且易于理解""",
        description="精酿啤酒与美食搭配模板",
        parameters={
            "mood": "心情状态",
            "taste": "口味偏好",
            "dining_scenario": "餐饮场景（如：聚餐、独酌、约会等）",
            "food_type": "食物类型（如：烧烤、海鲜、甜点等）"
        }
    )
    
    templates["beer_style_guide"] = PromptTemplate(
        name="beer_style_guide",
        template="""请为以下精酿啤酒风格提供详细的风格指南：

{beer_style}

指南应包含：
1. 风格历史和起源
2. 典型风味特征
3. 酒精度范围
4. 代表性品牌或酒厂
5. 适合的新手入门推荐
6. 进阶探索建议""",
        description="精酿啤酒风格指南模板",
        parameters={
            "beer_style": "精酿啤酒风格名称（如：IPA、世涛、酸艾尔等）"
        }
    )
    
    return templates


def register_beer_templates(manager: PromptManager) -> None:
    """将精酿啤酒推荐模板注册到提示词管理器"""
    templates = create_beer_recommendation_templates()
    for template in templates.values():
        manager.register_template(template)


def get_beer_template_manager() -> PromptManager:
    """获取预加载了精酿啤酒推荐模板的提示词管理器"""
    manager = PromptManager()
    register_beer_templates(manager)
    return manager
