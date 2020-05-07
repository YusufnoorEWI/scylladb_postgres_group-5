import uuid

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class Item(Model):
    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    price = columns.Decimal()
    count = columns.BigInt()


