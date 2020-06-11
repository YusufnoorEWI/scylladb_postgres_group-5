import uuid

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, BigInteger, Numeric, Boolean
from sqlalchemy.schema import PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID

Base_order = declarative_base()


class PostgresOrder(Base_order):
    __tablename__ = 'order'

    order_id = Column(UUID(as_uuid=True), default=uuid.uuid4,  nullable=False)
    user_id = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False)
    paid = Column(Boolean, nullable=False)
    __table_args__ = (
        PrimaryKeyConstraint('order_id', 'user_id'),
        {},
    )

    def __init__(self, user_id):
        self.user_id = user_id
        self.paid = False
