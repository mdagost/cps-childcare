"""Simplify combined field validator.

Revision ID: f9ffe487856b
Revises: b7e1394dd00e
Create Date: 2024-10-23 12:15:07.383080

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'f9ffe487856b'
down_revision: Union[str, None] = 'b7e1394dd00e'
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
