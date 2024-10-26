"""edit password and username

Revision ID: f22699bcfb4c
Revises: daa880a820ed
Create Date: 2024-10-26 13:14:54.958487

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'f22699bcfb4c'
down_revision = 'daa880a820ed'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('username',
               existing_type=mysql.VARCHAR(length=128),
               nullable=True)
        batch_op.alter_column('password',
               existing_type=mysql.VARCHAR(length=255),
               nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('password',
               existing_type=mysql.VARCHAR(length=255),
               nullable=False)
        batch_op.alter_column('username',
               existing_type=mysql.VARCHAR(length=128),
               nullable=False)

    # ### end Alembic commands ###
