from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.config.database import get_db
from src.schemas import UserCreate, UserLogin, UserResponse, Token, UserUpdate, PasswordChange, PasswordResetRequest, PasswordReset
from src.services.auth import AuthService
from src.utils import get_current_user
from src.models import User

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        Created user information
    """
    try:
        user = AuthService.register_user(db, user_data)
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    Login a user
    
    Args:
        login_data: User login data
        db: Database session
        
    Returns:
        Access token for authentication
    """
    try:
        user, access_token = AuthService.login_user(db, login_data)
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user information
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user_info(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current authenticated user information
    
    Args:
        user_data: User update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated user information
    """
    try:
        updated_user = AuthService.update_user(db, current_user.id, user_data)
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user information: {str(e)}"
        )


@router.post("/change-password")
async def change_current_user_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change password for current authenticated user
    
    Args:
        password_data: Password change data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    try:
        AuthService.change_password(db, current_user.id, password_data)
        return {"message": "Password changed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change password: {str(e)}"
        )


@router.post("/reset-password/request")
async def request_password_reset(
    reset_request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset (forgot password scenario)
    
    Args:
        reset_request: Password reset request data
        db: Database session
        
    Returns:
        Success message (in real app, would send reset token to email)
    """
    try:
        # In real application, this would generate a reset token and send it to the user's email
        # For simplicity, we'll just return a success message
        user = db.query(User).filter(User.email == reset_request.email).first()
        if not user:
            # For security reasons, we don't reveal if the email exists
            return {"message": "Password reset request received"}
        
        # Generate a dummy reset token (in real app, this would be a secure token)
        # reset_token = generate_reset_token(user.id)
        # send_email(user.email, "Password Reset", f"Your reset token: {reset_token}")
        
        return {"message": "Password reset request received"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process password reset request: {str(e)}"
        )


@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordReset,
    db: Session = Depends(get_db)
):
    """
    Reset password using reset token (forgot password scenario)
    
    Args:
        reset_data: Password reset data
        db: Database session
        
    Returns:
        Success message
    """
    try:
        # In real application, this would verify the reset token
        # For simplicity, we'll just find the user by email and reset the password
        user = db.query(User).filter(User.email == reset_data.email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token or email"
            )
        
        # In real app, we would verify the reset token here
        # if not verify_reset_token(reset_data.token, user.id):
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="Invalid or expired reset token"
        #     )
        
        # Reset password
        AuthService.reset_password(db, user.id, reset_data.new_password)
        
        return {"message": "Password reset successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset password: {str(e)}"
        )


@router.delete("/me")
async def delete_current_user_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete current authenticated user account
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    try:
        AuthService.delete_user(db, current_user.id)
        return {"message": "Account deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )
