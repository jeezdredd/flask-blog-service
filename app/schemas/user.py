from pydantic import BaseModel

class UserBrief(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class UserProfile(BaseModel):
    id: int
    name: str
    followers: list[UserBrief]
    following: list[UserBrief]