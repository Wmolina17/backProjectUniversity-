from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime

class Answer(BaseModel):
    userId: str
    likes: int = 0
    dislikes: int = 0
    date: datetime
    textContent: str
    listLike: List[str] = []
    listDeslike: List[str] = []
    
class LikeDislikeRequest(BaseModel):
    questionId: str
    answerIndex: int
    action: str
    userId: str

class Question(BaseModel):
    userId: str
    title: str
    textContent: str
    viewsCount: int = 0
    answersCount: int = 0
    date: datetime
    tags: List[str] = []
    answers: List[Answer] = {}
    isReceivingAnswers: bool = True

    class Config:
        orm_mode = True
