import hmac
import hashlib

def generate_token(user_id: str, expires_at: int, secret_key: str) -> str:
    payload = f"{user_id}:{expires_at}"
    sig = hmac.new(secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]
    return f"{payload}:{sig}"

def verify_token(token: str, secret_key: str, current_time: int) -> bool:
    try:
        parts = token.split(":")
        if len(parts) != 3:
            return False
        user_id, expires_str, sig = parts
        expires_at = int(expires_str)
        if current_time > expires_at:
            return False
        payload = f"{user_id}:{expires_at}"
        expected_sig = hmac.new(secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]
        return hmac.compare_digest(sig, expected_sig)
    except Exception:
        return False
