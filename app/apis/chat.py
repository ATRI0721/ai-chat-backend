from io import StringIO
import json
from typing import AsyncGenerator, List, Optional
from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import StreamingResponse
from app.ai.llm import generate_ai_response, generate_title as ai_generate_title
from app.core.db import get_session
from app.core.deps import CurrentUser, GetConversation, GetMessage, SessionDep
from app.curd import add_conversation, add_message, delete_messages, update_conversation_title
import app.curd as curd
from app.models.database import Conversation, Message
from app.models.interfaces import ChatConversation, ChatCreate, ChatMessage, ChatUpdate

router = APIRouter(tags=["chat"], prefix="/chat")

@router.get("/conversations", response_model=List[ChatConversation])
def get_conversations(user: CurrentUser):
    return user.conversations

@router.post("/conversation", response_model=ChatConversation)
def create_conversation(user: CurrentUser, conversation: ChatCreate, session: SessionDep):
    conversation_db = Conversation(title=conversation.title, user_id=user.id)
    add_conversation(user, conversation_db, session)
    return conversation_db

@router.get("/conversation/{conversation_id}/messages", response_model=List[ChatMessage])
def get_messages(conversation: GetConversation):
    return conversation.messages

@router.patch("/conversation/{conversation_id}", response_model=ChatConversation)
def update_title(conversation: GetConversation, title: ChatUpdate, session: SessionDep):
    update_conversation_title(conversation, title.title, session)
    return conversation

@router.get("/conversation/{conversation_id}/generate-title", response_model=ChatConversation)
def generate_title(conversation: GetConversation):
    _messages = [{"role": msg.role, "content": msg.content} for msg in conversation.messages]
    async def _generate_title():
        _title = ""
        async for t in ai_generate_title(_messages):
            t.update({
                "type": "title",
                "conversation_id": conversation.id,
                "done" : False,
            })
            _title += t["value"]

            
            yield format_event(t)
        update_conversation_title(conversation, _title)
        yield format_event({
            "type": "title",
            "conversation_id": conversation.id,
            "value": _title,
            "update_time": conversation.update_time.isoformat(),
            "done" : True,
        })
    return StreamingResponse(_generate_title(), media_type="text/event-stream")

@router.delete("/conversation/{conversation_id}")
def delete_conversation(conversation: GetConversation, session: SessionDep):
    curd.delete_conversation(conversation, session)
    return {"message": "success"}

@router.delete("/conversations")
def delete_conversations(user: CurrentUser, session: SessionDep):
    for conversation in user.conversations:
        curd.delete_conversation(conversation, session)
    return {"message": "success"}

@router.get("/completions/{conversation_id}/regenerate/{message_id}")
async def regenerate_completions(conversation: GetConversation, message: GetMessage, session: SessionDep):
    delete_messages(conversation, message, session)
    ai_message = Message(content="", role="assistant")
    messages_data = list(conversation.messages)
    async def respond():
        yield json.dumps({
            "type": "init",
            "ai_message_id": ai_message.id,
            "done": False,
        }) + '\n\n\n'

        content_buffer = StringIO()
        async for content in generate_response(messages_data, content_buffer, ai_message.id):
            yield content

        ai_message.content = content_buffer.getvalue()
        content_buffer.close()
        add_message(conversation, ai_message, session)

    return StreamingResponse(respond(), media_type="text/event-stream")

@router.post("/completions/{conversation_id}")
async def get_completions(
    conversation: GetConversation,
    session: SessionDep,
    message: str = Body(..., embed=True),
):
    user_message = Message(content=message, role="user")
    ai_message = Message(content="", role="assistant")

    # 保存用户消息（用当前请求的 session）
    add_message(conversation, user_message, session)

    messages_data = list(conversation.messages)

    async def respond() -> AsyncGenerator[str, None]:
        try:
            yield format_event({
                "type": "init",
                "user_message_id": user_message.id,
                "ai_message_id": ai_message.id,
                "done": False,
            })

            buffer = StringIO()
            async for event in generate_response(messages_data, buffer, ai_message.id):
                yield event

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            ai_message.content = buffer.getvalue()
            buffer.close()
            if ai_message.content.strip():
                session = next(get_session())
                add_message(conversation, ai_message, session)

    return StreamingResponse(respond(), media_type="text/event-stream")


async def generate_response(
    messages: list[Message],
    buffer: StringIO,
    message_id: str
) -> AsyncGenerator[str, None]:
    _messages = [{"role": msg.role, "content": msg.content} for msg in messages]

    async for t in generate_ai_response(_messages):
        t.update({
            "type": "message",
            "id": message_id
        })
        buffer.write(t["value"])
        yield format_event(t)

def format_event(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False) + "\n\n\n"
