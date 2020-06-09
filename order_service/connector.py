import os
from time import sleep

from cassandra.cluster import Cluster
from cassandra.cqlengine import connection, ValidationError
from cassandra.cqlengine.management import sync_table
from cassandra.cqlengine.query import QueryException
from sqlalchemy import create_engine
from sqlalchemy.exc import DataError
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm.exc import NoResultFound

from order_service.scylla_order_item import ScyllaOrderItem
from order_service.scylla_order import ScyllaOrder
from order_service.postgres_order_item import Base_order_item, PostgresOrderItem
from order_service.postgres_order import PostgresOrder, Base_order


class ConnectorFactory:
    def __init__(self):
        """Initializes a database connector factory with parameters set by the environment variables."""
        self.db_host = os.getenv("DB_HOST", "127.0.0.1")
        self.db_type = os.getenv("DATABASE_TYPE", 'postgres')
        self.postgres_user = os.getenv('POSTGRES_USER', 'postgres')
        self.postgres_password = os.getenv('POSTGRES_PASSWORD', 'mysecretpassword')
        self.postgres_port = os.getenv('POSTGRES_PORT', '5432')
        self.postgres_name = os.getenv('POSTGRES_DB', 'postgres')

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
            return ScyllaConnector(self.db_host)
        else:
            raise ValueError("Invalid database")


class ScyllaConnector:
    def __init__(self, host):
        """Establishes a connection to the ScyllaDB database, creates the "wdm" keyspace if it does not exist
        and creates or updates the stock_item table.
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
        sync_table(ScyllaOrderItem)
        sync_table(ScyllaOrder)
        # Also sync the order table, retrieve everything.

    @staticmethod
    def create_order(user_id):
        """creates an order for the given user, and returns an order_id

        :param user_id: the user id
        :return: the id of the order
        """
        order = ScyllaOrder.create(user_id=user_id, paid=False)
        return order.order_id

    @staticmethod
    def delete_order(order_id):
        """
         deletes an order by ID
        :param order_id: id of order to be deleted
        """
        try:
            ScyllaOrder.get(order_id=order_id).delete()
        except QueryException:
            raise ValueError(f"Order with id {order_id} not found")

    @staticmethod
    def get_order(order_id):
        """Retrieves the order from the database by its id.

        :param order_id: the id of the order
        :raises ValueError: if the order with order_id does not exist or if the format of the order_id is invalid
        :return: the order with id order_id
        """
        try:
            order = ScyllaOrder.get(order_id=order_id)
        except QueryException:
            raise ValueError(f"Order with id {order_id} not found")
        except ValidationError:
            raise ValueError(f"Order id {order_id} is not a valid id")

        return order

    @staticmethod
    def add_item(order_id, item_id, item_price):
        """Adds a given item in the order given


        :param order_id: the id of the order
        :param item_id: the id of the item
        :param item_price: the price of the item
        :return: the list of item in order
        """
        if item_price < 0:
            raise ValueError(f"Item price {item_price} is not valid")
        try:
            item = ScyllaOrderItem.get(item_id=item_id, order_id=order_id)
            item.item_num += 1
            ScyllaOrderItem.update(item)
        except QueryException:
            item = ScyllaOrderItem.create(item_id=item_id, order_id=order_id,
                                          price=item_price, item_num=1)
            ScyllaOrderItem.update(item)
        return item.item_num

    @staticmethod
    def remove_item(order_id, item_id):
        """Removes the given item from the given order

        :param item_id: the id of the item
        :param order_id: the id of the order
        :raises AssertionError: if the item is not in the order
        :return: the number of the item in stock
        """
        try:
            item = ScyllaOrderItem.get(item_id=item_id, order_id=order_id)
            item.item_num -= 1
            ScyllaOrderItem.update(item)
        except QueryException:
            raise ValueError(f"Order {order_id} does not contain item {item_id}")
        tmp = item.item_num
        if item.item_num == 0:
            ScyllaOrderItem.get(item_id=item_id, order_id=order_id).delete()
        return tmp

    @staticmethod
    def get_order_info(order_id):
        try:
            order = ScyllaOrder.get(order_id=order_id)
        except QueryException:
            raise ValueError("Order with id not found")
        except ValidationError:
            raise ValueError("Invalid id provided")

        try:
            items = ScyllaOrderItem.objects.filter(order_id=order_id).all()
            items = items[:]
            total_cost = 0
            item_list = []
            for item in items:
                total_cost += item.item_num * item.price
                item_list.extend([item.item_id] * item.item_num)
        except QueryException:
            # When there's no item in the order
            item_list = []
            total_cost = 0
        return order.paid, item_list, order.user_id, total_cost

    @staticmethod
    def get_order_ids_by_user(user_id):
        try:
            orders = ScyllaOrder.objects.allow_filtering().filter(user_id=user_id).all()
            order_ids = []
            for order in list(orders):
                order_ids.append(order.order_id)
        except QueryException:
            raise ValueError("No orders for user")
        return order_ids

    @staticmethod
    def find_item(order_id, item_id):
        try:
            item = ScyllaOrderItem.get(item_id=item_id, order_id=order_id)
            return True, item.price
        except QueryException:
            return False, None
        except ValidationError:
            raise ValueError("Not a valid UUID")

    @staticmethod
    def get_item_num(order_id, item_id):
        try:
            item = ScyllaOrderItem.get(item_id=item_id, order_id=order_id)
            return item.item_num
        except QueryException:
            raise ValueError(f"Order {order_id} does not contain item {item_id}")

    def set_paid(self, order_id):
        order = self.get_order(order_id)
        order.paid = True
        ScyllaOrder.update(order)
        return True


class PostgresConnector:
    def __init__(self, db_user, db_password, db_host, db_port, db_name):
        """Establishes a connection to the PostgreSQL database, and creates or updates the order_item and order table.
        """
        self.engine = create_engine(f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}',
                                    convert_unicode=True)
        self.db_session = scoped_session(sessionmaker(autocommit=False,
                                                      autoflush=False,
                                                      bind=self.engine))
        Base_order.query = self.db_session.query_property()
        Base_order.metadata.create_all(bind=self.engine)
        Base_order_item.query = self.db_session.query_property()
        Base_order_item.metadata.create_all(bind=self.engine)

    def create_order(self, user_id):
        """creates an order for the given user, and returns an order_id

        :param user_id: the user id
        :return: the id of the order
        """
        order = PostgresOrder(user_id=user_id)
        self.db_session.add(order)
        self.db_session.commit()
        return order.order_id

    def create_order_item(self, order_id, item_id, price, item_num):
        """creates an order for the given user, and returns an order_id

        :param order_id: id of the order
        :param item_id: id of the item
        :param price: the user id
        :param item_num: amount of items
        :return: the id of the order
        """
        order_item = PostgresOrderItem(order_id, item_id, price, item_num)
        self.db_session.add(order_item)
        self.db_session.commit()
        return order_item.order_id

    def get_order(self, order_id):
        """Retrieves the order from the database by its id.

        :param order_id: the id of the order
        :raises ValueError: if the order with order_id does not exist or if the format of the order_id is invalid
        :return: the order with id order_id
        """
        try:
            order = self.db_session.query(PostgresOrder).filter_by(order_id=order_id).one()
        except NoResultFound:
            raise ValueError(f"Order with id {order_id} not found")
        except DataError:
            raise ValueError(f"Order id {order_id} is not a valid id")

        return order

    def get_order_item(self, order_id, item_id):
        """Retrieves the order item from the database by its order_id and item_id

        :param order_id: the id of the order
        :param item_id: the id of the item
        :return: the order item with ids order_id and item_id

        """
        try:
            item = self.db_session.query(PostgresOrderItem) \
                .filter_by(order_id=order_id, item_id=item_id).one()
        except DataError:
            raise ValueError(f"Item {item_id} in order {order_id} is not a valid id")
        except NoResultFound:
            raise ValueError(f"Item {item_id} in order {order_id} not found")
        except ValidationError:
            raise ValueError("Unknown exception (validation error)")
        return item

    def delete_order(self, order_id):
        """Deletes an order by ID

        :param order_id: the id of the order to delete
        """
        try:
            order = self.get_order(order_id=order_id)
            self.db_session.delete(order)
            self.db_session.commit()
        except ValueError | QueryException:
            raise ValueError(f"Order with id {order_id} not found")

    def add_item(self, item_id, order_id, item_price):
        """Adds a given item in the order given


        :param item_id: the id of the item
        :param order_id: the id of the order
        :param item_price: price of the item
        :return: the list of item in order
        """

        if item_price < 0:
            raise ValueError(f"Item price {item_price} is not valid")
        try:
            item = self.get_order_item(order_id, item_id)
            item.item_num += 1
            self.db_session.commit()
        # NOT SURE IF THIS WORKS
        except ValueError:
            self.create_order_item(order_id, item_id, item_price, 1)
            item = self.get_order_item(order_id, item_id)
            self.db_session.commit()
        return item.item_num

    def remove_item(self, order_id, item_id):
        """Removes the given item from the given order

        :param item_id: the id of the item
        :param order_id: the id of the order
        :raises AssertionError: if the item is not in the order
        :return: the list of the item in stock
        """
        try:
            item = self.get_order_item(order_id, item_id)
            item.item_num -= 1
            self.db_session.commit()
        except ValueError:
            raise ValueError(f"Order {order_id} does not contain item {item_id}")
        tmp = item.item_num
        if item.item_num == 0:
            self.db_session.delete(item)
            self.db_session.commit()
        return tmp

    def get_order_info(self, order_id):
        """
        Get order information

        :param order_id: id of the order
        :return: order information (paid, items, user_id, total_cost)
        """
        order = self.get_order(order_id)
        items = self.db_session.query(PostgresOrderItem) \
            .filter_by(order_id=order_id).all()
        items = items[:]
        total_cost = 0
        item_list = []
        for item in items:
            total_cost += item.item_num * item.price
            item_list.extend([str(item.item_id)] * item.item_num)
        return order.paid, item_list, order.user_id, total_cost

    def get_order_ids_by_user(self, user_id):
        try:
            orders = self.db_session.query(PostgresOrder).filter_by(user_id=user_id).all()
            order_ids = []
            for order in list(orders):
                order_ids.append(order.order_id)
        except QueryException:
            raise ValueError("No orders for user")
        return order_ids
            
    def find_item(self, order_id, item_id):
        """
        Check whether an item is present in the order

        :param order_id: id of order to look in
        :param item_id: id of item to look for
        :return: Boolean indicating whether item was found, price if found
        """
        try:
            item = self.db_session.query(PostgresOrderItem) \
                .filter_by(order_id=order_id, item_id=item_id).one()
            if item is None:
                return False, None
            return True, item.price
        except NoResultFound:
            return False, None
        except DataError:
            raise ValueError("Not legal item id")

    def get_item_num(self, order_id, item_id):
        """
        Get the amount of item with item_id in order with order_id

        :param order_id: id of order to look in
        :param item_id: id of item to count
        :return: amount of occurrences of item with item_id in order with order_id
        """
        try:
            item = self.db_session.query(PostgresOrderItem) \
                .filter_by(order_id=order_id, item_id=item_id).one()
            return item.item_num
        except NoResultFound:
            raise ValueError(f"Order {order_id} does not contain item {item_id}")

    def set_paid(self, order_id):
        """
        Set paid boolean of order

        :param order_id: id of order to adjust
        :return: True if success.
        """
        order = self.get_order(order_id)
        order.paid = True
        self.db_session.commit()
        return True
