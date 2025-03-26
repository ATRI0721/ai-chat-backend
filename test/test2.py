from datetime import datetime, timedelta, timezone
from typing import List
import uuid

import redis
from sqlmodel import Field, SQLModel



# print(datetime.now(timezone.utc) + timedelta(minutes=60))

# print(list([T1(id=1, name="t1"), T1(id=2, name="t2"), T1(id=3, name="t3")]))

def generate_id() -> str:
    return str(uuid.uuid4())

class T1(SQLModel):
    id: str = Field(default_factory=generate_id)
    name: str

class T2(SQLModel):
    name: str


def f(id: str = generate_id()) -> str:
    return id

_redis = redis.Redis()

def set_email_verification_code(email: str, code: str) -> None:
    _redis.set(email, code, ex=600)  # 10 minutes

def get_email_verification_code(email: str):
    return _redis.get(email)

set_email_verification_code("test@test.com", "123456")
print(get_email_verification_code("test@test.com").decode())

