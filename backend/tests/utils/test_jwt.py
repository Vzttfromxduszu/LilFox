import pytest
from datetime import datetime, timedelta
from src.utils.jwt import create_access_token, decode_access_token
from src.config import settings

def test_create_access_token():
    """
    Test that JWT access token creation works correctly
    """
    data = {"sub": "testuser"}
    
    # Test with default expiration
    token = create_access_token(data)
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0
    
    # Test with custom expiration
    expires_delta = timedelta(minutes=1)
    token_with_expiry = create_access_token(data, expires_delta)
    assert token_with_expiry is not None
    assert isinstance(token_with_expiry, str)

def test_decode_access_token():
    """
    Test that JWT access token decoding works correctly
    """
    data = {"sub": "testuser"}
    
    # Create a token and decode it
    token = create_access_token(data)
    decoded = decode_access_token(token)
    
    # Check that decoded data contains the original data and expiration
    assert decoded is not None
    assert isinstance(decoded, dict)
    assert decoded["sub"] == data["sub"]
    assert "exp" in decoded
    
    # Check that expiration time is in the future
    exp_time = datetime.fromtimestamp(decoded["exp"])
    assert exp_time > datetime.utcnow()
    
    # Test that token with invalid signature raises exception
    invalid_token = token + "invalid"
    with pytest.raises(Exception):
        decode_access_token(invalid_token)
