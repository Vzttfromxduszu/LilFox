from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from src.models import User
from src.schemas import UserCreate, UserLogin, UserUpdate, PasswordChange, PasswordReset
from src.utils import hash_password, verify_password, create_access_token

class AuthService:
    """Authentication service for user registration and login"""
    
    @staticmethod
    def register_user(db: Session, user_data: UserCreate) -> User:
        """
        Register a new user
        
        Args:
            db: Database session
            user_data: User creation data
            
        Returns:
            Created user object
            
        Raises:
            HTTPException: If username or email already exists
        """
        try:
            # Check if username or email already exists
            existing_user = db.query(User).filter(
                (User.username == user_data.username) | 
                (User.email == user_data.email)
            ).first()
            
            if existing_user:
                if existing_user.username == user_data.username:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username already registered"
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already registered"
                    )
            
            # Create new user
            hashed_password = hash_password(user_data.password)
            db_user = User(
                username=user_data.username,
                email=user_data.email,
                hashed_password=hashed_password
            )
            
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            return db_user
            
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already registered"
            )
    
    @staticmethod
    def login_user(db: Session, login_data: UserLogin) -> tuple[User, str]:
        """
        Login a user
        
        Args:
            db: Database session
            login_data: User login data
            
        Returns:
            Tuple of user object and access token
            
        Raises:
            HTTPException: If authentication fails
        """
        # Find user by username or email
        user = db.query(User).filter(
            (User.username == login_data.username_or_email) | 
            (User.email == login_data.username_or_email)
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Verify password
        if not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Create access token
        access_token = create_access_token(data={"sub": user.username})
        
        return user, access_token
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User:
        """
        Get user by ID
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            User object
            
        Raises:
            HTTPException: If user not found
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> User:
        """
        Get user by username
        
        Args:
            db: Database session
            username: Username
            
        Returns:
            User object
            
        Raises:
            HTTPException: If user not found
        """
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    
    @staticmethod
    def update_user(db: Session, user_id: int, user_data: UserUpdate) -> User:
        """
        Update user information
        
        Args:
            db: Database session
            user_id: User ID
            user_data: User update data
            
        Returns:
            Updated user object
            
        Raises:
            HTTPException: If user not found or username/email already exists
        """
        # Get user by ID
        user = AuthService.get_user_by_id(db, user_id)
        
        # Check if username is being updated and already exists
        if user_data.username and user_data.username != user.username:
            existing_user = db.query(User).filter(User.username == user_data.username).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists"
                )
            user.username = user_data.username
        
        # Check if email is being updated and already exists
        if user_data.email and user_data.email != user.email:
            existing_user = db.query(User).filter(User.email == user_data.email).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )
            user.email = user_data.email
        
        # Commit changes
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def delete_user(db: Session, user_id: int) -> None:
        """
        Delete user account
        
        Args:
            db: Database session
            user_id: User ID
            
        Raises:
            HTTPException: If user not found
        """
        # Get user by ID
        user = AuthService.get_user_by_id(db, user_id)
        
        # Delete user
        db.delete(user)
        db.commit()
    
    @staticmethod
    def change_password(db: Session, user_id: int, password_data: PasswordChange) -> User:
        """
        Change user password
        
        Args:
            db: Database session
            user_id: User ID
            password_data: Password change data
            
        Returns:
            Updated user object
            
        Raises:
            HTTPException: If user not found or current password is incorrect
        """
        # Get user by ID
        user = AuthService.get_user_by_id(db, user_id)
        
        # Verify current password
        if not verify_password(password_data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )
        
        # Update password
        user.hashed_password = hash_password(password_data.new_password)
        
        # Commit changes
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def reset_password(db: Session, user_id: int, new_password: str) -> User:
        """
        Reset user password (for forgot password scenario)
        
        Args:
            db: Database session
            user_id: User ID
            new_password: New password
            
        Returns:
            Updated user object
            
        Raises:
            HTTPException: If user not found
        """
        # Get user by ID
        user = AuthService.get_user_by_id(db, user_id)
        
        # Update password
        user.hashed_password = hash_password(new_password)
        
        # Commit changes
        db.commit()
        db.refresh(user)
        
        return user
