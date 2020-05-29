import uuid

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, BigInteger, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()


class PostgresOrder(Base):
    __tablename__ = 'stock_item'

    order_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    item_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    price = Column(Numeric, nullable=False)
    item_num = Column(BigInteger, nullable=False)

    def __init__(self, order_id, item_id, price, item_num):
        self.order_id = order_id,
        self.item_id = item_id,
        self.item_num = item_num,
        self.price = price