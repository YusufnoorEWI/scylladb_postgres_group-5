import requests
from cassandra.cluster import Cluster
from cassandra.cqlengine import connection, ValidationError
from cassandra.cqlengine.management import sync_table
from cassandra.cqlengine.query import QueryException

from .payments import Payments


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
        sync_table(Payments)

    @staticmethod
    def pay(user_id, order_id, amount):
        """Pays the order
        """
        try:
            payment = Payments.get(user_id=user_id, order_id=order_id)

            # TODO: GET THE IP FROM DOCKER COMPOSE
            # TODO: SUBTRACT amount from the user's credit
            # users_response = requests.post(f"http://{user_ip}/users/credit/subtract/{user_id}/{amount}")
            # if users_response.status_code == 400 or users_response.status_code == 404:
            #     raise ValueError(f"problem with user endpoint")

            payment.status = True
            payment.amount = amount
            Payments.update(payment)
        except QueryException:
            raise ValueError(f"Payment with order_id {order_id} not found")
        except ValidationError:
            raise ValueError(f"Payment order_id {order_id} is not a valid id")

    @staticmethod
    def cancel_pay(user_id, order_id):
        """Cancels the payment.

        :raises ValueError: if there is no such user
        """
        try:
            payment = Payments.get(user_id=user_id, order_id=order_id)
            # TODO: GET THE IP FROM DOCKER COMPOSE
            # TODO: ADD TO THE USER'S CREDIT WITH payment.amount
            # users_response = requests.post(f"http://{user_ip}/users/credit/add/{user_id}/{payment.amount}")
            # if users_response.status_code == 400 or users_response.status_code == 404:
            #     abort(400, "User service failure")

            payment.status = False
            Payments.update(payment)
        except QueryException:
            raise ValueError(f"Payment with order_id {order_id} not found")
        except ValidationError:
            raise ValueError(f"Payment order_id {order_id} is not a valid id")

    @staticmethod
    def status(order_id):
        """Retrieves the payment from the database by its order_id.

        :param order_id: the id of the order
        :raises ValueError: if the order with order_id does not exist or if the format of the order_id is invalid
        :return: the payment with order_id order_id
        """
        try:
            payment = Payments.get(order_id=order_id)
        except QueryException:
            raise ValueError(f"Payment with order_id {order_id} not found")
        except ValidationError:
            raise ValueError(f"Payment order_id {order_id} is not a valid id")

        return payment
