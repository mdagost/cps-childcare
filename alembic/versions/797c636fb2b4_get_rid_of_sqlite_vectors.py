"""get rid of sqlite vectors

Revision ID: 797c636fb2b4
Revises: b2d51e1e82f4
Create Date: 2024-11-27 13:48:14.436330

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '797c636fb2b4'
down_revision: Union[str, None] = 'b2d51e1e82f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
