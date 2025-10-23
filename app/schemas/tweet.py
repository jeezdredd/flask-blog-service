from pydantic import BaseModel, ConfigDict
from app.schemas.user import UserBrief


class TweetCreate(BaseModel):
    tweet_data: str
    tweet_media_ids: list[int] | None = None


class TweetOut(BaseModel):
    id: int
    content: str
    attachments: list[str]
    author: UserBrief
    likes: list[UserBrief]

    model_config = ConfigDict(from_attributes=True)
