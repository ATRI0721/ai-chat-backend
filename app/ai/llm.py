from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from openai import AsyncOpenAI
from app.ai.prompts import prompt_template
from app.ai.kb import KB
from app.core.config import settings

embeddings = OllamaEmbeddings(model=settings.EMBEND_MODEL, base_url=settings.EMBEND_MODEL_URL)

vector_QAnew_db = Chroma(persist_directory=settings.PERSIST_DIR, embedding_function=embeddings)

restatement_client = AsyncOpenAI(
    api_key=settings.MODEL_API_KEY,
    base_url=settings.RESTATE_MODEL_URL,
)

chat_client = AsyncOpenAI(
    api_key=settings.MODEL_API_KEY,
    base_url=settings.CHAT_MODEL_URL,
)

title_client = AsyncOpenAI(
    api_key=settings.MODEL_API_KEY,
    base_url=settings.TITLE_MODEL_URL,
)

    
async def restatement(sentence: str):
    query = f"""
    请用第一人称简短总结复述：
    内容：
    {sentence}
    请严格直接给出复述，不要添加其他内容。
    """
    resp = await restatement_client.chat.completions.create(
        model=settings.RESTATE_MODEL,
        messages=[
            {"role": "system", "content": "你是一个助手"},
            {"role": "user", "content": query},
        ],
    )
    res = resp.choices[0].message.content
    return res if res else ""


async def stream_after_marker(stream, marker: str):
    marker_len = len(marker)
    buffer = ""
    found_marker = False

    async for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        if not delta:
            continue

        if not found_marker:
            buffer += delta
            if marker in buffer:
                found_marker = True
                after = buffer.split(marker, 1)[1]
                if after:
                    yield {"value": after, "done": False}
                buffer = "" 
            else:
                if len(buffer) > marker_len:
                    buffer = buffer[-marker_len:]
        else:
            yield {"value": delta, "done": False}

    yield {"value": "", "done": True}


async def generate_ai_response(messages: list[dict]):
    user_history = [msg["content"] for msg in messages if msg["role"] == "user"]
    message = user_history[-1]
    summary = await restatement("\n".join(user_history))
    docs = vector_QAnew_db.similarity_search(summary, k=3)
    vector_db_result = "\n".join([doc.page_content for doc in docs])
    prompt = prompt_template.format(
        history=messages[:-1],
        message=message,
        content=vector_db_result,
    )
    stream = await chat_client.chat.completions.create(
        model=settings.CHAT_MODEL,
        messages=[{"role": "system", "content": KB}, {"role": "system", "content": prompt}],
        stream=True
    )

    async for item in stream_after_marker(stream, "给用户的回答:\n"):
        yield item

async def generate_title(messages: list[dict]):
    prompt = f'''
        请为以下对话生成一个简短的标题:
        {"\n".join(f"{msg['role']}: {msg['content']}" for msg in messages)}
        \n\n
        请严格直接给出中文标题，不要添加其他内容, 标题长度在 5-15 个字之间。
    '''
    stream = await title_client.chat.completions.create(
        model=settings.TITLE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )

    async for item in stream:
        yield {"value": item.choices[0].delta.content or "", "done": item.choices[0].finish_reason != None}
    
    yield {"value": "", "done": True}

