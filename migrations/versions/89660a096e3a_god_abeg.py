"""God abeg

Revision ID: 89660a096e3a
Revises: e741b023a878
Create Date: 2024-11-04 15:37:11.472969

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '89660a096e3a'
down_revision = 'e741b023a878'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('reviewers',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('paper_id', sa.Integer(), nullable=False),
    sa.Column('reviewer_id', sa.Integer(), nullable=False),
    sa.Column('claimed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ),
    sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('papers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('reviewer_count', sa.Integer(), nullable=True))
        batch_op.drop_constraint('papers_ibfk_2', type_='foreignkey')
        batch_op.drop_column('assigned_reviewer_id')

    with op.batch_alter_table('review_history', schema=None) as batch_op:
        batch_op.alter_column('status',
               existing_type=mysql.ENUM('A', 'R', 'P', 'AMAR', 'AMIR', 'CUR'),
               nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('review_history', schema=None) as batch_op:
        batch_op.alter_column('status',
               existing_type=mysql.ENUM('A', 'R', 'P', 'AMAR', 'AMIR', 'CUR'),
               nullable=True)

    with op.batch_alter_table('papers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('assigned_reviewer_id', mysql.INTEGER(), autoincrement=False, nullable=True))
        batch_op.create_foreign_key('papers_ibfk_2', 'users', ['assigned_reviewer_id'], ['id'])
        batch_op.drop_column('reviewer_count')

    op.drop_table('reviewers')
    # ### end Alembic commands ###