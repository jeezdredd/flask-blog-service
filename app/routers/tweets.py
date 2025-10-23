from typing import Iterable

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload, selectinload

from app.deps.auth import get_current_user, get_db
from app.models.follow import Follow
from app.models.like import Like
from app.models.media import Media
from app.models.tweet import Tweet, TweetMedia
from app.schemas.tweet import TweetCreate, TweetOut
from app.schemas.user import UserBrief

router = APIRouter(prefix="/api/tweets", tags=["tweets"])


def _serialize_tweet(tweet: Tweet) -> dict:
    attachments = [media.path for media in tweet.medias]
    like_users = [UserBrief.model_validate(like.user) for like in tweet.likes if like.user is not None]
    payload = TweetOut(
        id=tweet.id,
        content=tweet.content,
        attachments=attachments,
        author=UserBrief.model_validate(tweet.author),
        likes=like_users,
    )
    return payload.model_dump()


@router.post("", status_code=status.HTTP_201_CREATED)
def create_tweet(
    payload: TweetCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    text = (payload.tweet_data or "").strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="tweet_data is required")
    if len(text) > 1000:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="tweet_data is too long")

    tweet = Tweet(content=text, author_id=user.id)
    db.add(tweet)
    db.flush()

    media_ids = payload.tweet_media_ids or []
    if media_ids:
        medias: Iterable[Media] = (
            db.query(Media).filter(Media.id.in_(media_ids)).options(joinedload(Media.uploader)).all()
        )
        found_ids = {media.id for media in medias}
        missing = set(media_ids) - found_ids
        if missing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid media ids")
        for media in medias:
            if media.uploader_id != user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="cannot attach foreign media")
            db.add(TweetMedia(tweet_id=tweet.id, media_id=media.id))

    db.commit()
    return {"result": True, "tweet_id": tweet.id}


@router.delete("/{tweet_id}")
def delete_tweet(
    tweet_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
    if not tweet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tweet not found")
    if tweet.author_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not allowed to delete tweet")

    db.delete(tweet)
    db.commit()
    return {"result": True}


@router.post("/{tweet_id}/likes")
def like_tweet(
    tweet_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    tweet = db.query(Tweet).options(selectinload(Tweet.likes)).filter(Tweet.id == tweet_id).first()
    if not tweet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tweet not found")

    already_liked = any(like.user_id == user.id for like in tweet.likes)
    if not already_liked:
        db.add(Like(user_id=user.id, tweet_id=tweet_id))
        db.commit()
    return {"result": True}


@router.delete("/{tweet_id}/likes")
def unlike_tweet(
    tweet_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    like = db.query(Like).filter(Like.tweet_id == tweet_id, Like.user_id == user.id).first()
    if not like:
        return {"result": True}
    db.delete(like)
    db.commit()
    return {"result": True}


@router.get("")
def feed(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    followed_ids = [row.followee_id for row in db.query(Follow.followee_id).filter(Follow.follower_id == user.id)]
    if not followed_ids:
        return {"result": True, "tweets": []}

    tweets = (
        db.query(Tweet)
        .filter(Tweet.author_id.in_(followed_ids))
        .options(
            selectinload(Tweet.author),
            selectinload(Tweet.medias),
            selectinload(Tweet.likes).joinedload(Like.user),
        )
        .all()
    )

    tweets.sort(key=lambda t: (len(t.likes), t.id), reverse=True)
    payload = [_serialize_tweet(tweet) for tweet in tweets]
    return {"result": True, "tweets": payload}
