"""
API使用示例
演示如何通过HTTP API调用LLM服务
"""

import requests
import json


BASE_URL = "http://localhost:8001/api/v1"


def example_health_check():
    """健康检查示例"""
    print("=== 健康检查 ===")
    
    response = requests.get(f"{BASE_URL}/health")
    data = response.json()
    
    print(f"状态: {data['status']}")
    print(f"版本: {data['version']}")
    print(f"可用模型: {data['models_available']}")
    print(f"可用模板: {data['templates_available']}")
    
    print()


def example_chat_api():
    """聊天API示例"""
    print("=== 聊天API ===")
    
    payload = {
        "messages": [
            {"role": "user", "content": "你好，请介绍一下你自己"}
        ]
    }
    
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    data = response.json()
    
    print(f"响应内容: {data['content']}")
    print(f"使用的模型: {data['model']}")
    
    print()


def example_complete_api():
    """文本补全API示例"""
    print("=== 文本补全API ===")
    
    payload = {
        "prompt": "请用一句话解释什么是人工智能："
    }
    
    response = requests.post(f"{BASE_URL}/complete", json=payload)
    data = response.json()
    
    print(f"响应内容: {data['content']}")
    
    print()


def example_template_chat_api():
    """使用模板聊天API示例"""
    print("=== 使用模板聊天API ===")
    
    payload = {
        "template_name": "qa",
        "template_params": {
            "context": "Python是一种高级编程语言，由Guido van Rossum于1991年首次发布。",
            "question": "Python是什么时候发布的？"
        }
    }
    
    response = requests.post(f"{BASE_URL}/chat/template", json=payload)
    data = response.json()
    
    print(f"响应内容: {data['content']}")
    
    print()


def example_list_templates_api():
    """列出模板API示例"""
    print("=== 列出模板API ===")
    
    response = requests.get(f"{BASE_URL}/templates")
    templates = response.json()
    
    print(f"可用模板: {templates}")
    
    print()


def example_get_template_info_api():
    """获取模板信息API示例"""
    print("=== 获取模板信息API ===")
    
    template_name = "qa"
    response = requests.get(f"{BASE_URL}/templates/{template_name}")
    data = response.json()
    
    print(f"模板名称: {data['name']}")
    print(f"描述: {data['description']}")
    print(f"必需参数: {data['required_parameters']}")
    
    print()


def example_register_template_api():
    """注册模板API示例"""
    print("=== 注册模板API ===")
    
    payload = {
        "name": "custom_greeting",
        "template": "你好{name}，欢迎来到{place}！希望你在这里度过愉快的时光。",
        "description": "自定义问候模板"
    }
    
    response = requests.post(f"{BASE_URL}/templates", json=payload)
    data = response.json()
    
    print(f"消息: {data['message']}")
    
    print()


def example_parse_api():
    """解析API示例"""
    print("=== 解析API ===")
    
    # JSON格式解析
    payload = {
        "content": '{"name": "张三", "age": 25, "city": "北京"}',
        "format_type": "json"
    }
    
    response = requests.post(f"{BASE_URL}/parse", json=payload)
    data = response.json()
    
    print(f"JSON解析结果: {data['data']}")
    
    # 列表格式解析
    payload = {
        "content": "- 苹果\n- 香蕉\n- 橙子",
        "format_type": "list"
    }
    
    response = requests.post(f"{BASE_URL}/parse", json=payload)
    data = response.json()
    
    print(f"列表解析结果: {data['data']}")
    
    # 自动检测格式
    payload = {
        "content": "```python\nprint('Hello, World!')\n```"
    }
    
    response = requests.post(f"{BASE_URL}/parse", json=payload)
    data = response.json()
    
    print(f"自动检测解析结果: {data['data']}")
    
    print()


def example_chat_with_parse():
    """聊天并解析响应示例"""
    print("=== 聊天并解析响应 ===")
    
    payload = {
        "messages": [
            {"role": "user", "content": "请用JSON格式返回一个包含姓名、年龄、城市的信息"}
        ],
        "parse_format": "json"
    }
    
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    data = response.json()
    
    print(f"解析后的数据: {data['content']}")
    
    print()


if __name__ == "__main__":
    print("LilFox Model Service - API使用示例\n")
    print("请确保服务已启动: python main.py\n")
    
    try:
        example_health_check()
        example_chat_api()
        example_complete_api()
        example_template_chat_api()
        example_list_templates_api()
        example_get_template_info_api()
        example_register_template_api()
        example_parse_api()
        example_chat_with_parse()
        
        print("所有API示例运行完成！")
    except requests.exceptions.ConnectionError:
        print("错误: 无法连接到服务，请确保服务已启动")
    except Exception as e:
        print(f"错误: {e}")