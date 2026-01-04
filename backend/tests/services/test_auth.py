import pytest
from fastapi import HTTPException
from src.services.auth import AuthService
from src.schemas import UserCreate, UserLogin
from src.models import User

def test_register_user(db_session):
    """
    Test user registration functionality
    """
    # Create test user data
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="testpassword123"
    )
    
    # Register the user
    user = AuthService.register_user(db_session, user_data)
    
    # Verify user was created successfully
    assert user is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.hashed_password is not None
    assert user.hashed_password != "testpassword123"
    assert user.id is not None
    assert user.created_at is not None

def test_register_user_duplicate_username(db_session):
    """
    Test that registering a user with duplicate username raises an HTTPException
    """
    # Create and register first user
    user_data1 = UserCreate(
        username="testuser",
        email="test1@example.com",
        password="testpassword123"
    )
    AuthService.register_user(db_session, user_data1)
    
    # Try to register another user with the same username
    user_data2 = UserCreate(
        username="testuser",
        email="test2@example.com",
        password="testpassword123"
    )
    
    with pytest.raises(HTTPException) as excinfo:
        AuthService.register_user(db_session, user_data2)
    
    assert excinfo.value.status_code == 400
    assert "Username already registered" in str(excinfo.value.detail)

def test_register_user_duplicate_email(db_session):
    """
    Test that registering a user with duplicate email raises an HTTPException
    """
    # Create and register first user
    user_data1 = UserCreate(
        username="testuser1",
        email="test@example.com",
        password="testpassword123"
    )
    AuthService.register_user(db_session, user_data1)
    
    # Try to register another user with the same email
    user_data2 = UserCreate(
        username="testuser2",
        email="test@example.com",
        password="testpassword123"
    )
    
    with pytest.raises(HTTPException) as excinfo:
        AuthService.register_user(db_session, user_data2)
    
    assert excinfo.value.status_code == 400
    assert "Email already registered" in str(excinfo.value.detail)

def test_login_user_with_username(db_session):
    """
    Test user login with username functionality
    """
    # Register a test user
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="testpassword123"
    )
    AuthService.register_user(db_session, user_data)
    
    # Login with username
    login_data = UserLogin(
        username_or_email="testuser",
        password="testpassword123"
    )
    
    user, token = AuthService.login_user(db_session, login_data)
    
    # Verify login was successful
    assert user is not None
    assert user.username == "testuser"
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0

def test_login_user_with_email(db_session):
    """
    Test user login with email functionality
    """
    # Register a test user
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="testpassword123"
    )
    AuthService.register_user(db_session, user_data)
    
    # Login with email
    login_data = UserLogin(
        username_or_email="test@example.com",
        password="testpassword123"
    )
    
    user, token = AuthService.login_user(db_session, login_data)
    
    # Verify login was successful
    assert user is not None
    assert user.email == "test@example.com"
    assert token is not None
    assert isinstance(token, str)

def test_login_user_invalid_credentials(db_session):
    """
    Test that login with invalid credentials raises an HTTPException
    """
    # Register a test user
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="testpassword123"
    )
    AuthService.register_user(db_session, user_data)
    
    # Try to login with wrong password
    login_data = UserLogin(
        username_or_email="testuser",
        password="wrongpassword"
    )
    
    with pytest.raises(HTTPException) as excinfo:
        AuthService.login_user(db_session, login_data)
    
    assert excinfo.value.status_code == 401
    assert "Invalid credentials" in str(excinfo.value.detail)

def test_login_user_nonexistent_user(db_session):
    """
    Test that login with non-existent user raises an HTTPException
    """
    # Try to login with non-existent username
    login_data = UserLogin(
        username_or_email="nonexistentuser",
        password="testpassword123"
    )
    
    with pytest.raises(HTTPException) as excinfo:
        AuthService.login_user(db_session, login_data)
    
    assert excinfo.value.status_code == 401
    assert "Invalid credentials" in str(excinfo.value.detail)
