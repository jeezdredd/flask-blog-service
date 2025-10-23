from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User

def ensure_users(db: Session):
    if db.query(User).count() == 0:
        db.add_all(
            [
                User(name="Cool Dev", api_key="test"),
                User(name="Alice", api_key="alice"),
                User(name="Bob", api_key="bob"),
            ]
        )
        db.commit()

if __name__ == "__main__":
    db = SessionLocal()
    try:
        ensure_users(db)
    finally:
        db.close()