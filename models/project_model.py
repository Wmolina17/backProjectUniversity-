from pydantic import BaseModel
from datetime import datetime

class Project(BaseModel):
    title: str
    textContent: str
    likeCount: int = 0
    watchCount: int = 0
    img: str
    typeContent: str
    urlVideo: str
    urlPage: str

    class Config:
        orm_mode = True
