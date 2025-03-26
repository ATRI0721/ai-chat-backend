from datetime import datetime
from typing import List
from sqlmodel import Field, Relationship, SQLModel

from utils import generate_uuid, get_time


class User(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    email: str = Field(max_length=100, index=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    conversations: List["Conversation"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class Message(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    content: str
    is_user: bool
    conversation_id: str = Field(foreign_key="conversation.id")
    conversation: "Conversation" = Relationship(back_populates="messages")

class Conversation(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    title: str = Field(max_length=100)
    update_time: int = Field(default_factory=get_time)
    user_id: str = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="conversations")
    messages: List["Message"] = Relationship(back_populates="conversation", sa_relationship_kwargs={"cascade": "all, delete-orphan"})