from typing import Iterable

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload, selectinload

from app.deps.auth import get_current_user, get_db
from app.models.follow import Follow
from app.models.like import Like
from app.models.media import Media
from app.models.tweet import Tweet, TweetMedia
from app.schemas.tweet import LikeInfo, TweetCreate, TweetOut
from app.schemas.user import UserBrief

router = APIRouter(prefix="/api/tweets", tags=["tweets"])


def _serialize_tweet(tweet: Tweet, current_user_id: int, likes_count: int | None = None) -> dict:
    attachments = [media.path for media in tweet.medias]
    like_users = [LikeInfo(user_id=like.user_id, name=like.user.name if like.user else "") for like in tweet.likes]
    effective_likes_count = likes_count if likes_count is not None else len(tweet.likes)
    liked_by_me = any(like.user_id == current_user_id for like in tweet.likes)
    payload = TweetOut(
        id=tweet.id,
        content=tweet.content,
        attachments=attachments,
        author=UserBrief.model_validate(tweet.author),
        likes=like_users,
        likes_count=effective_likes_count,
        liked_by_me=liked_by_me,
        stamp=tweet.created_at,
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
    sort: str = Query("popular", pattern="^(popular|latest)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    offset: int | None = Query(None, ge=1),
):
    author_ids = {row.followee_id for row in db.query(Follow.followee_id).filter(Follow.follower_id == user.id)}
    author_ids.add(user.id)

    likes_count_subquery = (
        db.query(
            Like.tweet_id.label("tweet_id"),
            func.count(Like.id).label("likes_count"),
        )
        .group_by(Like.tweet_id)
        .subquery()
    )

    likes_count_expr = func.coalesce(likes_count_subquery.c.likes_count, 0)

    query = (
        db.query(Tweet, likes_count_expr.label("likes_count"))
        .outerjoin(likes_count_subquery, likes_count_subquery.c.tweet_id == Tweet.id)
        .filter(Tweet.author_id.in_(author_ids))
        .options(
            selectinload(Tweet.author),
            selectinload(Tweet.medias),
            selectinload(Tweet.likes).joinedload(Like.user),
        )
    )

    if sort == "popular":
        query = query.order_by(desc(likes_count_expr), desc(Tweet.created_at), desc(Tweet.id))
    else:
        query = query.order_by(desc(Tweet.created_at), desc(Tweet.id), desc(likes_count_expr))

    page_number = offset if offset is not None else page
    skip = (page_number - 1) * limit

    rows = query.offset(skip).limit(limit + 1).all()
    has_next = len(rows) > limit
    rows = rows[:limit]

    payload = [_serialize_tweet(tweet, current_user_id=user.id, likes_count=likes_count) for tweet, likes_count in rows]
    pagination = {
        "page": page_number,
        "limit": limit,
        "sort": sort,
        "has_next": has_next,
        "has_previous": page_number > 1,
        "next_page": page_number + 1 if has_next else None,
        "previous_page": page_number - 1 if page_number > 1 else None,
    }
    return {"result": True, "tweets": payload, "pagination": pagination}
