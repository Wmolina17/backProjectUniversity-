from pydantic import BaseModel

class Resource(BaseModel):
    title: str
    description: str
    likeCount: int = 0
    img: str
    redirectionLink: str

    class Config:
        orm_mode = True
