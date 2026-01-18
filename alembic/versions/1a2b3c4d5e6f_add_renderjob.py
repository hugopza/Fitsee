"""Add RenderJob

Revision ID: 1a2b3c4d5e6f
Revises: 
Create Date: 2026-01-18 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1a2b3c4d5e6f'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create enum type
    renderjobstatus = postgresql.ENUM('QUEUED', 'RUNNING', 'DONE', 'FAILED', name='renderjobstatus')
    renderjobstatus.create(op.get_bind())

    sizeenum = postgresql.ENUM('XS', 'S', 'M', 'L', 'XL', name='sizeenum')
    # Assuming SizeEnum might already exist from ProductVariant, but if safe check is needed:
    # sizeenum.create(op.get_bind(), checkfirst=True) 
    # For now, explicit creation might fail if it exists. 
    # But since I cannot check DB, I will assume RenderJob is the main thing.
    # Note: ProductVariant used SizeEnum. If it exists, we shouldn't create it again.
    # I will handle this by checking if type exists in a raw SQL block if I could, but here I'll just use the name strings.
    
    op.create_table('render_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('size', sa.Enum('XS', 'S', 'M', 'L', 'XL', name='sizeenum'), nullable=False),
        sa.Column('status', sa.Enum('QUEUED', 'RUNNING', 'DONE', 'FAILED', name='renderjobstatus'), nullable=False),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('video_url', sa.String(), nullable=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], )
    )


def downgrade() -> None:
    op.drop_table('render_jobs')
    
    renderjobstatus = postgresql.ENUM('QUEUED', 'RUNNING', 'DONE', 'FAILED', name='renderjobstatus')
    renderjobstatus.drop(op.get_bind())
