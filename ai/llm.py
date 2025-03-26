import ollama
from core.config import settings

MODEL: str = settings.MODEL_NAME

client = ollama.AsyncClient()

def model_exists(model_name: str) -> bool:
    return model_name in [str(i['model']) for i in ollama.list().model_dump()["models"]]
    
async def generate_ai_response(messages: list[dict]):
    async for part in await client.chat(model=MODEL, messages=messages, stream=True):
        yield {"value":part['message']['content'],"done":part['done']}

if not model_exists(MODEL):
    raise ValueError(f"Model {MODEL} does not exist.")