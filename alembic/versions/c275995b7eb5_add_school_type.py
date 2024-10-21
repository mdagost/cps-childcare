"""Add school_type.

Revision ID: c275995b7eb5
Revises: 0fc9bb7d322a
Create Date: 2024-09-19 15:32:25.352925

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'c275995b7eb5'
down_revision: Union[str, None] = '0fc9bb7d322a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('crawleropenairecord', sa.Column('school_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False))
    op.add_column('crawlerrecord', sa.Column('school_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('crawlerrecord', 'school_type')
    op.drop_column('crawleropenairecord', 'school_type')
    # ### end Alembic commands ###
