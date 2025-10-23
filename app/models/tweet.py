from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey
from app.db.session import Base

class Tweet(Base):
    __tablename__ = "tweets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str] = mapped_column(String(1000), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

class TweetMedia(Base):
    __tablename__ = "tweet_medias"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tweet_id: Mapped[int] = mapped_column(ForeignKey("tweets.id", ondelete="CASCADE"))
    media_id: Mapped[int] = mapped_column(ForeignKey("medias.id", ondelete="CASCADE"))

from app.models.user import User  # noqa: E402
from app.models.media import Media  # noqa: E402
from app.models.like import Like  # noqa: E402

Tweet.author = relationship(User, back_populates="tweets")
Tweet.attachments = relationship("TweetMedia", back_populates="tweet", cascade="all,delete")
Tweet.likes = relationship(Like, back_populates="tweet", cascade="all,delete")

TweetMedia.tweet = relationship(Tweet, back_populates="attachments")
TweetMedia.media = relationship(Media)