"""update

Revision ID: bdb5b9afc914
Revises: 006a27dd9d2b
Create Date: 2024-10-04 11:24:51.605989

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'bdb5b9afc914'
down_revision = '006a27dd9d2b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_index('email')
        batch_op.drop_index('username')

    op.drop_table('user')
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('is_paid',
               existing_type=mysql.TINYINT(display_width=1),
               nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('is_paid',
               existing_type=mysql.TINYINT(display_width=1),
               nullable=False)

    op.create_table('user',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('username', mysql.VARCHAR(length=128), nullable=False),
    sa.Column('email', mysql.VARCHAR(length=255), nullable=False),
    sa.Column('role', mysql.ENUM('AUTHOR', 'REVIEWER', 'EDITOR'), nullable=False),
    sa.Column('first_name', mysql.VARCHAR(length=255), nullable=False),
    sa.Column('last_name', mysql.VARCHAR(length=255), nullable=False),
    sa.Column('phone_number', mysql.VARCHAR(length=20), nullable=False),
    sa.Column('is_paid', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
    sa.Column('password', mysql.VARCHAR(length=255), nullable=False),
    sa.Column('created_at', mysql.DATETIME(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.create_index('username', ['username'], unique=True)
        batch_op.create_index('email', ['email'], unique=True)

    # ### end Alembic commands ###