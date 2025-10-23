from pydantic import BaseModel


class MediaOut(BaseModel):
    result: bool
    media_id: int
