from io import StringIO
import json
from typing import List
from fastapi import APIRouter, Body
from fastapi.responses import StreamingResponse

from ai.llm import generate_ai_response
from core.deps import CurrentUser, GetConversation, GetMessage, SessionDep
from curd import add_conversation, add_message, delete_message, delete_messages, update_conversation_title
import curd
from models.database import Conversation, Message, User
from models.interfaces import ChatConversation, ChatCreate, ChatMessage, ChatUpdate


router = APIRouter(tags=["chat"], prefix="/chat")

@router.get("/conversations", response_model=List[ChatConversation])
def get_conversations(user: CurrentUser):
    return user.conversations

@router.post("/conversation", response_model=ChatConversation)
def create_conversation(user: CurrentUser, conversation: ChatCreate, session: SessionDep):
    conversation_db = Conversation.model_validate(conversation)
    add_conversation(user, conversation_db, session)
    return conversation_db

@router.get("/conversation/{conversation_id}/messages", response_model=List[ChatMessage])
def get_messages(conversation: GetConversation):
    return conversation.messages

@router.put("/conversation/{conversation_id}", response_model=ChatConversation)
def update_title(conversation: GetConversation, title: ChatUpdate, session: SessionDep):
    update_conversation_title(conversation, title.title, session)
    return conversation

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
    messages = conversation.messages
    ai_message = Message(content="", is_user=False)
    async def respond():
        yield json.dumps({
            "type":"init",
            "ai_message_id": ai_message.id,
            "done": False,
        }) + '\n\n\n'
        content_buffer = StringIO()
        async for content in generate_response(messages, content_buffer, ai_message.id):
            yield content
        ai_message.content = content_buffer.getvalue()
        content_buffer.close()
        add_message(conversation,ai_message, session)

    return StreamingResponse(respond(), media_type="text/event-stream")
    


@router.post("/completions/{conversation_id}")
async def get_completions(conversation: GetConversation, session: SessionDep, message: str = Body(embed=True)):
    user_message = Message(content=message, is_user=True)
    ai_message = Message(content="", is_user=False)
    add_message(conversation,user_message, session)
    messages = [{"role":"user" if msg.is_user else "assistant","content":msg.content}
                 for msg in conversation.messages]
    async def respond():
        yield json.dumps({
            "type":"init",
            "user_message_id": user_message.id,
            "ai_message_id": ai_message.id,
            "done": False,
        }) + '\n\n\n'
        content_buffer = StringIO()
        async for content in generate_response(conversation.messages, content_buffer, ai_message.id):
            yield content
        ai_message.content = content_buffer.getvalue()
        content_buffer.close()
        add_message(conversation,ai_message, session)
    return StreamingResponse(respond(), media_type="text/event-stream")


async def generate_response(messages: List[Message], buffer: StringIO, message_id: str):
    _messages = [{"role":"user" if msg.is_user else "assistant","content":msg.content}
                 for msg in messages]
    async for t in generate_ai_response(_messages):
        t['type'] = 'message'
        t['id'] = message_id
        buffer.write(t['value'])
        yield json.dumps(t) + '\n\n\n'


    