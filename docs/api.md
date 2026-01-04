# LilFox API 文档

## 目录

- [概述](#概述)
- [认证](#认证)
- [用户管理](#用户管理)
- [模型服务](#模型服务)
- [错误处理](#错误处理)
- [限流](#限流)

## 概述

LilFox API 提供统一的大模型 Web 应用接口，包含用户认证、模型调用等功能。

### 基础信息

- **Base URL**: `http://localhost:8080/api`
- **Content-Type**: `application/json`
- **API Version**: v1

### 通用响应格式

成功响应:
```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

错误响应:
```json
{
  "code": 400,
  "message": "error message",
  "data": null
}
```

## 认证

### 1. 用户注册

注册新用户账号。

**请求**
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "testuser",
  "email": "test@example.com",
  "password": "Password123"
}
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名，3-20个字符 |
| email | string | 是 | 邮箱地址 |
| password | string | 是 | 密码，至少8个字符，包含大小写字母和数字 |

**响应**
```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### 2. 用户登录

使用用户名或邮箱登录。

**请求**
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "testuser",
  "password": "Password123"
}
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名或邮箱 |
| password | string | 是 | 密码 |

**响应**
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

### 3. 获取当前用户信息

获取当前登录用户的详细信息。

**请求**
```http
GET /api/v1/users/me
Authorization: Bearer <access_token>
```

**响应**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

## 用户管理

### 1. 更新用户信息

更新当前用户的信息。

**请求**
```http
PUT /api/v1/users/me
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "username": "newusername",
  "email": "newemail@example.com"
}
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 否 | 新用户名 |
| email | string | 否 | 新邮箱地址 |

**响应**
```json
{
  "code": 200,
  "message": "更新成功",
  "data": {
    "id": 1,
    "username": "newusername",
    "email": "newemail@example.com",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

### 2. 修改密码

修改当前用户的密码。

**请求**
```http
POST /api/v1/users/me/change-password
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "old_password": "Password123",
  "new_password": "NewPassword456"
}
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| old_password | string | 是 | 当前密码 |
| new_password | string | 是 | 新密码 |

**响应**
```json
{
  "code": 200,
  "message": "密码修改成功",
  "data": null
}
```

### 3. 删除账户

删除当前用户的账户。

**请求**
```http
DELETE /api/v1/users/me
Authorization: Bearer <access_token>
```

**响应**
```json
{
  "code": 200,
  "message": "账户删除成功",
  "data": null
}
```

## 模型服务

### 1. 发送消息

向大模型发送消息并获取回复。

**请求**
```http
POST /api/v1/llm/chat
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "provider": "openai",
  "model": "gpt-3.5-turbo",
  "messages": [
    {
      "role": "user",
      "content": "你好，请介绍一下你自己"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| provider | string | 是 | 模型提供商 |
| model | string | 是 | 模型名称 |
| messages | array | 是 | 消息列表 |
| temperature | float | 否 | 温度参数，0-2 |
| max_tokens | int | 否 | 最大token数 |

**响应**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "chatcmpl-xxx",
    "object": "chat.completion",
    "created": 1234567890,
    "model": "gpt-3.5-turbo",
    "choices": [
      {
        "index": 0,
        "message": {
          "role": "assistant",
          "content": "你好！我是一个AI助手..."
        },
        "finish_reason": "stop"
      }
    ],
    "usage": {
      "prompt_tokens": 10,
      "completion_tokens": 20,
      "total_tokens": 30
    }
  }
}
```

### 2. 流式聊天

使用流式方式获取模型回复。

**请求**
```http
POST /api/v1/llm/chat/stream
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "provider": "openai",
  "model": "gpt-3.5-turbo",
  "messages": [
    {
      "role": "user",
      "content": "写一首诗"
    }
  ]
}
```

**响应**

Server-Sent Events (SSE) 格式:

```
data: {"choices":[{"delta":{"content":"春"}}]}

data: {"choices":[{"delta":{"content":"风"}}]}

data: {"choices":[{"delta":{"content":"拂"}}]}

data: [DONE]
```

### 3. 使用提示词模板

使用预定义的提示词模板。

**请求**
```http
POST /api/v1/llm/template
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "template_name": "code_review",
  "provider": "openai",
  "model": "gpt-3.5-turbo",
  "parameters": {
    "code": "def hello():\n    print('Hello, World!')",
    "language": "python"
  }
}
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| template_name | string | 是 | 模板名称 |
| provider | string | 是 | 模型提供商 |
| model | string | 是 | 模型名称 |
| parameters | object | 是 | 模板参数 |

**响应**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "content": "代码审查结果...",
    "usage": {
      "prompt_tokens": 50,
      "completion_tokens": 100,
      "total_tokens": 150
    }
  }
}
```

## 错误处理

### 错误码

| 错误码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用 |

### 错误响应示例

```json
{
  "code": 400,
  "message": "用户名已存在",
  "data": {
    "field": "username",
    "error": "duplicate"
  }
}
```

## 限流

API 实施了速率限制以防止滥用。

### 限流规则

- 默认限制: 100 请求/分钟
- 认证用户: 60 请求/分钟
- 未认证用户: 30 请求/分钟

### 限流响应头

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1234567890
```

### 限流错误响应

```json
{
  "code": 429,
  "message": "请求过于频繁，请稍后再试",
  "data": {
    "retry_after": 60
  }
}
```
