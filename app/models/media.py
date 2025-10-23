from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Media(Base):
    __tablename__ = "medias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    path: Mapped[str] = mapped_column(String(512), nullable=False)
    uploader_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    uploader: Mapped["User"] = relationship("User", back_populates="media_uploads")
    tweets: Mapped[list["Tweet"]] = relationship(
        "Tweet", secondary="tweet_medias", back_populates="medias", viewonly=True
    )
