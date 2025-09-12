import os
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from openai import AsyncOpenAI
from prompts import prompt_template


class Settings:
    # DeepSeek 配置
    DEEPSEEK_API_KEY: str = "sk-a07720b3aebc4e308781c5a912a03d0c"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-reasoner"

    # Ollama 配置
    OLLAMA_MODEL: str = "znbang/bge:large-en-v1.5-f16"
    OLLAMA_BASE_URL: str = "http://localhost:11434"

settings = Settings()

embeddings = OllamaEmbeddings(model=settings.OLLAMA_MODEL, base_url=settings.OLLAMA_BASE_URL)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
persist_dir = os.path.join(BASE_DIR, "vector_QAFamily_db")
vector_QAnew_db = Chroma(persist_directory=persist_dir, embedding_function=embeddings)

restatement_client = AsyncOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL,
)
    
async def restatement(sentence: str):
    query = f"""
    请用第一人称简短总结复述：
    内容：
    {sentence}
    请严格直接给出复述，不要添加其他内容。
    """
    resp = await restatement_client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "你是一个助手"},
            {"role": "user", "content": query},
        ],
    )
    res = resp.choices[0].message.content
    return res if res else ""


ds_client = AsyncOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL,
)

async def stream_after_marker(stream, marker: str):
    """
    通用流式过滤器: 只输出 marker 之后的内容
    :param stream: 异步生成器 (LLM 的流式输出)
    :param marker: 分隔符字符串
    """
    marker_len = len(marker)
    buffer = ""
    found_marker = False

    async for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        # print(delta,end="")
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
    stream = await ds_client.chat.completions.create(
        model=settings.DEEPSEEK_MODEL,
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )
    
    async for item in stream_after_marker(stream, "给用户的回答\n"):
        yield item


