from pydantic import BaseModel, EmailStr
from typing import List, Optional

class UpdateEmailRequest(BaseModel):
    user_id: str
    newEmail: str
    password: str

class UpdatePasswordRequest(BaseModel):
    email: str
    currentPassword: str
    newPassword: str

class DeleteAccountRequest(BaseModel):
    email: str
    password: str
    
class LoginRequest(BaseModel):
    email: str
    password: str
    
class VerifyEmail(BaseModel):
    email: EmailStr
    
class UpdateUserModel(BaseModel):
    email: str
    password: str
    nombre: str
    telefono: str
    pais: str
    imgBase64: str = None

class User(BaseModel):
    fullname: str
    phone: str
    country: str
    studyArea: str
    email: EmailStr
    password: str
    imgBase64: str = None
    activeQuestions: List[str] = []
    answeredQuestions: List[str] = []
    activeOwnForums: List[str] = []
    activeAllForums: List[str] = []
    savedResources: List[str] = []

    class Config:
        orm_mode = True
