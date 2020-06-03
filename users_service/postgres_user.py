import uuid

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, BigInteger, Numeric
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()


class PostgresStockItem(Base):
    __tablename__ = 'stock_item'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    credit = Column(Numeric, nullable=False)

    def __init__(self, credit):
        self.credit = credit
