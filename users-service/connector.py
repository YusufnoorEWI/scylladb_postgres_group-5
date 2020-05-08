from cassandra.cluster import Cluster
from cassandra.cqlengine import connection, ValidationError
from cassandra.cqlengine.management import sync_table
from cassandra.cqlengine.query import QueryException

from .users_item import UsersItem


class ScyllaConnector:
    def __init__(self):
        """Establishes a connection to the ScyllaDB database, creates the "wdm" keyspace if it does not exist
        and creates or updates the stock_item table.
        """
        session = Cluster(['192.168.99.100']).connect()
        session.execute("""
            CREATE KEYSPACE IF NOT EXISTS wdm
            WITH replication = { 'class': 'SimpleStrategy', 'replication_factor': '2' }
            """)

        connection.setup(['192.168.99.100'], "wdm")
        sync_table(UsersItem)

    @staticmethod
    def create():
        """Creates an item with the specified price.

        :return: the id of the created item
        """
        user = UsersItem.create(credit=0.0)
        return user.id

    @staticmethod
    def remove(user_id):
        """Creates an item with the specified price.

        :return: the id of the created item
        """
        try:
            UsersItem.get(id=user_id).delete()
        except QueryException:
            raise ValueError(f"User with id {user_id} not found")

    @staticmethod
    def get_user(user_id):
        """Retrieves the item from the database by its id.

        :param item_id: the id of the item
        :raises ValueError: if the item with item_id does not exist or if the format of the item_id is invalid
        :return: the item with id item_id
        """
        try:
            item = UsersItem.get(id=user_id)
        except QueryException:
            raise ValueError(f"Item with id {user_id} not found")
        except ValidationError:
            raise ValueError(f"Item id {user_id} is not a valid id")

        return item

    def add_amount(self, user_id, number):
        """Adds the given number to the item count.

        :param item_id: the id of the item
        :param number: the number to add to stock
        :return: the number of the item in stock
        """
        user = self.get_user(user_id)
        user.credit = user.credit + number
        UsersItem.update(user)
        return user.in_stock

    def subtract_amount(self, user_id, number):
        """Subtracts the given number from the item count.

        :param item_id: the id of the item
        :param number: the number to subtract from stock
        :raises AssertionError: if the item count after subtraction is negative
        :return: the number of the item in stock
        """
        user = self.get_user(user_id)

        user.credit = user.credit - number
        assert user.credit >= 0.0, 'Item count cannot be negative'

        UsersItem.update(user)
        return user.credit
