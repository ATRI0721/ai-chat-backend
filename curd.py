from fastapi import HTTPException
from sqlmodel import Session, select
from core.security import get_password_hash
from models.database import Conversation, Message, User
from models.interfaces import UserCreate
from utils import generate_uuid, get_time


def add_user(user: UserCreate, session: Session) -> User | None:
    if (session.exec(select(User).where(User.email == user.email)).first()):
        return None
    new_user = User(email=user.email, hashed_password=get_password_hash(user.password))
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user

def get_user_by_email(email: str, session: Session) -> User | None:
    return session.exec(select(User).where(User.email == email)).first()

def get_user_by_id(id: str, session: Session) -> User | None:
    return session.exec(select(User).where(User.id == id)).first()

def update_user_password(user: User, new_password: str, session: Session) -> User:
    user.hashed_password = get_password_hash(new_password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def delete_user(user: User, session: Session) -> None:
    session.delete(user)
    session.commit()

def add_conversation(user: User, conversation: Conversation, session: Session) -> None:
    while (session.exec(select(Conversation).where(Conversation.id == conversation.id)).first()): 
        conversation.id = generate_uuid()
    user.conversations.append(conversation)
    session.add(user)
    session.commit()
    session.refresh(user)

def update_conversation_title(conversation: Conversation, new_title: str, session: Session) -> None:
    conversation.title = new_title
    conversation.update_time = get_time()
    session.add(conversation)
    session.commit()
    session.refresh(conversation)

def delete_conversation(conversation: Conversation, session: Session) -> None:
    session.delete(conversation)
    session.commit()


def add_message(conversation: Conversation, message: Message, session: Session) -> None:
    while (session.exec(select(Message).where(Message.id == message.id)).first()): 
        message.id = generate_uuid()
    conversation.messages.append(message)
    conversation.update_time = get_time()
    session.add(conversation)
    session.commit()
    session.refresh(conversation)

def delete_message(message: Message, session: Session) -> None:
    session.delete(message)
    session.commit()

def delete_messages(conversation: Conversation, message: Message, session: Session) -> None:
    if message.conversation_id != conversation.id:
        raise HTTPException(status_code=400, detail="Message not in conversation")
    conversation.messages = conversation.messages[:conversation.messages.index(message)]
    conversation.update_time = get_time()
    session.add(conversation)
    session.commit()
    session.refresh(conversation)