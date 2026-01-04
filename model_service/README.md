# LilFox Model Service

大模型交互服务，提供统一的接口与大模型进行交互，支持提示词管理、模型调用、响应解析等功能。

## 功能特性

- **提示词管理**: 支持模板定义、动态参数替换、提示词组合
- **大模型交互**: 支持主流大模型API调用（OpenAI等）
- **响应解析**: 支持结构化数据提取、错误处理、结果格式化
- **配置管理**: 支持API密钥配置、模型参数预设、环境切换
- **RESTful API**: 提供完整的HTTP API接口
- **模块化设计**: 代码可扩展性和可维护性强

## 项目结构

```
model_service/
├── src/
│   ├── config/           # 配置管理
│   │   ├── __init__.py
│   │   └── settings.py   # 配置设置
│   ├── prompts/          # 提示词管理
│   │   ├── __init__.py
│   │   └── template.py   # 提示词模板
│   ├── models/           # 大模型交互
│   │   ├── __init__.py
│   │   ├── base.py       # 抽象基类
│   │   └── openai.py     # OpenAI实现
│   ├── parsers/          # 响应解析
│   │   ├── __init__.py
│   │   └── response_parser.py  # 响应解析器
│   ├── services/         # 核心服务
│   │   ├── __init__.py
│   │   └── llm_service.py      # LLM服务
│   └── routes/           # API路由
│       ├── __init__.py
│       ├── schemas.py    # 数据模型
│       └── llm.py        # LLM路由
├── examples/             # 使用示例
│   ├── basic_usage.py    # 基础使用示例
│   └── api_usage.py      # API使用示例
├── tests/                # 测试
│   └── __init__.py
├── main.py               # 应用入口
├── requirements.txt      # 依赖列表
└── .env                  # 环境配置
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 文件为 `.env` 并配置相关参数：

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置你的API密钥：

```env
OPENAI_API_KEY=your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo
```

### 3. 启动服务

```bash
python main.py
```

服务将在 `http://localhost:8001` 启动。

### 4. 访问API文档

打开浏览器访问 `http://localhost:8001/docs` 查看完整的API文档。

## 使用示例

### 基础使用

```python
from src.services import llm_service
from src.models import Message

# 聊天
messages = [Message(role="user", content="你好")]
response = llm_service.chat(messages)
print(response.content)

# 文本补全
response = llm_service.complete("请解释什么是人工智能")
print(response.content)

# 使用模板
response = llm_service.chat_with_template(
    template_name="qa",
    template_params={
        "context": "Python是一种编程语言",
        "question": "Python是什么？"
    }
)
print(response.content)
```

### API调用

```python
import requests

# 聊天
response = requests.post("http://localhost:8001/api/v1/chat", json={
    "messages": [{"role": "user", "content": "你好"}]
})
print(response.json()["content"])

# 使用模板
response = requests.post("http://localhost:8001/api/v1/chat/template", json={
    "template_name": "qa",
    "template_params": {
        "context": "Python是一种编程语言",
        "question": "Python是什么？"
    }
})
print(response.json()["content"])
```

## API接口

### 健康检查

```
GET /api/v1/health
```

返回服务状态、可用模型和模板列表。

### 聊天

```
POST /api/v1/chat
```

发送消息列表进行对话。

**请求体**:
```json
{
  "messages": [
    {"role": "user", "content": "你好"}
  ],
  "provider": "openai",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

### 文本补全

```
POST /api/v1/complete
```

使用提示词进行文本补全。

**请求体**:
```json
{
  "prompt": "请解释什么是人工智能",
  "provider": "openai",
  "temperature": 0.7
}
```

### 模板聊天

```
POST /api/v1/chat/template
```

使用预定义模板进行对话。

**请求体**:
```json
{
  "template_name": "qa",
  "template_params": {
    "context": "背景信息",
    "question": "问题"
  }
}
```

### 列出模板

```
GET /api/v1/templates
```

返回所有可用的模板名称。

### 获取模板信息

```
GET /api/v1/templates/{template_name}
```

返回指定模板的详细信息。

### 注册模板

```
POST /api/v1/templates
```

注册自定义模板。

**请求体**:
```json
{
  "name": "custom_template",
  "template": "模板内容 {param}",
  "description": "模板描述"
}
```

### 解析响应

```
POST /api/v1/parse
```

解析大模型返回的内容。

**请求体**:
```json
{
  "content": "待解析的内容",
  "format_type": "json"
}
```

支持的格式类型: `json`, `code`, `list`, `key_value`, `markdown`, `text`

## 预定义模板

服务内置了以下常用模板：

- **qa**: 问答模板
- **summarization**: 文本摘要模板
- **translation**: 翻译模板
- **code_generation**: 代码生成模板
- **sentiment_analysis**: 情感分析模板
- **explanation**: 概念解释模板

## 配置说明

主要配置项（在 `.env` 文件中）：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| OPENAI_API_KEY | OpenAI API密钥 | - |
| OPENAI_BASE_URL | OpenAI API地址 | https://api.openai.com/v1 |
| OPENAI_MODEL | 默认模型 | gpt-3.5-turbo |
| OPENAI_TEMPERATURE | 温度参数 | 0.7 |
| OPENAI_MAX_TOKENS | 最大token数 | 1000 |
| API_HOST | API主机地址 | 0.0.0.0 |
| API_PORT | API端口 | 8001 |
| DEBUG | 调试模式 | False |

## 扩展开发

### 添加新的模型提供商

1. 在 `src/models/` 目录下创建新的模型实现文件
2. 继承 `BaseLLMModel` 类并实现抽象方法
3. 在 `LLMService._initialize_models()` 中添加初始化代码

### 添加新的解析格式

1. 在 `ResponseParser` 类中添加新的解析方法
2. 在 `__init__` 中注册到 `parsers` 字典

## 测试

运行基础使用示例：

```bash
python examples/basic_usage.py
```

运行API使用示例（需先启动服务）：

```bash
python examples/api_usage.py
```

## 注意事项

1. 请妥善保管API密钥，不要将 `.env` 文件提交到版本控制
2. 在生产环境中，建议使用环境变量管理敏感信息
3. 注意API调用频率限制，避免超出配额
4. 建议在生产环境中启用HTTPS和身份验证

## 许可证

MIT License