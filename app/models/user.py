from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer
from app.db.session import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

# связи объявим после импорта зависимых классов
from app.models.tweet import Tweet  # noqa: E402
User.tweets = relationship(Tweet, back_populates="author", cascade="all,delete")