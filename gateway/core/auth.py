from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum
import jwt
from fastapi import Request, HTTPException, status
from passlib.context import CryptContext

from ..config.settings import settings
from ..monitoring.logger import get_logger

logger = get_logger(__name__)


class AuthType(Enum):
    """认证类型"""
    JWT = "jwt"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BASIC = "basic"


class AuthManager:
    """认证管理器"""
    
    def __init__(self):
        self.auth_type = AuthType(settings.AUTH_TYPE)
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.expire_minutes = settings.JWT_EXPIRE_MINUTES
        self.api_key_header = settings.API_KEY_HEADER
        
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.api_keys: Dict[str, Dict[str, Any]] = {}
        self.users: Dict[str, Dict[str, Any]] = {}
    
    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.expire_minutes)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        logger.debug(f"Created access token for user: {data.get('sub', 'unknown')}")
        
        return encoded_jwt
    
    def decode_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """解码访问令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.JWTError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def hash_password(self, password: str) -> str:
        """哈希密码"""
        return self.pwd_context.hash(password)
    
    def add_api_key(
        self,
        api_key: str,
        user_id: str,
        permissions: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """添加API密钥"""
        self.api_keys[api_key] = {
            "user_id": user_id,
            "permissions": permissions or [],
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat()
        }
        logger.info(f"Added API key for user: {user_id}")
    
    def remove_api_key(self, api_key: str):
        """移除API密钥"""
        if api_key in self.api_keys:
            user_id = self.api_keys[api_key]["user_id"]
            del self.api_keys[api_key]
            logger.info(f"Removed API key for user: {user_id}")
    
    def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """验证API密钥"""
        return self.api_keys.get(api_key)
    
    def add_user(
        self,
        user_id: str,
        username: str,
        password: str,
        permissions: Optional[List[str]] = None
    ):
        """添加用户"""
        self.users[user_id] = {
            "username": username,
            "password_hash": self.hash_password(password),
            "permissions": permissions or [],
            "created_at": datetime.utcnow().isoformat()
        }
        logger.info(f"Added user: {username}")
    
    def verify_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """验证用户"""
        for user_id, user_data in self.users.items():
            if user_data["username"] == username:
                if self.verify_password(password, user_data["password_hash"]):
                    return {"user_id": user_id, **user_data}
        return None
    
    async def authenticate_request(self, request: Request) -> Optional[Dict[str, Any]]:
        """认证请求"""
        if self.auth_type == AuthType.JWT:
            return await self._authenticate_jwt(request)
        elif self.auth_type == AuthType.API_KEY:
            return await self._authenticate_api_key(request)
        elif self.auth_type == AuthType.BASIC:
            return await self._authenticate_basic(request)
        else:
            logger.warning(f"Unsupported auth type: {self.auth_type}")
            return None
    
    async def _authenticate_jwt(self, request: Request) -> Optional[Dict[str, Any]]:
        """JWT认证"""
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning("Missing or invalid Authorization header")
            return None
        
        token = auth_header.split(" ")[1]
        payload = self.decode_access_token(token)
        
        if not payload:
            return None
        
        return {
            "user_id": payload.get("sub"),
            "username": payload.get("username"),
            "permissions": payload.get("permissions", []),
            "token_type": "jwt"
        }
    
    async def _authenticate_api_key(self, request: Request) -> Optional[Dict[str, Any]]:
        """API密钥认证"""
        api_key = request.headers.get(self.api_key_header)
        
        if not api_key:
            logger.warning(f"Missing {self.api_key_header} header")
            return None
        
        key_data = self.verify_api_key(api_key)
        
        if not key_data:
            logger.warning("Invalid API key")
            return None
        
        return {
            "user_id": key_data["user_id"],
            "permissions": key_data["permissions"],
            "token_type": "api_key"
        }
    
    async def _authenticate_basic(self, request: Request) -> Optional[Dict[str, Any]]:
        """Basic认证"""
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Basic "):
            logger.warning("Missing or invalid Authorization header")
            return None
        
        import base64
        try:
            credentials = base64.b64decode(auth_header.split(" ")[1]).decode()
            username, password = credentials.split(":")
            
            user_data = self.verify_user(username, password)
            
            if not user_data:
                return None
            
            return {
                "user_id": user_data["user_id"],
                "username": user_data["username"],
                "permissions": user_data["permissions"],
                "token_type": "basic"
            }
        except Exception as e:
            logger.error(f"Error parsing basic auth: {e}")
            return None
    
    def check_permission(self, user_permissions: List[str], required_permission: str) -> bool:
        """检查权限"""
        if "admin" in user_permissions:
            return True
        return required_permission in user_permissions
    
    def raise_unauthorized(self, detail: str = "Unauthorized"):
        """抛出未授权异常"""
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    def raise_forbidden(self, detail: str = "Forbidden"):
        """抛出禁止访问异常"""
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )
