from cassandra import ConsistencyLevel
from cassandra.cluster import Cluster
from cassandra.cqlengine import connection, ValidationError
from cassandra.cqlengine.management import sync_table
from cassandra.cqlengine.query import QueryException
from time import sleep

from sqlalchemy import create_engine
from sqlalchemy.exc import DataError
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm.exc import NoResultFound


from users_service.scylla_user import ScyllaUser
from users_service.postgres_user import Base, PostgresUser
import os


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
        sync_table(ScyllaUser)

    @staticmethod
    def create():
        """Creates a user with zero initial credit.

        :return: the id of the created user
        """
        user = ScyllaUser.create(credit=0.0)
        return user.id

    @staticmethod
    def remove(user_id):
        """Removes a user with the given user id.

        :raises ValueError: if there is no such user
        """
        try:
            ScyllaUser.get(id=user_id).delete()
        except QueryException:
            raise ValueError(f"User with id {user_id} not found")

    @staticmethod
    def get_user(user_id):
        """Retrieves the user from the database by its id.

        :param user_id: the id of the user
        :raises ValueError: if the user with user_id does not exist or if the format of the user_id is invalid
        :return: the user with id user_id
        """
        try:
            user = ScyllaUser.get(id=user_id)
        except QueryException:
            raise ValueError(f"User with id {user_id} not found")
        except ValidationError:
            raise ValueError(f"User id {user_id} is not a valid id")
        return user

    def add_amount(self, user_id, number):
        """Adds the given number to the user's credit.

        :param user_id: the id of the user
        :param number: the number to add to credit
        :return: the total credit
        """
        user = self.get_user(user_id)
        user.credit = user.credit + number
        ScyllaUser.update(user)
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
        assert user.credit >= 0.0, 'User credit cannot be negative'

        ScyllaUser.update(user)
        return user.credit


class PostgresConnector:
    def __init__(self, db_user, db_password, db_host, db_port, db_name):
        """Establishes a connection to the PostgreSQL database, and creates or updates the user table.
        """
        self.engine = create_engine(f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}',
                                    convert_unicode=True, pool_timeout=3)
        self.db_session = scoped_session(sessionmaker(bind=self.engine))
        Base.query = self.db_session.query_property()
        Base.metadata.create_all(bind=self.engine)
        Base.metadata.query = self.db_session.query_property()
        PostgresUser.metadata.create_all(bind=self.engine)
        PostgresUser.metadata.query = self.db_session.query_property()

    def create(self):
        """Creates a user with zero initial credit.

        :return: the id of the created user
        """
        session = self.db_session()
        try:
            item = PostgresUser(credit=0.0)
            session.add(item)
            session.commit()
            return str(item.id)
        except Exception:
            raise Exception
        finally:
            session.close()

    def get_user(self, user_id):
        """Retrieves the user from the database by its id.

        :param user_id: the id of the user
        :raises ValueError: if the user with user_id does not exist or if the format of the user_id is invalid
        :return: the user with id user_id
        """
        session = self.db_session()
        try:
            return session.query(PostgresUser).filter_by(id=user_id).one()
        except NoResultFound:
            raise ValueError(f"User with id {user_id} not found")
        except DataError:
            raise ValueError(f"User id {user_id} is not a valid id")
        finally:
            session.close()

    def remove(self, user_id):
        """Removes a user with the given user id.

        :raises ValueError: if there is no such user
        """
        session = self.db_session()
        try:
            user = session.query(PostgresUser).filter_by(id=user_id).one()
            session.delete(user)
            session.commit()
            return True
        except Exception:
            raise Exception
        finally:
            session.close()

    def add_amount(self, user_id, number):
        """Adds the given number to the user's credit.

        :param user_id: the id of the user
        :param number: the number to add to credit
        :return: the total credit
        """
        session = self.db_session()
        try:
            user = session.query(PostgresUser).filter_by(id=user_id).one()
            user.credit += number
            session.commit()
            return user.credit
        except Exception:
            raise Exception
        finally:
            session.close()

    def subtract_amount(self, user_id, number):
        """Subtracts the given number from the user's credit.

        :param user_id: the id of the user
        :param number: the number to subtract from credit
        :raises AssertionError: if the user credit after subtraction is negative
        :return: the remaining credit
        """
        session = self.db_session()
        try:
            user = session.query(PostgresUser).filter_by(id=user_id).one()
            assert user.credit - number >= 0
            user.credit -= number
            session.commit()
            return user.credit
        except Exception as e:
            raise e
        finally:
            session.close()
