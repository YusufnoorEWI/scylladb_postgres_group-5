import uuid

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, BigInteger, Numeric, Boolean
from sqlalchemy.schema import PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID

Base_order_item = declarative_base()


class PostgresOrderItem(Base_order_item):
    __tablename__ = 'order_item'

    order_id = Column(UUID(as_uuid=True), default=uuid.uuid4,  nullable=False)
    item_id = Column(UUID(as_uuid=True), default=uuid.uuid4,  nullable=False)
    price = Column(Numeric, nullable=False)
    item_num = Column(BigInteger, nullable=False)
    __table_args__ = (
        PrimaryKeyConstraint('order_id', 'item_id'),
        {},
    )

    def __init__(self, order_id, item_id, price, item_num):
        self.order_id = order_id,
        self.item_id = item_id,
        self.item_num = item_num,
        self.price = price
