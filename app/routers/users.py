from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.deps.auth import get_db, get_current_user
from app.models.user import User
from app.models.follow import Follow
from app.schemas.user import UserBrief, UserProfile

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/me")
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    followers = db.query(User).join(Follow, Follow.follower_id == User.id).filter(Follow.followee_id == user.id).all()
    following = db.query(User).join(Follow, Follow.followee_id == User.id).filter(Follow.follower_id == user.id).all()
    return {"result": True, "user": UserProfile(id=user.id, name=user.name, followers=followers, following=following)}

@router.get("/{user_id}")
def user_profile(user_id: int, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="user not found")
    followers = db.query(User).join(Follow, Follow.follower_id == User.id).filter(Follow.followee_id == u.id).all()
    following = db.query(User).join(Follow, Follow.followee_id == User.id).filter(Follow.follower_id == u.id).all()
    return {"result": True, "user": UserProfile(id=u.id, name=u.name, followers=followers, following=following)}
