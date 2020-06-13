import os
from time import sleep
from cassandra import ConsistencyLevel
from flask import abort
import requests
from cassandra.cluster import Cluster
from cassandra.cqlengine import connection, ValidationError
from cassandra.cqlengine.management import sync_table
from cassandra.cqlengine.query import QueryException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine
from sqlalchemy.exc import DataError
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from payment_service.scylla_payment_item import Payments
from payment_service.postgres_payment_item import Base, Payment


class ConnectorFactory:
    def __init__(self):
        """Initializes a database connector factory with parameters set by the environment variables."""
        self.db_host = os.getenv("DB_HOST", 'localhost')
        self.db_type = os.getenv("DATABASE_TYPE", 'postgres')
        self.postgres_user = os.getenv('POSTGRES_USER', 'postgres')
        self.postgres_password = os.getenv('POSTGRES_PASSWORD', 'mysecretpassword')
        self.postgres_port = os.getenv('POSTGRES_PORT', '5432')
        self.postgres_name = os.getenv('POSTGRES_DB', 'postgres')
        if os.getenv('SCYLLA_NODES'):
            self.scylla_nodes = os.getenv('SCYLLA_NODES').split(" ")

    def get_connector(self):
        """
        Returns the connector specified by the DATABASE_TYPE environment variable.
        :raises ValueError: if DATABASE_TYPE is not a valid database option
        :return: a PostgresConnector if DATABASE_TYPE is set to postgres,
        or a ScyllaConnector if DATABASE_TYPE is set to scylla
        """
        if self.db_type == 'postgres':
            return PostgresConnector(self.postgres_user, self.postgres_password, self.db_host, self.postgres_port, self.postgres_name)
        elif self.db_type == 'scylla':
            return ScyllaConnector(self.scylla_nodes)
        else:
            raise ValueError("Invalid database")


class ScyllaConnector:
    def __init__(self, nodes):
        """Establishes a connection to the ScyllaDB database, creates the "wdm" keyspace if it does not exist
        and creates or updates the users table.
        """
        while True:
            try:
                session = Cluster(contact_points=nodes).connect()
                break
            except Exception:
                sleep(1)
        session.execute("""
            CREATE KEYSPACE IF NOT EXISTS wdm
            WITH replication = { 'class': 'SimpleStrategy', 'replication_factor': '3' }
            """)
        session.default_consistency_level = ConsistencyLevel.QUORUM

        connection.setup(nodes, "wdm")
        sync_table(Payments)

    def pay(self, user_id, order_id, amount):
        """Pays the order
        :param user_id the id of the user
        :param order_id the id of the order
        :param the amount of the transaction
        :raise ValidationErrror if the order id is not valid
        :return creates the payment for the parameters used

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

        :param user_id: the id of the user
        :param order_id: the id of the order
        :raises ValueError: if there is no such user
        :return Payment status is False (cancel)
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



#I am not sure here about the endpoints

class PostgresConnector:
    def __init__(self, db_user, db_password, db_host, db_port, db_name):
        """Establishes a connection to the PostgreSQL database, and creates or updates the stock_item table.
        """
        self.engine = create_engine(f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}',
                                    convert_unicode=True)
        self.db_session = scoped_session(sessionmaker(autocommit=False,
                                                      autoflush=False,
                                                      bind=self.engine))
        Base.query = self.db_session.query_property()
        Base.metadata.create_all(bind=self.engine)


    def pay(self, user_id, order_id, amount):
        """Pays the order
        :param user_id the id of the user
        :param order_id the id of the order
        :param the amount of the transaction
        :raise ValidationErrror if the order id is not valid
        :return creates the payment for the parameters used
        """
        try:
            payment: Payment = self.db_session.query(Payment).filter_by(order_id=order_id, user_id=user_id).first()
            if payment is not None:  # payment exists in the database
                if payment.status is True:
                    abort(400, "the payment is already made")

            users_response = requests.post(f"http://{os.environ['USER_SERVICE_URL']}/users/credit/subtract/{user_id}/{amount}")
            if not users_response.ok:
                abort(400, "User service failure")

            if payment is not None:
                payment.status = True
                payment.amount = amount
            else:
                payment = Payment(user_id=user_id, order_id=order_id, status=True, amount=amount)
            self.db_session.add(payment)
            self.db_session.commit()
        except SQLAlchemyError:
            return abort(400, 'Error in the database')



    def cancel_pay(self ,user_id, order_id):
        """Cancels the payment from the database.

        :param user_id: the id of the user
        :param order_id: the id of the order
        :raises : error  if the payment does not exist/made and  if the userid and order id does not exist
        :return: sets the payment status as false (cancel)
        """
        try:
            payment: Payment = self.db_session.query(Payment).filter_by(order_id=order_id, user_id=user_id).first()
            if payment is None:
                abort(400, 'payment does not exist')
            if payment.status is False:
                abort(400, "the payment is not made")
            users_response = requests.post(f"http://{os.environ['USER_SERVICE_URL']}/users/credit/add/{user_id}/{payment.amount}")
            if not users_response.ok:
                abort(400, "User service failure")
            payment.status = False
            self.db_session.add(payment)
            self.db_session.commit()
        except SQLAlchemyError:
            return abort(400, 'Error in the database')



    def status(self, order_id):
        """Retrieves the payment from the database by its order_id.

        :param order_id: the id of the order
        :raises ValueError: if the order with order_id does not exist or if the format of the order_id is invalid
        :return: the payment with order_id order_id
        """
        try:
            payment: Payment = self.db_session.query(Payment).filter_by(order_id=order_id).first()
            if payment is None:
                abort(400, 'payment does not exist')
            else:
                return payment.status

        except SQLAlchemyError:
            return abort(400, 'Error in the database')



