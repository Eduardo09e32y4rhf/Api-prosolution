"""Subscriptions table, encrypted IG token and post image_url

- Cria `subscriptions` (assinatura com data de expiração) e migra quem tinha
  `users.is_vip = true` para uma assinatura ativa de PRO_PLAN_DAYS dias.
- Remove `users.is_vip`.
- Adiciona `posts.image_url` (exigido pela Graph API para publicar).
- Converte `brand_profiles.ig_access_token` para Text e criptografa os tokens já salvos.

Revision ID: 7b3e9f1c2d4a
Revises: 5cc56dc26eb6
Create Date: 2026-10-21 12:00:00.000000

"""

from collections.abc import Sequence
from datetime import timedelta

import sqlalchemy as sa

from alembic import op
from app.core.config import settings
from app.core.crypto import decrypt, encrypt
from app.core.timeutils import utcnow

revision: str = "7b3e9f1c2d4a"
down_revision: str | Sequence[str] | None = "5cc56dc26eb6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("plan", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("current_period_end", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_subscriptions_id"), "subscriptions", ["id"], unique=False)

    conn = op.get_bind()
    now = utcnow()
    vip_ids = conn.execute(sa.text("SELECT id FROM users WHERE is_vip = :t"), {"t": True}).scalars().all()
    for user_id in vip_ids:
        conn.execute(
            sa.text(
                "INSERT INTO subscriptions (user_id, plan, status, current_period_end, created_at, updated_at) "
                "VALUES (:user_id, 'pro', 'active', :end, :now, :now)"
            ),
            {"user_id": user_id, "end": now + timedelta(days=settings.PRO_PLAN_DAYS), "now": now},
        )

    with op.batch_alter_table("users") as batch:
        batch.drop_column("is_vip")

    op.add_column("posts", sa.Column("image_url", sa.String(), nullable=True))

    with op.batch_alter_table("brand_profiles") as batch:
        batch.alter_column("ig_access_token", type_=sa.Text(), existing_type=sa.String(), existing_nullable=True)

    rows = conn.execute(
        sa.text("SELECT id, ig_access_token FROM brand_profiles WHERE ig_access_token IS NOT NULL")
    ).all()
    for row_id, token in rows:
        conn.execute(
            sa.text("UPDATE brand_profiles SET ig_access_token = :token WHERE id = :id"),
            {"token": encrypt(token), "id": row_id},
        )


def downgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(
        sa.text("SELECT id, ig_access_token FROM brand_profiles WHERE ig_access_token IS NOT NULL")
    ).all()
    for row_id, token in rows:
        conn.execute(
            sa.text("UPDATE brand_profiles SET ig_access_token = :token WHERE id = :id"),
            {"token": decrypt(token), "id": row_id},
        )
    with op.batch_alter_table("brand_profiles") as batch:
        batch.alter_column("ig_access_token", type_=sa.String(), existing_type=sa.Text(), existing_nullable=True)

    op.drop_column("posts", "image_url")

    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("is_vip", sa.Boolean(), nullable=True))
    conn.execute(
        sa.text(
            "UPDATE users SET is_vip = :t WHERE id IN "
            "(SELECT user_id FROM subscriptions WHERE status = 'active' AND current_period_end > :now)"
        ),
        {"t": True, "now": utcnow()},
    )

    op.drop_index(op.f("ix_subscriptions_id"), table_name="subscriptions")
    op.drop_table("subscriptions")
