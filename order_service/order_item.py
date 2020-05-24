import uuid

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model

class OrderItem(Model):
    order_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    user_id = columns.UUID(primary_key=False, default=uuid.uuid4)
    paid = columns.Boolean()
    items_list = columns.List(columns.UUID(primary_key=False, default=uuid.uuid4))
    total_cost = columns.Decimal()