from alembic import op
import sqlalchemy as sa

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("api_key", sa.String(255), nullable=False, unique=True, index=True),
    )
    op.create_table(
        "medias",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("path", sa.String(512), nullable=False),
        sa.Column("uploader_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
    )
    op.create_table(
        "tweets",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("content", sa.String(1000), nullable=False),
        sa.Column("author_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
    )
    op.create_table(
        "tweet_medias",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("tweet_id", sa.Integer, sa.ForeignKey("tweets.id", ondelete="CASCADE")),
        sa.Column("media_id", sa.Integer, sa.ForeignKey("medias.id", ondelete="CASCADE")),
    )
    op.create_table(
        "likes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("tweet_id", sa.Integer, sa.ForeignKey("tweets.id", ondelete="CASCADE")),
        sa.UniqueConstraint("user_id", "tweet_id", name="uq_like_user_tweet"),
    )
    op.create_table(
        "follows",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("follower_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("followee_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.UniqueConstraint("follower_id", "followee_id", name="uq_follow_pair"),
    )

def downgrade():
    op.drop_table("follows")
    op.drop_table("likes")
    op.drop_table("tweet_medias")
    op.drop_table("tweets")
    op.drop_table("medias")
    op.drop_table("users")