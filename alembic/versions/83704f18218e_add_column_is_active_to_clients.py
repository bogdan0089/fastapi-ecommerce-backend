"""add column is_active to clients

Revision ID: 83704f18218e
Revises: 74015617f956
Create Date: 2026-04-18 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '83704f18218e'
down_revision: Union[str, Sequence[str], None] = '74015617f956'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('clients', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))


def downgrade() -> None:
    op.drop_column('clients', 'is_active')
