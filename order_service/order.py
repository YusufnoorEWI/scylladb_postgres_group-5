import uuid

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model

class Order(Model):
    order_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    user_id = columns.UUID(primary_key=False, default=uuid.uuid4)
    paid = columns.Boolean()