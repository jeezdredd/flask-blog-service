from __future__ import annotations

import base64
from pathlib import Path
from typing import Dict

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import Follow, Like, Media, Tweet, TweetMedia, User

USER_FIXTURES = [
    ("Cool Dev", "test"),
    ("Alice", "alice"),
    ("Bob", "bob"),
]

MEDIA_DIR = Path("media")
SAMPLE_IMAGE_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="


def ensure_sample_media() -> Path:
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    sample_path = MEDIA_DIR / "welcome.png"
    if not sample_path.exists():
        sample_path.write_bytes(base64.b64decode(SAMPLE_IMAGE_B64))
    return sample_path


def ensure_users(db: Session) -> Dict[str, User]:
    if db.query(User).count() == 0:
        db.add_all([User(name=name, api_key=api_key) for name, api_key in USER_FIXTURES])
        db.commit()

    users = {user.api_key: user for user in db.query(User).all()}
    return users


def seed_demo_data(db: Session) -> None:
    users = ensure_users(db)

    follow_pairs = [
        ("test", "alice"),
        ("test", "bob"),
        ("alice", "bob"),
        ("alice", "test"),
        ("bob", "alice"),
        ("bob", "test"),
    ]
    existing_follows = {(follow.follower_id, follow.followee_id) for follow in db.query(Follow).all()}
    for follower_key, followee_key in follow_pairs:
        follower = users.get(follower_key)
        followee = users.get(followee_key)
        if not follower or not followee:
            continue
        pair = (follower.id, followee.id)
        if pair not in existing_follows:
            db.add(Follow(follower_id=follower.id, followee_id=followee.id))

    alice = users.get("alice")
    bob = users.get("bob")
    demo_viewer = users.get("test")

    if db.query(Tweet).count() == 0 and alice and bob:
        tweets = [
            Tweet(content="Добро пожаловать в корпоративный микроблог!", author_id=alice.id),
            Tweet(content="Мы теперь можем делиться новостями и идеями ⚡️", author_id=bob.id),
            Tweet(content="Лайкайте и комментируйте — это помогает!", author_id=alice.id),
        ]
        db.add_all(tweets)
        db.flush()

        if demo_viewer:
            db.add_all(
                [
                    Like(user_id=demo_viewer.id, tweet_id=tweets[0].id),
                    Like(user_id=demo_viewer.id, tweet_id=tweets[1].id),
                ]
            )
        db.add(Like(user_id=alice.id, tweet_id=tweets[1].id))

        sample_path = ensure_sample_media()
        media = (
            db.query(Media)
            .filter(Media.path == f"/media/{sample_path.name}")
            .filter(Media.uploader_id == alice.id)
            .first()
        )
        if not media:
            media = Media(path=f"/media/{sample_path.name}", uploader_id=alice.id)
            db.add(media)
            db.flush()
        if not db.query(TweetMedia).filter_by(tweet_id=tweets[0].id, media_id=media.id).first():
            db.add(TweetMedia(tweet_id=tweets[0].id, media_id=media.id))

    db.commit()


if __name__ == "__main__":
    session = SessionLocal()
    try:
        seed_demo_data(session)
    finally:
        session.close()
