from cassandra.cluster import Cluster
from cassandra.cqlengine import connection, ValidationError
from cassandra.cqlengine.management import sync_table
from cassandra.cqlengine.query import QueryException

from .users_item import Users


class ScyllaConnector:
    def __init__(self):
        """Establishes a connection to the ScyllaDB database, creates the "wdm" keyspace if it does not exist
        and creates or updates the users table.
        """
        session = Cluster(['192.168.99.100']).connect()
        session.execute("""
            CREATE KEYSPACE IF NOT EXISTS wdm
            WITH replication = { 'class': 'SimpleStrategy', 'replication_factor': '2' }
            """)

        connection.setup(['192.168.99.100'], "wdm")
        sync_table(Users)

    @staticmethod
    def create():
        """Creates a user with zero initial credit.

        :return: the id of the created user
        """
        user = Users.create(credit=0.0)
        return user.id

    @staticmethod
    def remove(user_id):
        """Removes a user with the given user id.

        :raises ValueError: if there is no such user
        """
        try:
            Users.get(id=user_id).delete()
        except QueryException:
            raise ValueError(f"User with id {user_id} not found")

    @staticmethod
    def get_user(user_id):
        """Retrieves the user from the database by its id.

        :param item_id: the id of the user
        :raises ValueError: if the user with user_id does not exist or if the format of the user_id is invalid
        :return: the user with id user_id
        """
        try:
            item = Users.get(id=user_id)
        except QueryException:
            raise ValueError(f"Item with id {user_id} not found")
        except ValidationError:
            raise ValueError(f"Item id {user_id} is not a valid id")

        return item

    def add_amount(self, user_id, number):
        """Adds the given number to the user's credit.

        :param user_id: the id of the user
        :param number: the number to add to credit
        :return: the total credit
        """
        user = self.get_user(user_id)
        user.credit = user.credit + number
        Users.update(user)
        return user.credit

    def subtract_amount(self, user_id, number):
        """Subtracts the given number from the user's credit.

        :param user_id: the id of the user
        :param number: the number to subtract from credit
        :raises AssertionError: if the user credit after subtraction is negative
        :return: the remaining credit
        """
        user = self.get_user(user_id)

        user.credit = user.credit - number
        assert user.credit >= 0.0, 'Item count cannot be negative'

        Users.update(user)
        return user.credit
