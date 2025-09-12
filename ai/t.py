import asyncio
import ollama
import json
from datetime import datetime
from pathlib import Path
from openai import AsyncOpenAI

from llm import generate_ai_response, settings


# ========== 工具函数 ==========

def load_prompt(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def save_conversation(conversation, patient_prompt, out_dir="conversations", prefix="conversation"):
    # 为每个病人建立单独目录
    out_dir = Path(out_dir) / prefix
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    json_path = out_dir / f"{prefix}_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "patient_prompt": patient_prompt,
                "conversation": conversation,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"[保存成功] {json_path}")


# ========== 患者模型客户端 ==========
def get_patient_client():
    return AsyncOpenAI(
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
    )


async def patient_ai_respond(messages: list[dict], client: AsyncOpenAI):
    resp = await client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
    )
    res = resp.choices[0].message.content
    return res if res else ""


# ========== 单个线程的对话 ==========
async def run_conversation(patient_prompt: str, max_rounds=10, prefix="conversation"):
    client = get_patient_client()

    # 初始化对话记录
    conversation = [
        {"role": "system", "content": patient_prompt},
        {"role": "user", "content": "你好，我想聊聊最近的心理状态。"},
    ]

    for round_idx in range(max_rounds):
        # 患者发言
        patient_reply = await patient_ai_respond(conversation, client)
        conversation.append({"role": "user", "content": patient_reply})
        print(f"\n[{prefix} 患者]: {patient_reply}")

        # 心理医生回应（流式）
        doctor_reply_parts = []
        async for chunk in generate_ai_response(conversation[1:]):
            doctor_reply_parts.append(chunk["value"])
        doctor_reply = "".join(doctor_reply_parts).strip()
        conversation.append({"role": "assistant", "content": doctor_reply})
        print(f"[{prefix} 心理医生]: {doctor_reply}")

    save_conversation(conversation, patient_prompt, prefix=prefix)
    return conversation


# ========== 主入口，运行9个线程 ==========
async def main():
    prompt_files = [
        f"prompts/patient{i}.txt" for i in range(1, 4)
    ]

    tasks = []
    for idx, file in enumerate(prompt_files, 1):
        patient_prompt = load_prompt(file)
        prefix = f"patient{idx}"
        tasks.append(run_conversation(patient_prompt, max_rounds=10, prefix=prefix))

    await asyncio.gather(*tasks, return_exceptions=True)

async def run_multi_main(times=10):
    tasks = [main() for _ in range(times)]
    await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    asyncio.run(run_multi_main(1))
