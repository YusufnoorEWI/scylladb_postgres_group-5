import uuid

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class ScyllaOrder(Model):
    order_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    user_id = columns.UUID(primary_key=True, default=uuid.uuid4, custom_index=True)
    paid = columns.Boolean()
