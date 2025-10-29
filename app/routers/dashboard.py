from fastapi import APIRouter, Depends
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.deps.auth import get_current_user, get_db
from app.models.follow import Follow
from app.models.like import Like
from app.models.tweet import Tweet
from app.models.user import User

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def overview(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),  # noqa: ARG001 - ensures auth is enforced
):
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_tweets = db.query(func.count(Tweet.id)).scalar() or 0
    total_likes = db.query(func.count(Like.id)).scalar() or 0

    followers_counts = (
        db.query(
            Follow.followee_id.label("user_id"),
            func.count(Follow.follower_id).label("followers_count"),
        )
        .group_by(Follow.followee_id)
        .subquery()
    )
    tweet_counts = (
        db.query(
            Tweet.author_id.label("user_id"),
            func.count(Tweet.id).label("tweet_count"),
        )
        .group_by(Tweet.author_id)
        .subquery()
    )

    followers_count_col = func.coalesce(followers_counts.c.followers_count, 0)
    tweet_count_col = func.coalesce(tweet_counts.c.tweet_count, 0)

    popular_authors_rows = (
        db.query(
            User.id,
            User.name,
            followers_count_col.label("followers_count"),
            tweet_count_col.label("tweet_count"),
        )
        .outerjoin(followers_counts, followers_counts.c.user_id == User.id)
        .outerjoin(tweet_counts, tweet_counts.c.user_id == User.id)
        .order_by(desc(followers_count_col), desc(tweet_count_col), User.name)
        .limit(5)
        .all()
    )

    like_counts = (
        db.query(
            Like.tweet_id.label("tweet_id"),
            func.count(Like.id).label("likes_count"),
        )
        .group_by(Like.tweet_id)
        .subquery()
    )

    likes_count_col = func.coalesce(like_counts.c.likes_count, 0)

    trending_rows = (
        db.query(
            Tweet.id,
            Tweet.content,
            User.name,
            likes_count_col.label("likes_count"),
        )
        .join(User, Tweet.author_id == User.id)
        .outerjoin(like_counts, like_counts.c.tweet_id == Tweet.id)
        .order_by(desc(likes_count_col), desc(Tweet.created_at), desc(Tweet.id))
        .limit(5)
        .all()
    )

    stats = {
        "total_users": int(total_users),
        "total_tweets": int(total_tweets),
        "total_likes": int(total_likes),
        "popular_authors": [
            {
                "user_id": row[0],
                "name": row[1],
                "followers_count": int(row[2]),
                "tweet_count": int(row[3]),
            }
            for row in popular_authors_rows
        ],
        "trending_tweets": [
            {
                "tweet_id": row[0],
                "content": row[1],
                "author": row[2],
                "likes_count": int(row[3]),
            }
            for row in trending_rows
        ],
    }
    return {"result": True, "stats": stats}
