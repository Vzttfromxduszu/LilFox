from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(..., min_length=8, max_length=100, 
                        description="Password must contain at least 8 characters")

class UserLogin(BaseModel):
    """User login schema"""
    username_or_email: str = Field(..., description="Username or email")
    password: str

class UserUpdate(BaseModel):
    """User update schema"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None

class PasswordChange(BaseModel):
    """Password change schema"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100, 
                            description="Password must contain at least 8 characters")

class PasswordResetRequest(BaseModel):
    """Password reset request schema"""
    email: EmailStr

class PasswordReset(BaseModel):
    """Password reset schema"""
    email: EmailStr
    token: str
    new_password: str = Field(..., min_length=8, max_length=100, 
                            description="Password must contain at least 8 characters")

class UserResponse(UserBase):
    """User response schema"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    """Token response schema"""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Token data schema"""
    username: Optional[str] = None
