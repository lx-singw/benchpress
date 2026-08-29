import time
from token_manager import generate_token, verify_token

def test_token_valid():
    secret = "test-secret-key"
    now = int(time.time())
    token = generate_token("user_123", now + 100, secret)
    assert verify_token(token, secret, now) is True

def test_token_expired():
    secret = "test-secret-key"
    now = int(time.time())
    token = generate_token("user_123", now - 10, secret)
    assert verify_token(token, secret, now) is False

def test_token_tampered():
    secret = "test-secret-key"
    now = int(time.time())
    token = generate_token("user_123", now + 100, secret)
    tampered = token[:-4] + "ffff"
    assert verify_token(tampered, secret, now) is False
