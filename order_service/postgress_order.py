import uuid

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, BigInteger, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()


class PostgresOrder(Base):
    __tablename__ = 'order'

    order_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), primary_key=False, default=uuid.uuid4, unique=True, nullable=False)
    paid = Column(Boolean, nullable=False)

    def __init__(self, user_id):
        self.user_id = user_id,
        self.paid = False