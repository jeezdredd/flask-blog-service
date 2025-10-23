from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.deps.auth import get_db, get_current_user
from app.models.tweet import Tweet, TweetMedia
from app.models.media import Media
from app.schemas.tweet import TweetCreate

router = APIRouter(prefix="/api/tweets", tags=["tweets"])

@router.post("")
def create_tweet(payload: TweetCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if not payload.tweet_data or len(payload.tweet_data) > 1000:
        raise HTTPException(status_code=422, detail="invalid tweet_data")
    t = Tweet(content=payload.tweet_data, author_id=user.id)
    db.add(t)
    db.flush()
    ids = payload.tweet_media_ids or []
    if ids:
        medias = db.query(Media).filter(Media.id.in_(ids)).all()
        for m in medias:
            db.add(TweetMedia(tweet_id=t.id, media_id=m.id))
    db.commit()
    return {"result": True, "tweet_id": t.id}

@router.delete("/{tweet_id}")
def delete_tweet(tweet_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    t = db.query(Tweet).filter(Tweet.id == tweet_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="tweet not found")
    if t.author_id != user.id:
        raise HTTPException(status_code=403, detail="forbidden")
    db.delete(t)
    db.commit()
    return {"result": True}