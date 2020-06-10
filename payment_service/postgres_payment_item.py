import uuid

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Boolean, Numeric
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Payment(Base):
    # Define Payment table
    __tablename__ = 'payments'

    id = Column(UUID(as_uuid=True), primary_key=True, default= uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, default= uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), nullable=False, default= uuid.uuid4)
    status = Column(Boolean())
    amount = Column(Numeric())

    # Define all the views

    def __init__(self, user_id, order_id, status, amount):
        self.user_id = user_id,
        self.order_id = order_id,
        self.status = status
        self.amount = amount


