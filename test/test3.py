from random import randint
from typing import Annotated, List
from fastapi import Body, Depends, FastAPI
from sqlmodel import Field, Relationship, SQLModel


app = FastAPI()

class T1(SQLModel):
    id: int = Field(default=randint(1, 1000000000), primary_key=True)
    name: str
    t2: "T2" = Relationship(back_populates="t1")

class T2(SQLModel):
    id: int
    t1: "T1" = Relationship(back_populates="t2")

def get_t2(id: int) -> T2:
    return T2(id=id)

d = Annotated[T2, Depends(get_t2)]

@app.get("/")
def hello_world():
    return {"message": "Hello World"}

@app.get("/t2/{id}")
def get_t2(t2: d, id: int):
    return {"t2": t2, "id": id}

@app.get("/t2",response_model=T2)
def get_t2(name: str = Body(embed=True)):
    res = T1(name=name)
    res.t2 = T2(id=1)
    return res.t2