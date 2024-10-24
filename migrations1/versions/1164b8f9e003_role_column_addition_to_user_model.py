"""role column addition to user model

Revision ID: 1164b8f9e003
Revises: 100872e13f24
Create Date: 2024-07-17 13:29:03.863163

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1164b8f9e003'
down_revision = '100872e13f24'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('role', sa.Enum('AUTHOR', 'REVIEWER', 'EDITOR', name='role'), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('role')

    # ### end Alembic commands ###