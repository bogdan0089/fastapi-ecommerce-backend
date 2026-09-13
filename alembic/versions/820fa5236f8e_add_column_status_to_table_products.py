"""add column status to table products

Revision ID: 820fa5236f8e
Revises: 0c070ef68db0
Create Date: 2026-04-12 17:40:48.947324

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '820fa5236f8e'
down_revision: Union[str, Sequence[str], None] = '0c070ef68db0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    sa.Enum('superadmin', 'moderator', 'client', name='role').create(op.get_bind(), checkfirst=True)
    sa.Enum('pending', 'accept', 'rejected', name='productstatus').create(op.get_bind(), checkfirst=True)
    op.add_column('clients', sa.Column('role', sa.Enum('superadmin', 'moderator', 'client', name='role', create_type=False), nullable=False, server_default='client'))
    op.create_unique_constraint(None, 'clients', ['email'])
    op.add_column('products', sa.Column('status', sa.Enum('pending', 'accept', 'rejected', name='productstatus', create_type=False), nullable=False, server_default='pending'))
    op.alter_column('products', 'price',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('products', 'price',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               nullable=True)
    op.drop_column('products', 'status')
    op.drop_constraint('clients_email_key', 'clients', type_='unique')
    op.drop_column('clients', 'role')
    sa.Enum(name='role').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='productstatus').drop(op.get_bind(), checkfirst=True)
