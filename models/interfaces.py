from datetime import datetime
from sqlmodel import Field, SQLModel


class UserCreate(SQLModel):
    password: str
    email: str
    verification_code: str

class UserLoginResponse(SQLModel):
    id: str
    email: str

class UserResponse(SQLModel):
    access_token: str
    user: UserLoginResponse

class UserLoginCode(SQLModel):
    email: str
    verification_code: str

class UserLoginPassword(SQLModel):
    email: str
    password: str

class UserResetPassword(SQLModel):
    email: str
    verification_code: str
    new_password: str


class AuthEmail(SQLModel):
    email: str

class AuthEmailVerification(SQLModel):
    email: str
    verification_code: str


class ChatMessage(SQLModel):
    id: str
    content: str
    is_user: bool
    conversation_id: str

class ChatConversation(SQLModel):
    id: str
    title: str
    update_time: int

class ChatCreate(SQLModel):
    title: str = Field(default="新对话")
    user_id:str = ""

class ChatUpdate(SQLModel):
    title: str 


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None