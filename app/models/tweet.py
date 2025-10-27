from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Tweet(Base):
    __tablename__ = "tweets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str] = mapped_column(String(1000), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    author: Mapped["User"] = relationship("User", back_populates="tweets")
    tweet_medias: Mapped[list["TweetMedia"]] = relationship(
        "TweetMedia", back_populates="tweet", cascade="all, delete-orphan"
    )
    medias: Mapped[list["Media"]] = relationship(
        "Media", secondary="tweet_medias", back_populates="tweets", viewonly=True
    )
    likes: Mapped[list["Like"]] = relationship("Like", back_populates="tweet", cascade="all, delete-orphan")


class TweetMedia(Base):
    __tablename__ = "tweet_medias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tweet_id: Mapped[int] = mapped_column(ForeignKey("tweets.id", ondelete="CASCADE"))
    media_id: Mapped[int] = mapped_column(ForeignKey("medias.id", ondelete="CASCADE"))

    tweet: Mapped["Tweet"] = relationship("Tweet", back_populates="tweet_medias")
    media: Mapped["Media"] = relationship("Media")


# Late imports to ensure SQLAlchemy registry resolves string references.
from app.models.media import Media  # noqa: E402
from app.models.like import Like  # noqa: E402
from app.models.user import User  # noqa: E402
