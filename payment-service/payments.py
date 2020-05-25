import uuid

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class Payments(Model):
    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    user_id = columns.UUID()
    order_id = columns.UUID()
    status = columns.Boolean()
    amount = columns.Decimal()
