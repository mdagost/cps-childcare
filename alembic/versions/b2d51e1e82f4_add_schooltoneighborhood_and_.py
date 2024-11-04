"""Add schooltoneighborhood and neighborhood models.

Revision ID: b2d51e1e82f4
Revises: c992adf61e4f
Create Date: 2024-10-31 14:24:58.232736

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'b2d51e1e82f4'
down_revision: Union[str, None] = 'c992adf61e4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('neighborhood',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('neighborhood', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('student_count', sa.Integer(), nullable=True),
    sa.Column('low_income_student_count', sa.Integer(), nullable=True),
    sa.Column('low_income_student_pct', sa.Float(), nullable=True),
    sa.Column('black_student_count', sa.Integer(), nullable=True),
    sa.Column('black_student_pct', sa.Float(), nullable=True),
    sa.Column('hispanic_student_count', sa.Integer(), nullable=True),
    sa.Column('hispanic_student_pct', sa.Float(), nullable=True),
    sa.Column('white_student_count', sa.Integer(), nullable=True),
    sa.Column('white_student_pct', sa.Float(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('schooltoneighborhood',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('school_id', sa.Integer(), nullable=False),
    sa.Column('school_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('neighborhood', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('schooltoneighborhood')
    op.drop_table('neighborhood')
    # ### end Alembic commands ###
