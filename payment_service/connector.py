import os
from time import sleep
from flask import abort
import requests
from cassandra.cluster import Cluster
from cassandra.cqlengine import connection, ValidationError
from cassandra.cqlengine.management import sync_table
from cassandra.cqlengine.query import QueryException

from payment_service.payments import Payments


class ScyllaConnector:
    def __init__(self, host):
        """Establishes a connection to the ScyllaDB database, creates the "wdm" keyspace if it does not exist
        and creates or updates the users table.
        """
        while True:
            try:
                session = Cluster([host]).connect()
                break
            except Exception:
                sleep(1)
        session.execute("""
            CREATE KEYSPACE IF NOT EXISTS wdm
            WITH replication = { 'class': 'SimpleStrategy', 'replication_factor': '2' }
            """)

        connection.setup([host], "wdm")
        sync_table(Payments)

    def pay(self, user_id, order_id, amount):
        """Pays the order
        """
        try:
            payment = Payments.get(order_id=order_id)
            if payment.status:
                abort(400, "the payment is already made")
            self.request_user_to_pay(user_id, amount)
            payment.status = True
            payment.amount = amount
            Payments.update(payment)
        except QueryException:
            self.request_user_to_pay(user_id, amount)
            Payments.create(user_id=user_id, order_id=order_id, amount=amount, status=True)
        except ValidationError:
            abort(400, f"Payment order_id {order_id} is not a valid id")

    @staticmethod
    def request_user_to_pay(user_id, amount):
        users_response = requests \
            .post(f"http://{os.environ['USER_SERVICE_URL']}/users/credit/subtract/{user_id}/{amount}")
        if users_response.status_code == 400 or users_response.status_code == 404:
            abort(400, "User service failure")

    @staticmethod
    def cancel_pay(user_id, order_id):
        """Cancels the payment.

        :raises ValueError: if there is no such user
        """
        try:
            payment = Payments.get(order_id=order_id)
            if not payment.status:
                abort(400, "the payment is already canceled")
            users_response = requests\
                .post(f"http://{os.environ['USER_SERVICE_URL']}/users/credit/add/{user_id}/{payment.amount}")
            if users_response.status_code == 400 or users_response.status_code == 404:
                abort(400, "User service failure")
            payment.status = False
            Payments.update(payment)
        except QueryException:
            abort(400, 'payment does not exist')
        except ValidationError:
            abort(400, f"Payment order_id {order_id} is not a valid id")

    @staticmethod
    def status(order_id):
        """Retrieves the payment from the database by its order_id.

        :param order_id: the id of the order
        :raises ValueError: if the order with order_id does not exist or if the format of the order_id is invalid
        :return: the payment with order_id order_id
        """
        try:
            payment = Payments.get(order_id=order_id)
            return payment.status
        except QueryException:
            abort(400, 'payment does not exist')
        except ValidationError:
            abort(400, f"Payment order_id {order_id} is not a valid id")
