from typing import Optional, Dict, Any
import asyncio
import time
import uuid
from datetime import datetime

from ..monitoring.logger import get_logger

logger = get_logger(__name__)


def generate_request_id() -> str:
    """生成请求ID"""
    return str(uuid.uuid4())


def generate_trace_id() -> str:
    """生成追踪ID"""
    return str(uuid.uuid4())


def get_timestamp() -> str:
    """获取时间戳"""
    return datetime.utcnow().isoformat()


def get_timestamp_ms() -> int:
    """获取毫秒时间戳"""
    return int(time.time() * 1000)


def format_duration_ms(start_time: float, end_time: Optional[float] = None) -> float:
    """格式化持续时间（毫秒）"""
    end = end_time or time.time()
    return (end - start_time) * 1000


async def retry_async(
    func,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """异步重试"""
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return await func()
        except exceptions as e:
            last_exception = e
            if attempt < max_retries - 1:
                sleep_time = delay * (backoff_factor ** attempt)
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed: {e}. "
                    f"Retrying in {sleep_time:.2f}s"
                )
                await asyncio.sleep(sleep_time)
    
    raise last_exception


def safe_json_loads(data: str, default: Any = None) -> Any:
    """安全的JSON解析"""
    try:
        import json
        return json.loads(data)
    except Exception as e:
        logger.error(f"Error parsing JSON: {e}")
        return default


def safe_json_dumps(data: Any, default: str = "{}") -> str:
    """安全的JSON序列化"""
    try:
        import json
        return json.dumps(data)
    except Exception as e:
        logger.error(f"Error serializing JSON: {e}")
        return default


def mask_sensitive_data(data: Dict[str, Any], fields: list) -> Dict[str, Any]:
    """脱敏敏感数据"""
    masked = data.copy()
    
    for field in fields:
        if field in masked:
            value = masked[field]
            if isinstance(value, str):
                masked[field] = value[:2] + "******" + value[-2:] if len(value) > 4 else "******"
            else:
                masked[field] = "******"
    
    return masked


def extract_client_ip(request) -> str:
    """提取客户端IP"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host if request.client else "unknown"


def get_user_agent(request) -> str:
    """获取用户代理"""
    return request.headers.get("User-Agent", "unknown")


def parse_content_type(content_type: Optional[str]) -> Dict[str, str]:
    """解析Content-Type"""
    if not content_type:
        return {"type": "application/octet-stream"}
    
    parts = content_type.split(";")
    result = {"type": parts[0].strip()}
    
    for part in parts[1:]:
        if "=" in part:
            key, value = part.split("=", 1)
            result[key.strip().lower()] = value.strip().strip('"')
    
    return result


def is_json_content_type(content_type: Optional[str]) -> bool:
    """检查是否为JSON内容类型"""
    if not content_type:
        return False
    
    parsed = parse_content_type(content_type)
    return parsed["type"] in [
        "application/json",
        "application/ld+json",
        "application/x-json"
    ]


def build_response_data(
    success: bool,
    data: Any = None,
    message: str = "OK",
    code: int = 200,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """构建响应数据"""
    response = {
        "success": success,
        "code": code,
        "message": message,
        "data": data,
        "timestamp": get_timestamp()
    }
    
    if request_id:
        response["request_id"] = request_id
    
    return response


def build_error_response(
    error: str,
    code: int = 500,
    request_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """构建错误响应"""
    response = {
        "success": False,
        "code": code,
        "error": error,
        "timestamp": get_timestamp()
    }
    
    if request_id:
        response["request_id"] = request_id
    
    if details:
        response["details"] = details
    
    return response


def validate_url(url: str) -> bool:
    """验证URL"""
    import re
    pattern = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$',
        re.IGNORECASE
    )
    return pattern.match(url) is not None


def sanitize_path(path: str) -> str:
    """清理路径"""
    import os
    path = os.path.normpath(path)
    path = path.replace("\\", "/")
    return path


def truncate_string(s: str, max_length: int = 100, suffix: str = "...") -> str:
    """截断字符串"""
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


class Timer:
    """计时器"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """开始计时"""
        self.start_time = time.time()
        self.end_time = None
    
    def stop(self) -> float:
        """停止计时并返回持续时间（毫秒）"""
        self.end_time = time.time()
        return self.elapsed()
    
    def elapsed(self) -> float:
        """获取已过时间（毫秒）"""
        if self.start_time is None:
            return 0.0
        end = self.end_time or time.time()
        return (end - self.start_time) * 1000
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


class AsyncTimer:
    """异步计时器"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    async def start(self):
        """开始计时"""
        self.start_time = time.time()
        self.end_time = None
    
    async def stop(self) -> float:
        """停止计时并返回持续时间（毫秒）"""
        self.end_time = time.time()
        return self.elapsed()
    
    def elapsed(self) -> float:
        """获取已过时间（毫秒）"""
        if self.start_time is None:
            return 0.0
        end = self.end_time or time.time()
        return (end - self.start_time) * 1000
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()
