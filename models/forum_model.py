from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import pytz
colombia_tz = pytz.timezone("America/Bogota")

class ActiveUser(BaseModel):
    userId: str
    name: str
    imgBase64: Optional[str] = None
    email: str
    
class AddUserRequest(BaseModel):
    forum_id: str
    user: ActiveUser
    
class ResponseMessage(BaseModel):
    userId: str
    name: str
    textContent: str
    
class Message(BaseModel):
    userId: str
    name: str
    textContent: str
    respondTo: Optional[ResponseMessage] = None
    date: datetime = datetime.now(colombia_tz)
    
class Forum(BaseModel):
    imgBase64: Optional[str] = None
    creator: ActiveUser
    title: str
    description: str
    creationDate: datetime = datetime.now(colombia_tz)
    activeUsers: List[ActiveUser] = []
    messages: List[Message] = []

    class Config:
        orm_mode = True  
