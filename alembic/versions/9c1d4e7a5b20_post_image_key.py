"""Post image_key (imagem guardada em armazenamento próprio)

Troca `posts.image_url` (URL colada pelo usuário) por `posts.image_key` (chave do arquivo no
armazenamento; a URL pública passa a ser derivada). URLs coladas à mão não são migradas: a
coluna existia há poucas horas e nunca foi usada em produção, e uma imagem hospedada fora
não pode ser revalidada nem apagada por nós.

Revision ID: 9c1d4e7a5b20
Revises: 7b3e9f1c2d4a
Create Date: 2026-10-22 09:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "9c1d4e7a5b20"
down_revision: str | Sequence[str] | None = "7b3e9f1c2d4a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("posts") as batch:
        batch.add_column(sa.Column("image_key", sa.String(), nullable=True))
        batch.drop_column("image_url")
    # Posts agendados que dependiam de uma URL colada à mão ficam sem imagem e voltam a rascunho
    op.execute("UPDATE posts SET status = 'draft' WHERE status = 'scheduled' AND image_key IS NULL")


def downgrade() -> None:
    with op.batch_alter_table("posts") as batch:
        batch.add_column(sa.Column("image_url", sa.String(), nullable=True))
        batch.drop_column("image_key")
