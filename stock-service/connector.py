from cassandra.cluster import Cluster
from cassandra.cqlengine import connection, ValidationError
from cassandra.cqlengine.management import sync_table
from cassandra.cqlengine.query import QueryException

from .item import Item


class ScyllaConnector:
    def __init__(self):
        session = Cluster(['127.0.0.1']).connect()
        session.execute("""
            CREATE KEYSPACE IF NOT EXISTS wdm
            WITH replication = { 'class': 'SimpleStrategy', 'replication_factor': '2' }
            """)

        connection.setup(['127.0.0.1'], "wdm")
        sync_table(Item)

    @staticmethod
    def create_item(price):
        item = Item.create(price=price, count=0)
        return item.id

    @staticmethod
    def get_item(item_id):
        try:
            item = Item.get(id=item_id)
        except QueryException:
            raise ValueError(f"Item with id {item_id} not found")
        except ValidationError:
            raise ValueError(f"Item id {item_id} is not a valid id")

        return item

    def add_amount(self, item_id, number):
        item = self.get_item(item_id)
        item.count = item.count + number
        Item.update(item)
        return item.count

    def subtract_amount(self, item_id, number):
        item = self.get_item(item_id)
        item.count = item.count - number

        assert item.count >= 0, 'Item count cannot be negative'

        Item.update(item)
        return item.count

    def get_availability(self, item_id):
        item = self.get_item(item_id)
        return item.count
