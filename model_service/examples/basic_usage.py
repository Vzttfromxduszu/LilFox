"""
基础使用示例
演示如何使用LLM服务进行基本的对话和文本补全
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services import llm_service
from src.models import Message


def example_basic_chat():
    """基础聊天示例"""
    print("=== 基础聊天示例 ===")
    
    messages = [
        Message(role="user", content="你好，请介绍一下你自己")
    ]
    
    try:
        response = llm_service.chat(messages)
        print(f"模型: {response.model}")
        print(f"响应: {response.content}")
        print(f"使用情况: {response.usage}")
    except Exception as e:
        print(f"错误: {e}")
    
    print()


def example_text_completion():
    """文本补全示例"""
    print("=== 文本补全示例 ===")
    
    prompt = "请用一句话解释什么是人工智能："
    
    try:
        response = llm_service.complete(prompt)
        print(f"响应: {response.content}")
    except Exception as e:
        print(f"错误: {e}")
    
    print()


def example_chat_with_template():
    """使用模板进行聊天示例"""
    print("=== 使用模板聊天示例 ===")
    
    try:
        response = llm_service.chat_with_template(
            template_name="qa",
            template_params={
                "context": "Python是一种高级编程语言，由Guido van Rossum于1991年首次发布。",
                "question": "Python是什么时候发布的？"
            }
        )
        print(f"响应: {response.content}")
    except Exception as e:
        print(f"错误: {e}")
    
    print()


def example_list_templates():
    """列出所有可用模板"""
    print("=== 可用模板列表 ===")
    
    templates = llm_service.list_templates()
    print(f"共有 {len(templates)} 个模板:")
    for template in templates:
        print(f"  - {template}")
    
    print()


def example_get_template_info():
    """获取模板信息"""
    print("=== 模板信息示例 ===")
    
    template_name = "qa"
    info = llm_service.get_template_info(template_name)
    
    if info:
        print(f"模板名称: {info['name']}")
        print(f"描述: {info['description']}")
        print(f"必需参数: {info['required_parameters']}")
    else:
        print(f"模板 {template_name} 不存在")
    
    print()


def example_parse_response():
    """解析响应示例"""
    print("=== 响应解析示例 ===")
    
    # JSON格式解析
    json_content = '{"name": "张三", "age": 25, "city": "北京"}'
    result = llm_service.parse_response(json_content, format_type="json")
    print(f"JSON解析结果: {result.data}")
    
    # 列表格式解析
    list_content = "- 苹果\n- 香蕉\n- 橙子"
    result = llm_service.parse_response(list_content, format_type="list")
    print(f"列表解析结果: {result.data}")
    
    # 自动检测格式
    auto_content = "```python\nprint('Hello, World!')\n```"
    result = llm_service.parse_response(auto_content)
    print(f"自动检测格式: {result.data}")
    
    print()


def example_custom_template():
    """自定义模板示例"""
    print("=== 自定义模板示例 ===")
    
    # 注册自定义模板
    llm_service.register_template(
        name="custom_greeting",
        template="你好{name}，欢迎来到{place}！希望你在这里度过愉快的时光。",
        description="自定义问候模板"
    )
    
    # 使用自定义模板
    try:
        response = llm_service.chat_with_template(
            template_name="custom_greeting",
            template_params={
                "name": "小明",
                "place": "LilFox"
            }
        )
        print(f"响应: {response.content}")
    except Exception as e:
        print(f"错误: {e}")
    
    print()


def example_conversation():
    """多轮对话示例"""
    print("=== 多轮对话示例 ===")
    
    conversation = llm_service.create_conversation(
        system_prompt="你是一个专业的编程助手，擅长Python编程。"
    )
    
    # 第一轮对话
    llm_service.add_to_conversation(conversation, "user", "如何定义一个Python函数？")
    response = llm_service.chat(conversation)
    print(f"用户: 如何定义一个Python函数？")
    print(f"助手: {response.content}\n")
    
    # 第二轮对话
    llm_service.add_to_conversation(conversation, "assistant", response.content)
    llm_service.add_to_conversation(conversation, "user", "能给一个具体的例子吗？")
    response = llm_service.chat(conversation)
    print(f"用户: 能给一个具体的例子吗？")
    print(f"助手: {response.content}\n")
    
    print()


if __name__ == "__main__":
    print("LilFox Model Service - 基础使用示例\n")
    
    example_basic_chat()
    example_text_completion()
    example_chat_with_template()
    example_list_templates()
    example_get_template_info()
    example_parse_response()
    example_custom_template()
    example_conversation()
    
    print("所有示例运行完成！")