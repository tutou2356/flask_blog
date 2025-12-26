"""baseline

Revision ID: 0001_baseline
Revises: 
Create Date: 2025-12-25

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_baseline'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'post',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(length=100), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('tags', sa.Text(), nullable=True),
    )

    op.create_table(
        'visit',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('path', sa.String(length=255), nullable=False),
        sa.Column('method', sa.String(length=10), nullable=True),
        sa.Column('ip', sa.String(length=64), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('referrer', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('post_id', sa.Integer(), nullable=True),
    )

    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(length=80), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('password_hash', sa.String(length=200), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='visitor'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username'),
    )

    op.create_table(
        'comment',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('author_name', sa.String(length=80), nullable=False),
        sa.Column('author_email', sa.String(length=120), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_admin', sa.Boolean(), nullable=True),
        sa.Column('ip', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['post_id'], ['post.id']),
    )


def downgrade():
    op.drop_table('comment')
    op.drop_table('user')
    op.drop_table('visit')
    op.drop_table('post')
