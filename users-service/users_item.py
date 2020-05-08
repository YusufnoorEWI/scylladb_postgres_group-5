import uuid

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class Users(Model):
    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    credit = columns.Float()
