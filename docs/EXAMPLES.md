# LilFox API 使用示例

## Python 示例

### 1. 安装依赖

```bash
pip install requests httpx
```

### 2. 基础客户端

```python
import requests
from typing import Optional, Dict, Any


class LilFoxClient:
    """LilFox API 客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8080/api"):
        self.base_url = base_url
        self.access_token: Optional[str] = None
    
    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """发送HTTP请求"""
        url = f"{self.base_url}{endpoint}"
        
        if headers is None:
            headers = {}
        
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        response = requests.request(
            method=method,
            url=url,
            json=data,
            headers=headers
        )
        
        response.raise_for_status()
        return response.json()
    
    def register(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """用户注册"""
        data = {
            "username": username,
            "email": email,
            "password": password
        }
        return self._request("POST", "/v1/auth/register", data)
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """用户登录"""
        data = {
            "username": username,
            "password": password
        }
        result = self._request("POST", "/v1/auth/login", data)
        self.access_token = result["data"]["access_token"]
        return result
    
    def get_user_info(self) -> Dict[str, Any]:
        """获取用户信息"""
        return self._request("GET", "/v1/users/me")
    
    def update_user_info(self, username: Optional[str] = None, email: Optional[str] = None) -> Dict[str, Any]:
        """更新用户信息"""
        data = {}
        if username:
            data["username"] = username
        if email:
            data["email"] = email
        return self._request("PUT", "/v1/users/me", data)
    
    def change_password(self, old_password: str, new_password: str) -> Dict[str, Any]:
        """修改密码"""
        data = {
            "old_password": old_password,
            "new_password": new_password
        }
        return self._request("POST", "/v1/users/me/change-password", data)
    
    def chat(
        self,
        provider: str,
        model: str,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """发送聊天消息"""
        data = {
            "provider": provider,
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        return self._request("POST", "/v1/llm/chat", data)
    
    def use_template(
        self,
        template_name: str,
        provider: str,
        model: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """使用提示词模板"""
        data = {
            "template_name": template_name,
            "provider": provider,
            "model": model,
            "parameters": parameters
        }
        return self._request("POST", "/v1/llm/template", data)
```

### 3. 使用示例

#### 用户认证

```python
client = LilFoxClient()

# 注册新用户
try:
    result = client.register(
        username="testuser",
        email="test@example.com",
        password="Password123"
    )
    print("注册成功:", result)
except Exception as e:
    print("注册失败:", e)

# 登录
try:
    result = client.login(
        username="testuser",
        password="Password123"
    )
    print("登录成功:", result)
    print("Access Token:", client.access_token)
except Exception as e:
    print("登录失败:", e)

# 获取用户信息
try:
    result = client.get_user_info()
    print("用户信息:", result)
except Exception as e:
    print("获取用户信息失败:", e)
```

#### 聊天对话

```python
import asyncio
import httpx


async def chat_with_stream():
    """流式聊天示例"""
    client = LilFoxClient()
    client.login("testuser", "Password123")
    
    async with httpx.AsyncClient() as http_client:
        response = await http_client.post(
            "http://localhost:8080/api/v1/llm/chat/stream",
            json={
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "user", "content": "写一首关于春天的诗"}
                ]
            },
            headers={
                "Authorization": f"Bearer {client.access_token}"
            }
        )
        
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data = line[6:]
                if data == "[DONE]":
                    break
                print(data)


# 运行流式聊天
asyncio.run(chat_with_stream())
```

#### 使用提示词模板

```python
client = LilFoxClient()
client.login("testuser", "Password123")

# 使用代码审查模板
result = client.use_template(
    template_name="code_review",
    provider="openai",
    model="gpt-3.5-turbo",
    parameters={
        "code": """
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total
        """,
        "language": "python"
    }
)

print("代码审查结果:", result["data"]["content"])
```

## JavaScript/TypeScript 示例

### 1. 安装依赖

```bash
npm install axios
```

### 2. 基础客户端

```typescript
interface ApiResponse<T = any> {
  code: number;
  message: string;
  data: T;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

interface ChatMessage {
  role: string;
  content: string;
}

class LilFoxClient {
  private baseUrl: string;
  private accessToken: string | null = null;

  constructor(baseUrl: string = "http://localhost:8080/api") {
    this.baseUrl = baseUrl;
  }

  private async request<T = any>(
    method: string,
    endpoint: string,
    data?: any
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    if (this.accessToken) {
      headers["Authorization"] = `Bearer ${this.accessToken}`;
    }

    const response = await fetch(url, {
      method,
      headers,
      body: data ? JSON.stringify(data) : undefined,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async register(
    username: string,
    email: string,
    password: string
  ): Promise<ApiResponse> {
    return this.request("POST", "/v1/auth/register", {
      username,
      email,
      password,
    });
  }

  async login(
    username: string,
    password: string
  ): Promise<ApiResponse<LoginResponse>> {
    const result = await this.request<LoginResponse>("POST", "/v1/auth/login", {
      username,
      password,
    });
    this.accessToken = result.data.access_token;
    return result;
  }

  async getUserInfo(): Promise<ApiResponse> {
    return this.request("GET", "/v1/users/me");
  }

  async updateUserInfo(
    username?: string,
    email?: string
  ): Promise<ApiResponse> {
    const data: any = {};
    if (username) data.username = username;
    if (email) data.email = email;
    return this.request("PUT", "/v1/users/me", data);
  }

  async changePassword(
    oldPassword: string,
    newPassword: string
  ): Promise<ApiResponse> {
    return this.request("POST", "/v1/users/me/change-password", {
      old_password: oldPassword,
      new_password: newPassword,
    });
  }

  async chat(
    provider: string,
    model: string,
    messages: ChatMessage[],
    temperature: number = 0.7,
    maxTokens: number = 1000
  ): Promise<ApiResponse> {
    return this.request("POST", "/v1/llm/chat", {
      provider,
      model,
      messages,
      temperature,
      max_tokens: maxTokens,
    });
  }

  async useTemplate(
    templateName: string,
    provider: string,
    model: string,
    parameters: Record<string, any>
  ): Promise<ApiResponse> {
    return this.request("POST", "/v1/llm/template", {
      template_name: templateName,
      provider,
      model,
      parameters,
    });
  }

  async chatStream(
    provider: string,
    model: string,
    messages: ChatMessage[],
    onChunk: (chunk: string) => void
  ): Promise<void> {
    const url = `${this.baseUrl}/v1/llm/chat/stream`;
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${this.accessToken}`,
      },
      body: JSON.stringify({ provider, model, messages }),
    });

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error("Response body is not readable");
    }

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split("\n");

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.slice(6);
          if (data === "[DONE]") return;
          onChunk(data);
        }
      }
    }
  }
}
```

### 3. 使用示例

#### 用户认证

```typescript
const client = new LilFoxClient();

// 注册新用户
async function registerUser() {
  try {
    const result = await client.register(
      "testuser",
      "test@example.com",
      "Password123"
    );
    console.log("注册成功:", result);
  } catch (error) {
    console.error("注册失败:", error);
  }
}

// 登录
async function loginUser() {
  try {
    const result = await client.login("testuser", "Password123");
    console.log("登录成功:", result);
  } catch (error) {
    console.error("登录失败:", error);
  }
}

// 获取用户信息
async function getUserInfo() {
  try {
    const result = await client.getUserInfo();
    console.log("用户信息:", result);
  } catch (error) {
    console.error("获取用户信息失败:", error);
  }
}
```

#### 聊天对话

```typescript
async function chatExample() {
  const client = new LilFoxClient();
  await client.login("testuser", "Password123");

  try {
    const result = await client.chat(
      "openai",
      "gpt-3.5-turbo",
      [
        { role: "user", content: "你好，请介绍一下你自己" }
      ]
    );
    console.log("聊天结果:", result.data.choices[0].message.content);
  } catch (error) {
    console.error("聊天失败:", error);
  }
}

// 流式聊天
async function chatStreamExample() {
  const client = new LilFoxClient();
  await client.login("testuser", "Password123");

  try {
    await client.chatStream(
      "openai",
      "gpt-3.5-turbo",
      [
        { role: "user", content: "写一首关于春天的诗" }
      ],
      (chunk) => {
        console.log("收到消息块:", chunk);
      }
    );
  } catch (error) {
    console.error("流式聊天失败:", error);
  }
}
```

#### 使用提示词模板

```typescript
async function useTemplateExample() {
  const client = new LilFoxClient();
  await client.login("testuser", "Password123");

  try {
    const result = await client.useTemplate(
      "code_review",
      "openai",
      "gpt-3.5-turbo",
      {
        code: `
function calculateSum(numbers) {
  let total = 0;
  for (const num of numbers) {
    total += num;
  }
  return total;
}
        `,
        language: "javascript"
      }
    );
    console.log("代码审查结果:", result.data.content);
  } catch (error) {
    console.error("使用模板失败:", error);
  }
}
```

## cURL 示例

### 用户注册

```bash
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "Password123"
  }'
```

### 用户登录

```bash
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "Password123"
  }'
```

### 获取用户信息

```bash
curl -X GET http://localhost:8080/api/v1/users/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 发送聊天消息

```bash
curl -X POST http://localhost:8080/api/v1/llm/chat \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

## 错误处理

### Python

```python
try:
    result = client.chat(
        provider="openai",
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello"}]
    )
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 401:
        print("未认证，请先登录")
    elif e.response.status_code == 429:
        print("请求过于频繁，请稍后再试")
    else:
        print(f"请求失败: {e}")
except Exception as e:
    print(f"发生错误: {e}")
```

### JavaScript

```typescript
try {
  const result = await client.chat(
    "openai",
    "gpt-3.5-turbo",
    [{ role: "user", content: "Hello" }]
  );
} catch (error: any) {
  if (error.message.includes("401")) {
    console.error("未认证，请先登录");
  } else if (error.message.includes("429")) {
    console.error("请求过于频繁，请稍后再试");
  } else {
    console.error("发生错误:", error);
  }
}
```
