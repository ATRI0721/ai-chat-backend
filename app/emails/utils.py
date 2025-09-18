from random import randint
import re
import redis

from app.core.config import settings

_redis = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

def set_email_verification_code(email: str, code: str) -> None:
    _redis.set(email, code, ex=settings.EMAIL_VALIDATE_TOKEN_EXPIRE_MINUTES)  # 10 minutes

def get_email_verification_code(email: str):
    return _redis.get(email)

def is_valid_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def generate_verification_code() -> str:
    return str(randint(100000,999999))

def is_valid_verification_code(code: str) -> bool:
    return len(code) == 6 and code.isdigit()

def verify_email(email: str, verification_code: str) -> bool:
    if not is_valid_email(email) or not is_valid_verification_code(verification_code):
        return False
    code = get_email_verification_code(email)
    if not code or code.decode()!= verification_code:
        return False
    return True
