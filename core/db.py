from typing import Generator
from models.database import *
from sqlmodel import SQLModel, Session, create_engine

from core.config import Settings


engine = create_engine(Settings.DATABASE_URL,
                       connect_args={"check_same_thread": False})

def create_db_and_tables():
    SQLModel.metadata.create_all(engine,checkfirst=True)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

create_db_and_tables()