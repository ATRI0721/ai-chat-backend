import ollama
from app.core.config import settings

MODEL: str = settings.OLLAMA_MODEL

client = ollama.AsyncClient()

def model_exists(model_name: str) -> bool:
    return model_name in [str(i['model']) for i in ollama.list().model_dump()["models"]]
    
async def generate_ai_response(messages: list[dict]):
    async for part in await client.chat(model=MODEL, messages=messages, stream=True):
        yield {"value":part['message']['content'],"done":part['done']}

if not model_exists(MODEL):
    raise ValueError(f"Model {MODEL} does not exist.")

async def generate_title(messages: list[dict]):
    prompt = f'''
        请为以下对话生成一个简短的标题:
        {"\n".join(f"{msg['role']}: {msg['content']}" for msg in messages)}
        \n\n
        请严格直接给出中文标题，不要添加其他内容(包括标点符号、空格等), 标题长度在 5-15 个字之间。
    '''
    stream = await client.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )

    async for part in stream:
        yield {"value": part['message']['content'], "done": part['done']}
    
    yield {"value": "", "done": True}