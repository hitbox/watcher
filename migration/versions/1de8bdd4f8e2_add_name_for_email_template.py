"""Add name for email_template

Revision ID: 1de8bdd4f8e2
Revises: 
Create Date: 2026-09-14 17:28:51.188394

"""
import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '1de8bdd4f8e2'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Upgrade schema."""
    # Add name column for email_template
    op.add_column(
        'email_template',
        sa.Column('name',
        sa.String(),
        nullable=True),
    )
    op.create_unique_constraint(
        None,
        'email_template',
        ['name'],
    )

def downgrade():
    """Downgrade schema."""
    # Drop name column for email_template
    op.drop_column('email_template', 'name')
