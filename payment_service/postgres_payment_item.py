from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Payment(Base):
    # Define Payment table
    __table_name__ = 'payments'

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id =Column(UUID(as_uuid=True), nullable=False)
    order_id = Column(UUID(as_uuid=True), nullable=False)
    status = Column(Boolean())
    amount = Column(Float())

    # Define all the views
    def get_data(self):
        return {
            'user_id': str(self.user_id),
            'payment_id': str(self.payment_id),
            'status': self.status,
            'order_id': str(self.order_id),
            'amount': str(self.amount)
        }

    def get_status(self):
        return {
            'status': self.status
        }
