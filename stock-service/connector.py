from cassandra.cluster import Cluster
from cassandra.cqlengine import connection, ValidationError
from cassandra.cqlengine.management import sync_table
from cassandra.cqlengine.query import QueryException

from .stock_item import StockItem


class ScyllaConnector:
    def __init__(self):
        """Establishes a connection to the ScyllaDB database, creates the "wdm" keyspace if it does not exist
        and creates or updates the stock_item table.
        """
        session = Cluster(['127.0.0.1']).connect()
        session.execute("""
            CREATE KEYSPACE IF NOT EXISTS wdm
            WITH replication = { 'class': 'SimpleStrategy', 'replication_factor': '2' }
            """)

        connection.setup(['127.0.0.1'], "wdm")
        sync_table(StockItem)

    @staticmethod
    def create_item(price):
        """Creates an item with the specified price.

        :param price: the price of the item
        :return: the id of the created item
        """
        item = StockItem.create(price=price, in_stock=0)
        return item.id

    @staticmethod
    def get_item(item_id):
        """Retrieves the item from the database by its id.

        :param item_id: the id of the item
        :raises ValueError: if the item with item_id does not exist or if the format of the item_id is invalid
        :return: the item with id item_id
        """
        try:
            item = StockItem.get(id=item_id)
        except QueryException:
            raise ValueError(f"Item with id {item_id} not found")
        except ValidationError:
            raise ValueError(f"Item id {item_id} is not a valid id")

        return item

    def add_amount(self, item_id, number):
        """Adds the given number to the item count.

        :param item_id: the id of the item
        :param number: the number to add to stock
        :return: the number of the item in stock
        """
        item = self.get_item(item_id)
        item.in_stock = item.in_stock + number
        StockItem.update(item)
        return item.in_stock

    def subtract_amount(self, item_id, number):
        """Subtracts the given number from the item count.

        :param item_id: the id of the item
        :param number: the number to subtract from stock
        :raises AssertionError: if the item count after subtraction is negative
        :return: the number of the item in stock
        """
        item = self.get_item(item_id)
        item.in_stock = item.in_stock - number

        assert item.in_stock >= 0, 'Item count cannot be negative'

        StockItem.update(item)
        return item.in_stock
