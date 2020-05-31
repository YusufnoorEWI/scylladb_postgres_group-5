import uuid

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class Payments(Model):
    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    user_id = columns.UUID(default=uuid.uuid4)
    order_id = columns.UUID(default=uuid.uuid4, index=True)
    status = columns.Boolean()
    amount = columns.Decimal()
