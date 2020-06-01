import uuid

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, BigInteger, Numeric
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()


class PostgresStockItem(Base):
    __tablename__ = 'stock_item'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    price = Column(Numeric, nullable=False)
    in_stock = Column(BigInteger, nullable=False)

    def __init__(self, price, in_stock):
        self.price = price,
        self.in_stock = in_stock

