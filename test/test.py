from io import StringIO
import json
from random import randint
import re
import time
from typing import Annotated, Any, List, Literal
from fastapi import Body, Depends, FastAPI
from fastapi.responses import StreamingResponse
import ollama
import asyncio

from sqlmodel import Field, Relationship, SQLModel

MODEL: str = "llama3.2:latest"
# MODEL: str = "llama3:8b"

def model_exists(model_name: str) -> bool:
    return model_name in [str(i['model']) for i in ollama.list().model_dump()["models"]]

client = ollama.AsyncClient()

async def generate_ai_response(message: list[dict]):
    async for part in await client.chat(model=MODEL, messages=message, stream=True):
        yield {"value":part['message']['content'],"done":part['done']}

if not model_exists(MODEL):
    raise ValueError(f"Model {MODEL} does not exist.")

class Message(SQLModel):
    content: str
    is_user: bool
    id: int = Field(default=randint(1, 1000000000), primary_key=True)

class Conversation(SQLModel):
    id: int = Field(default=None, primary_key=True)
    messages: List[Message]

def add_message(conversation: Conversation, message: Message):
    conversation.messages.append(message)

conversation = Conversation(id=1, messages=[])

GetConversation = Annotated[Conversation,Depends(lambda: conversation)]



app = FastAPI()

@app.post("/test-model")
async def get_completions(conversation: GetConversation, message: str = Body(embed=True)):
    user_message = Message(content=message, is_user=True)
    ai_message = Message(content="", is_user=False)
    add_message(conversation,user_message)
    messages = [{"role":"user" if msg.is_user else "assistant","content":msg.content}
                 for msg in conversation.messages]
    async def respond():
        yield json.dumps({
            "type":"init",
            "user_message_id": user_message.id,
            "ai_message_id": ai_message.id,
            "done": False,
        }) + '\n'
        content_buffer = StringIO()
        async for t in generate_ai_response(messages):
            t['type'] = 'ai_message'
            t['id'] = ai_message.id
            content_buffer.write(t['value'])
            yield json.dumps(t) + '\n'
        ai_message.content = content_buffer.getvalue()
        content_buffer.close()
        add_message(conversation,ai_message)
    return StreamingResponse(respond(), media_type="text/event-stream")

@app.get("/test-stream")
async def test_stream():
    def stream():
        for i in range(5):
            time.sleep(1)
            print(i)
            yield str(i) + '\n'
    return StreamingResponse(stream(), media_type="text/event-stream")

@app.get("/")
def hello_world():
    return {"message": "Hello World"}

@app.get("/test-model")
async def get_completions(conversation: GetConversation, message: str = "what's the weather today?"):
    user_message = Message(content=message, is_user=True)
    ai_message = Message(content="", is_user=False)
    add_message(conversation,user_message)
    messages = [{"role":"user" if msg.is_user else "assistant","content":msg.content}
                 for msg in conversation.messages]
    async def respond():
        yield json.dumps({
            "type":"init",
            "user_message_id": user_message.id,
            "ai_message_id": ai_message.id,
            "done": False,
        }) + '\n'
        content_buffer = StringIO()
        async for t in generate_ai_response(messages):
            t['type'] = 'ai_message'
            t['id'] = ai_message.id
            content_buffer.write(t['value'])
            yield json.dumps(t) + '\n'
        ai_message.content = content_buffer.getvalue()
        content_buffer.close()
        add_message(conversation,ai_message)
    return StreamingResponse(respond(), media_type="text/event-stream")
   

