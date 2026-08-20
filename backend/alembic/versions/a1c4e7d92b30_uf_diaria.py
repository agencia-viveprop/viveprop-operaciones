"""serie diaria de UF

Revision ID: a1c4e7d92b30
Revises: b2dbf50bc5fc
Create Date: 2026-08-20
"""
from alembic import op
import sqlalchemy as sa

revision = "a1c4e7d92b30"
down_revision = "b2dbf50bc5fc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "uf_diaria",
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("valor", sa.Numeric(12, 2), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("fecha"),
    )


def downgrade() -> None:
    op.drop_table("uf_diaria")
