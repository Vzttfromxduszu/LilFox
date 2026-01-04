"""
精酿啤酒推荐API测试脚本

测试所有精酿啤酒推荐相关的API接口
"""
from pydantic import Json
import requests
import json

BASE_URL = "http://localhost:8001/api/v1"


def test_beer_recommendation():
    """测试精酿啤酒推荐接口"""
    print("\n=== 测试精酿啤酒推荐接口 ===")
    
    url = f"{BASE_URL}/beer/recommend"
    data = {
        "mood": "放松",
        "taste": "平衡",
        "hop": "柑橘味",
        "style": "IPA"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"请求失败: {e}")
        return False


def test_beer_knowledge():
    """测试精酿啤酒知识问答接口"""
    print("\n=== 测试精酿啤酒知识问答接口 ===")
    
    url = f"{BASE_URL}/beer/knowledge"
    data = {
        "question": "什么是IPA啤酒？它有什么特点？"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"请求失败: {e}")
        return False


def test_beer_pairing():
    """测试精酿啤酒与美食搭配接口"""
    print("\n=== 测试精酿啤酒与美食搭配接口 ===")
    
    url = f"{BASE_URL}/beer/pairing"
    data = {
        "mood": "兴奋",
        "taste": "苦",
        "dining_scenario": "聚餐",
        "food_type": "烧烤"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"请求失败: {e}")
        return False


def test_beer_style_guide():
    """测试精酿啤酒风格指南接口"""
    print("\n=== 测试精酿啤酒风格指南接口 ===")
    
    url = f"{BASE_URL}/beer/style-guide"
    data = {
        "beer_style": "世涛"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"请求失败: {e}")
        return False


def test_beer_chat():
    """测试精酿啤酒通用聊天接口"""
    print("\n=== 测试精酿啤酒通用聊天接口 ===")
    
    url = f"{BASE_URL}/beer/chat"
    data = {
        "message": "请推荐一款适合夏天饮用的精酿啤酒"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"请求失败: {e}")
        return False


def test_list_templates():
    """测试列出所有精酿啤酒相关模板接口"""
    print("\n=== 测试列出所有精酿啤酒相关模板接口 ===")
    
    url = f"{BASE_URL}/beer/templates"
    
    try:
        response = requests.get(url)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"请求失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("=" * 50)
    print("精酿啤酒推荐API测试")
    print("=" * 50)
    
    tests = [
        ("列出模板", test_list_templates),
        ("啤酒推荐", test_beer_recommendation),
        # ("知识问答", test_beer_knowledge),
        # ("美食搭配", test_beer_pairing),
        # ("风格指南", test_beer_style_guide),
        # ("通用聊天", test_beer_chat)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n{test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\n总计: {passed}/{total} 测试通过")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
