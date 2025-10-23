from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.tweet import Tweet
from app.models.user import User


def test_feed_returns_followed_tweets_sorted_by_popularity(client: TestClient, db_session: Session):
    tweets = db_session.query(Tweet).all()
    response = client.get("/api/tweets", headers={"api-key": "test"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"] is True

    expected_order = [tweet.id for tweet in sorted(tweets, key=lambda t: (len(t.likes), t.id), reverse=True)]
    actual_order = [tweet["id"] for tweet in payload["tweets"]]
    assert actual_order == expected_order


def test_cannot_attach_foreign_media_to_tweet(client: TestClient):
    upload = client.post(
        "/api/medias",
        headers={"api-key": "test"},
        files={"file": ("image.jpg", b"fake-image", "image/jpeg")},
    )
    assert upload.status_code == 200
    media_id = upload.json()["media_id"]

    create = client.post(
        "/api/tweets",
        headers={"api-key": "alice"},
        json={"tweet_data": "hello world", "tweet_media_ids": [media_id]},
    )
    assert create.status_code == 403
    body = create.json()
    assert body["result"] is False
    assert body["error_type"] == "http_error"
    assert "media" in body["error_message"]


def test_user_cannot_follow_self(client: TestClient, db_session: Session):
    alice = db_session.query(User).filter(User.api_key == "alice").first()
    assert alice is not None

    response = client.post(
        f"/api/users/{alice.id}/follow",
        headers={"api-key": "alice"},
    )
    assert response.status_code == 400
    body = response.json()
    assert body["result"] is False
    assert body["error_type"] == "http_error"
    assert "yourself" in body["error_message"]
