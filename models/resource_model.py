from pydantic import BaseModel

class Resource(BaseModel):
    userId: str
    title: str
    description: str
    savedCount: int = 0
    viewsCount: int = 0
    img: str
    redirectionLink: str
    resourceType: str

    class Config:
        orm_mode = True
