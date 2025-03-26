import time
import uuid
import random


def generate_uuid() -> str:
    return str(uuid.uuid4())

def get_time() -> int:
    return int(round(time.time() * 1000))

def generate_code(length: int = 6) -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(length))

