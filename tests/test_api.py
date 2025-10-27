from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.follow import Follow
from app.models.tweet import Tweet
from app.models.user import User


def test_feed_returns_followed_tweets_sorted_by_popularity(client: TestClient, db_session: Session):
    current_user = db_session.query(User).filter(User.api_key == "test").first()
    assert current_user is not None

    followed_ids = {
        row.followee_id for row in db_session.query(Follow.followee_id).filter(Follow.follower_id == current_user.id)
    }
    followed_ids.add(current_user.id)

    tweets = db_session.query(Tweet).filter(Tweet.author_id.in_(followed_ids)).all()
    response = client.get("/api/tweets", headers={"api-key": "test"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"] is True

    expected_order = [
        tweet.id
        for tweet in sorted(
            tweets,
            key=lambda t: (len(t.likes), t.created_at, t.id),
            reverse=True,
        )
    ]
    actual_order = [tweet["id"] for tweet in payload["tweets"]]
    assert actual_order == expected_order

    if payload["tweets"]:
        first = payload["tweets"][0]
        assert "stamp" in first
        for like in first["likes"]:
            assert "user_id" in like
            assert "name" in like


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


def test_feed_pagination_limits_results(client: TestClient):
    response = client.get("/api/tweets?offset=1&limit=1", headers={"api-key": "test"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["result"] is True
    assert len(payload["tweets"]) == 1


def test_feed_includes_own_tweets(client: TestClient, db_session: Session):
    user = db_session.query(User).filter(User.api_key == "test").first()
    assert user is not None

    tweet = Tweet(content="my fresh update", author_id=user.id)
    db_session.add(tweet)
    db_session.commit()

    response = client.get("/api/tweets", headers={"api-key": "test"})
    assert response.status_code == 200
    tweet_ids = {item["id"] for item in response.json()["tweets"]}
    assert tweet.id in tweet_ids


def test_users_listing_returns_follow_state(client: TestClient):
    response = client.get("/api/users", headers={"api-key": "test"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["result"] is True
    users = payload["users"]
    assert any(user["is_me"] for user in users)
    assert all("is_following" in user for user in users)


def test_followers_and_following_endpoints(client: TestClient, db_session: Session):
    alice = db_session.query(User).filter(User.api_key == "alice").first()
    assert alice is not None

    followers_resp = client.get(f"/api/users/{alice.id}/followers", headers={"api-key": "test"})
    assert followers_resp.status_code == 200
    assert followers_resp.json()["result"] is True

    following_resp = client.get(f"/api/users/{alice.id}/following", headers={"api-key": "test"})
    assert following_resp.status_code == 200
    assert following_resp.json()["result"] is True
