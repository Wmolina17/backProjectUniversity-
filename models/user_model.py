from pydantic import BaseModel, EmailStr
from typing import List, Optional

class LoginRequest(BaseModel):
    email: str
    password: str
    
class VerifyEmail(BaseModel):
    email: EmailStr

class User(BaseModel):
    fullname: str
    phone: str
    country: str
    studyArea: str
    email: EmailStr
    password: str
    activeQuestions: int = 0
    answeredQuestions: int = 0
    activeOwnForums: List[str] = []
    activeAllForums: List[str] = []
    savedProjects: List[str] = []
    savedResources: List[str] = []

    class Config:
        orm_mode = True
