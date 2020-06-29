import os
from time import sleep

from cassandra import ConsistencyLevel
from cassandra.cluster import Cluster
from cassandra.cqlengine import connection, ValidationError
from cassandra.cqlengine.management import sync_table
from cassandra.cqlengine.query import QueryException
from sqlalchemy import create_engine
from sqlalchemy.exc import DataError
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm.exc import NoResultFound

from stock_service.scylla_stock_item import ScyllaStockItem
from stock_service.postgres_stock_item import Base, PostgresStockItem


class ConnectorFactory:
    def __init__(self):
        """Initializes a database connector factory with parameters set by the environment variables."""
        self.db_host = os.getenv("DB_HOST")
        self.db_type = os.getenv("DATABASE_TYPE")
        self.postgres_user = os.getenv('POSTGRES_USER')
        self.postgres_password = os.getenv('POSTGRES_PASSWORD')
        self.postgres_port = os.getenv('POSTGRES_PORT')
        self.postgres_name = os.getenv('POSTGRES_DB')
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
            return PostgresConnector(self.postgres_user, self.postgres_password, self.db_host, self.postgres_port,
                                     self.postgres_name)
        elif self.db_type == 'scylla':
            return ScyllaConnector(self.scylla_nodes)
        else:
            raise ValueError("Invalid database")


class ScyllaConnector:
    def __init__(self, nodes):
        """Establishes a connection to the ScyllaDB database, creates the "wdm" keyspace if it does not exist
        and creates or updates the stock_item table.
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
        sync_table(ScyllaStockItem)

    @staticmethod
    def create_item(price):
        """Creates an item with the specified price.

        :param price: the price of the item
        :return: the id of the created item
        """
        item = ScyllaStockItem.create(price=price, in_stock=0)
        return item.id

    @staticmethod
    def get_item(item_id):
        """Retrieves the item from the database by its id.

        :param item_id: the id of the item
        :raises ValueError: if the item with item_id does not exist or if the format of the item_id is invalid
        :return: the item with id item_id
        """
        try:
            item = ScyllaStockItem.get(id=item_id)
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
        ScyllaStockItem.update(item)
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

        ScyllaStockItem.update(item)
        return item.in_stock


class PostgresConnector:
    def __init__(self, db_user, db_password, db_host, db_port, db_name):
        """Establishes a connection to the PostgreSQL database, and creates or updates the stock_item table.
        """
        self.engine = create_engine(f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}',
                                    convert_unicode=True, pool_size=10, pool_timeout=3)
        self.db_session = scoped_session(sessionmaker(autocommit=False,
                                                      autoflush=False,
                                                      bind=self.engine))
        Base.query = self.db_session.query_property()
        Base.metadata.create_all(bind=self.engine)

    def create_item(self, price):
        """Creates an item with the specified price.

        :param price: the price of the item
        :return: the id of the created item
        """
        item = PostgresStockItem(price=price, in_stock=0)
        self.db_session.add(item)
        self.db_session.commit()
        return str(item.id)

    def get_item(self, item_id):
        """Retrieves the item from the database by its id.

        :param item_id: the id of the item
        :raises ValueError: if the item with item_id does not exist or if the format of the item_id is invalid
        :return: the item with id item_id
        """
        try:
            item = self.db_session.query(PostgresStockItem).filter_by(id=item_id).one()
        except NoResultFound:
            raise ValueError(f"Item with id {item_id} not found")
        except DataError:
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
        self.db_session.commit()
        return item.in_stock

    def subtract_amount(self, item_id, number):
        """Subtracts the given number from the item count.

        :param item_id: the id of the item
        :param number: the number to subtract from stock
        :raises AssertionError: if the item count after subtraction is negative
        :return: the number of the item in stock
        """
        item = self.get_item(item_id)

        assert item.in_stock - number >= 0, 'Item count cannot be negative'

        item.in_stock = item.in_stock - number
        self.db_session.commit()
        return item.in_stock
