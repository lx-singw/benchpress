import time
from .token_manager import generate_token, verify_token

class AuthService:
    def __init__(self, secret_key: str, ttl_seconds: int = 3600):
        self.secret_key = secret_key
        self.ttl_seconds = ttl_seconds

    def issue(self, user_id: str) -> str:
        expires_at = int(time.time()) + self.ttl_seconds
        return generate_token(user_id, expires_at, self.secret_key)

    def validate(self, token: str) -> bool:
        current_time = int(time.time())
        return verify_token(token, self.secret_key, current_time)
