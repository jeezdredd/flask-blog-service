from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload, selectinload

from app.deps.auth import get_current_user, get_db
from app.models.follow import Follow
from app.models.user import User
from app.schemas.user import UserBrief, UserListItem, UserProfile

router = APIRouter(prefix="/api/users", tags=["users"])


def _load_user_with_relations(db: Session, user_id: int) -> User | None:
    return (
        db.query(User)
        .options(
            selectinload(User.followers).joinedload(Follow.follower),
            selectinload(User.following).joinedload(Follow.followee),
        )
        .filter(User.id == user_id)
        .first()
    )


def _serialize_profile(user: User) -> dict:
    profile = UserProfile(
        id=user.id,
        name=user.name,
        followers=[UserBrief.model_validate(link.follower) for link in user.followers if link.follower is not None],
        following=[UserBrief.model_validate(link.followee) for link in user.following if link.followee is not None],
    )
    return profile.model_dump()


@router.get("/me")
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    hydrated = _load_user_with_relations(db, user.id)
    if hydrated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    return {"result": True, "user": _serialize_profile(hydrated)}


@router.get("")
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    users = (
        db.query(User)
        .options(
            selectinload(User.followers).joinedload(Follow.follower),
            selectinload(User.following).joinedload(Follow.followee),
        )
        .all()
    )
    items = []
    for user in users:
        followers = user.followers or []
        following = user.following or []
        is_following = any(link.follower_id == current_user.id for link in followers)
        items.append(
            UserListItem(
                id=user.id,
                name=user.name,
                is_me=user.id == current_user.id,
                is_following=is_following,
                followers_count=len(followers),
                following_count=len(following),
            ).model_dump()
        )
    return {"result": True, "users": items}


@router.get("/{user_id}")
def user_profile(user_id: int, db: Session = Depends(get_db)):
    user = _load_user_with_relations(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    return {"result": True, "user": _serialize_profile(user)}


@router.post("/{user_id}/follow")
def follow_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="cannot follow yourself")
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")

    already_following = (
        db.query(Follow).filter(Follow.follower_id == current_user.id, Follow.followee_id == user_id).first()
    )
    if not already_following:
        db.add(Follow(follower_id=current_user.id, followee_id=user_id))
        db.commit()
        return {"result": True, "message": "followed"}
    return {"result": True, "message": "already_following"}


@router.delete("/{user_id}/follow")
def unfollow_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    relation = db.query(Follow).filter(Follow.follower_id == current_user.id, Follow.followee_id == user_id).first()
    if relation:
        db.delete(relation)
        db.commit()
        return {"result": True, "message": "unfollowed"}
    return {"result": True, "message": "not_following"}


@router.get("/{user_id}/followers")
def list_followers(user_id: int, db: Session = Depends(get_db)):
    user = _load_user_with_relations(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    followers = [
        UserBrief.model_validate(link.follower).model_dump() for link in user.followers if link.follower is not None
    ]
    return {"result": True, "followers": followers}


@router.get("/{user_id}/following")
def list_following(user_id: int, db: Session = Depends(get_db)):
    user = _load_user_with_relations(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    following = [
        UserBrief.model_validate(link.followee).model_dump() for link in user.following if link.followee is not None
    ]
    return {"result": True, "following": following}
