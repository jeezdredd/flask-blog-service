from pydantic import BaseModel, ConfigDict


class UserBrief(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class UserProfile(BaseModel):
    id: int
    name: str
    followers: list[UserBrief]
    following: list[UserBrief]

    model_config = ConfigDict(from_attributes=True)
