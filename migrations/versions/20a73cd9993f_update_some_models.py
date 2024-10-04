"""update some models

Revision ID: 20a73cd9993f
Revises: bdb5b9afc914
Create Date: 2024-10-05 00:42:56.089429

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20a73cd9993f'
down_revision = 'bdb5b9afc914'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('papers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('papers', schema=None) as batch_op:
        batch_op.drop_column('created_at')

    # ### end Alembic commands ###
