"""add appointment priority and activity log

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-17

"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

priority_enum = sa.Enum("routine", "urgent", name="appointment_priority")


def upgrade():
    priority_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "appointments",
        sa.Column("priority", priority_enum, nullable=False, server_default="routine"),
    )
    op.create_table(
        "activity",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("message", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_activity_created_at", "activity", ["created_at"])


def downgrade():
    op.drop_index("ix_activity_created_at", table_name="activity")
    op.drop_table("activity")
    op.drop_column("appointments", "priority")
    priority_enum.drop(op.get_bind(), checkfirst=True)
