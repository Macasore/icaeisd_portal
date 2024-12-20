"""Add logged_in column to User model

Revision ID: 006a27dd9d2b
Revises: 407516732338
Create Date: 2024-10-04 11:18:53.081079

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006a27dd9d2b'
down_revision = '407516732338'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('logged_in', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('logged_in')

    # ### end Alembic commands ###
