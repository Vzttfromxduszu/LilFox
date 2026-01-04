import pytest
from src.utils.password import hash_password, verify_password

def test_hash_password():
    """
    Test that password hashing works correctly
    """
    password = "testpassword123"
    hashed = hash_password(password)
    
    # Check that hash is generated and is not the same as the original password
    assert hashed is not None
    assert hashed != password
    assert len(hashed) > 0
    
    # Check that hashing the same password twice produces different results (salted hash)
    hashed2 = hash_password(password)
    assert hashed != hashed2

def test_verify_password():
    """
    Test that password verification works correctly
    """
    password = "testpassword123"
    hashed = hash_password(password)
    
    # Check that correct password is verified successfully
    assert verify_password(password, hashed) is True
    
    # Check that incorrect password fails verification
    assert verify_password("wrongpassword", hashed) is False
    
    # Check that empty password fails verification
    assert verify_password("", hashed) is False
    
    # Check that hashing and verifying with different encodings works
    password_with_unicode = "密码123"
    hashed_unicode = hash_password(password_with_unicode)
    assert verify_password(password_with_unicode, hashed_unicode) is True
