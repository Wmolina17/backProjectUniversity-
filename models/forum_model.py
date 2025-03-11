from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime

class ActiveUser(BaseModel):
    userId: str
    name: str

class Message(BaseModel):
    userId: str
    name: str
    textContent: str
    likes: int = 0
    img: str

class Forum(BaseModel):
    creator: Dict[str, ActiveUser] = {}
    title: str
    description: str
    creationDate: datetime
    usersCount: int = 0
    likeCount: int = 0
    messagesCount: int = 0
    activeUsers: Dict[str, ActiveUser] = {}
    messages: Dict[str, Message] = {}

    class Config:
        orm_mode = True
