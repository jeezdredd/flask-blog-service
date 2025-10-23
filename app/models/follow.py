from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Follow(Base):
    __tablename__ = "follows"
    __table_args__ = (UniqueConstraint("follower_id", "followee_id", name="uq_follow_pair"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    follower_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    followee_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    follower: Mapped["User"] = relationship("User", foreign_keys=[follower_id], back_populates="following")
    followee: Mapped["User"] = relationship("User", foreign_keys=[followee_id], back_populates="followers")
