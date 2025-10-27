from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserBrief


class TweetCreate(BaseModel):
    tweet_data: str
    tweet_media_ids: list[int] | None = None


class LikeInfo(BaseModel):
    user_id: int
    name: str


class TweetOut(BaseModel):
    id: int
    content: str
    attachments: list[str]
    author: UserBrief
    likes: list[LikeInfo]
    stamp: datetime

    model_config = ConfigDict(from_attributes=True)
