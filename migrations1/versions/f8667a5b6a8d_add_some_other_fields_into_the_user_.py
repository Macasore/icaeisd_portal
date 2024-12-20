"""add some other fields into the user model

Revision ID: f8667a5b6a8d
Revises: 1164b8f9e003
Create Date: 2024-08-06 19:32:23.982283

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f8667a5b6a8d'
down_revision = '1164b8f9e003'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('first_name', sa.String(length=255), nullable=False))
        batch_op.add_column(sa.Column('last_name', sa.String(length=255), nullable=False))
        batch_op.add_column(sa.Column('phone_number', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('is_paid', sa.Boolean(), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('is_paid')
        batch_op.drop_column('phone_number')
        batch_op.drop_column('last_name')
        batch_op.drop_column('first_name')

    # ### end Alembic commands ###
