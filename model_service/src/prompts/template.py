from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import re
import json


@dataclass
class PromptTemplate:
    """提示词模板类，支持动态参数替换和提示词组合"""
    
    name: str
    template: str
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    
    def format(self, **kwargs) -> str:
        """使用提供的参数格式化模板"""
        try:
            formatted = self.template.format(**kwargs)
            return formatted
        except KeyError as e:
            raise ValueError(f"缺少必需的参数: {e}")
    
    def validate_parameters(self, **kwargs) -> bool:
        """验证提供的参数是否满足模板要求"""
        required_params = set(re.findall(r'\{(\w+)\}', self.template))
        provided_params = set(kwargs.keys())
        return required_params.issubset(provided_params)
    
    def get_required_parameters(self) -> List[str]:
        """获取模板所需的所有参数"""
        return list(set(re.findall(r'\{(\w+)\}', self.template)))
    
    def add_example(self, input_data: Dict[str, Any], output: str) -> None:
        """添加示例"""
        self.examples.append({"input": input_data, "output": output})
    
    def with_examples(self) -> str:
        """将示例添加到模板中"""
        if not self.examples:
            return self.template
        
        examples_text = "\n\n示例:\n"
        for i, example in enumerate(self.examples, 1):
            examples_text += f"\n示例 {i}:\n"
            examples_text += f"输入: {json.dumps(example['input'], ensure_ascii=False)}\n"
            examples_text += f"输出: {example['output']}\n"
        
        return self.template + examples_text
    
    def combine(self, other_template: 'PromptTemplate', separator: str = "\n\n") -> 'PromptTemplate':
        """组合两个提示词模板"""
        combined_name = f"{self.name}+{other_template.name}"
        combined_template = f"{self.template}{separator}{other_template.template}"
        combined_description = f"{self.description} + {other_template.description}"
        combined_parameters = {**self.parameters, **other_template.parameters}
        
        return PromptTemplate(
            name=combined_name,
            template=combined_template,
            description=combined_description,
            parameters=combined_parameters,
            examples=[]
        )


class PromptManager:
    """提示词管理器，用于管理和组织多个提示词模板"""
    
    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
    
    def register_template(self, template: PromptTemplate) -> None:
        """注册提示词模板"""
        self.templates[template.name] = template
    
    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """获取指定的提示词模板"""
        return self.templates.get(name)
    
    def list_templates(self) -> List[str]:
        """列出所有已注册的模板名称"""
        return list(self.templates.keys())
    
    def format_template(self, name: str, **kwargs) -> str:
        """格式化指定的模板"""
        template = self.get_template(name)
        if template is None:
            raise ValueError(f"未找到模板: {name}")
        return template.format(**kwargs)
    
    def create_chain(self, template_names: List[str], separator: str = "\n\n") -> PromptTemplate:
        """创建提示词链，按顺序组合多个模板"""
        if not template_names:
            raise ValueError("模板名称列表不能为空")
        
        first_template = self.get_template(template_names[0])
        if first_template is None:
            raise ValueError(f"未找到模板: {template_names[0]}")
        
        chain_template = first_template
        for name in template_names[1:]:
            next_template = self.get_template(name)
            if next_template is None:
                raise ValueError(f"未找到模板: {name}")
            chain_template = chain_template.combine(next_template, separator)
        
        return chain_template
    
    def remove_template(self, name: str) -> bool:
        """移除指定的模板"""
        if name in self.templates:
            del self.templates[name]
            return True
        return False
    
    def clear_all(self) -> None:
        """清除所有模板"""
        self.templates.clear()


# 预定义的常用提示词模板
PREDEFINED_TEMPLATES = {
    "qa": PromptTemplate(
        name="qa",
        template="你是一个专业的问答助手。请根据以下信息回答用户的问题。\n\n背景信息:\n{context}\n\n用户问题:\n{question}\n\n请提供准确、详细的回答:",
        description="问答模板",
        parameters={"context": "背景信息", "question": "用户问题"}
    ),
    
    "summarization": PromptTemplate(
        name="summarization",
        template="请对以下文本进行摘要，要求简洁明了，保留关键信息。\n\n原文:\n{text}\n\n摘要:",
        description="文本摘要模板",
        parameters={"text": "待摘要的文本"}
    ),
    
    "translation": PromptTemplate(
        name="translation",
        template="请将以下文本从{source_lang}翻译成{target_lang}。\n\n原文:\n{text}\n\n译文:",
        description="翻译模板",
        parameters={"source_lang": "源语言", "target_lang": "目标语言", "text": "待翻译的文本"}
    ),
    
    "code_generation": PromptTemplate(
        name="code_generation",
        template="你是一个专业的编程助手。请根据以下要求生成代码。\n\n语言: {language}\n需求: {requirements}\n\n请提供完整、可运行的代码，并添加必要的注释:",
        description="代码生成模板",
        parameters={"language": "编程语言", "requirements": "需求描述"}
    ),
    
    "sentiment_analysis": PromptTemplate(
        name="sentiment_analysis",
        template="请分析以下文本的情感倾向（正面、负面或中性），并给出置信度。\n\n文本:\n{text}\n\n分析结果:",
        description="情感分析模板",
        parameters={"text": "待分析的文本"}
    ),
    
    "explanation": PromptTemplate(
        name="explanation",
        template="请用简单易懂的语言解释以下概念。\n\n概念:\n{concept}\n\n解释:",
        description="概念解释模板",
        parameters={"concept": "待解释的概念"}
    ),
    
    
}


def initialize_prompt_manager() -> PromptManager:
    """初始化提示词管理器并加载预定义模板"""
    manager = PromptManager()
    for template in PREDEFINED_TEMPLATES.values():
        manager.register_template(template)
    return manager