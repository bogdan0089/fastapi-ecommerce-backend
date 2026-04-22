"""add image_url to products

Revision ID: 8ac24070988a
Revises: 83704f18218e
Create Date: 2026-04-22 16:36:17.153242

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8ac24070988a'
down_revision: Union[str, Sequence[str], None] = '83704f18218e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('products', sa.Column('image_url', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('products', 'image_url')
