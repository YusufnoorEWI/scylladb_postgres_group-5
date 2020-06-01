import uuid

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model

class OrderItem(Model):
    order_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    item_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    price = columns.Decimal()
    item_num = columns.BigInt()