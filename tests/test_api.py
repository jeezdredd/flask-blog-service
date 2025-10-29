from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.follow import Follow
from app.models.like import Like
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
    assert payload["pagination"]["sort"] == "popular"

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
        assert "likes_count" in first
        assert "liked_by_me" in first

    liked_by_me_ids = {
        like.tweet_id for like in db_session.query(Like).filter(Like.user_id == current_user.id).all()
    }
    for item in payload["tweets"]:
        assert item["likes_count"] == len(item["likes"])
        if item["id"] in liked_by_me_ids:
            assert item["liked_by_me"] is True
        else:
            assert item["liked_by_me"] is False


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
    first_page = client.get("/api/tweets?limit=1&page=1", headers={"api-key": "test"})
    assert first_page.status_code == 200
    first_payload = first_page.json()
    assert first_payload["result"] is True
    assert len(first_payload["tweets"]) == 1
    assert first_payload["pagination"]["page"] == 1

    second_page = client.get("/api/tweets?limit=1&page=2", headers={"api-key": "test"})
    assert second_page.status_code == 200
    second_payload = second_page.json()
    assert second_payload["result"] is True
    assert len(second_payload["tweets"]) == 1
    assert second_payload["pagination"]["page"] == 2

    assert first_payload["tweets"][0]["id"] != second_payload["tweets"][0]["id"]
    assert first_payload["pagination"]["has_next"] is True
    assert second_payload["pagination"]["has_previous"] is True


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


def test_feed_can_sort_by_latest(client: TestClient, db_session: Session):
    user = db_session.query(User).filter(User.api_key == "test").first()
    assert user is not None

    tweet = Tweet(content="most recent insight", author_id=user.id)
    db_session.add(tweet)
    db_session.commit()

    response = client.get("/api/tweets?sort=latest", headers={"api-key": "test"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["result"] is True
    assert payload["pagination"]["sort"] == "latest"
    assert payload["tweets"][0]["id"] == tweet.id


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


def test_dashboard_overview_returns_metrics(client: TestClient):
    response = client.get("/api/dashboard", headers={"api-key": "test"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["result"] is True
    stats = payload["stats"]
    assert {"total_users", "total_tweets", "total_likes", "popular_authors", "trending_tweets"} <= stats.keys()
    assert isinstance(stats["popular_authors"], list)
    assert isinstance(stats["trending_tweets"], list)
    if stats["popular_authors"]:
        first_author = stats["popular_authors"][0]
        assert {"user_id", "name", "followers_count", "tweet_count"} <= first_author.keys()
    if stats["trending_tweets"]:
        first_tweet = stats["trending_tweets"][0]
        assert {"tweet_id", "content", "author", "likes_count"} <= first_tweet.keys()
