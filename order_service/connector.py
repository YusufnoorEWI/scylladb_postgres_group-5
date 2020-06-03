import sys
import os

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
from order_service.postgress_order_item import Base_order_item, PostgresOrderItem
from order_service.postgress_order import PostgresOrder, Base_order




class ConnectorFactory:
    def __init__(self):
        """Initializes a database connector factory with parameters set by the environment variables."""
        self.db_host = os.getenv("DB_HOST", "127.0.0.1")
        self.db_type = os.getenv("DATABASE_TYPE",'postgres')
        self.postgres_user = os.getenv('POSTGRES_USER', 'postgres')
        self.postgres_password = os.getenv('POSTGRES_PASSWORD','mysecretpassword')
        self.postgres_port = os.getenv('POSTGRES_PORT', '5432')
        self.postgres_name = os.getenv('POSTGRES_DB','postgres')

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
            return ScyllaConnector(self.db_host)
        else:
            raise ValueError("Invalid database")

class ScyllaConnector:
    def __init__(self, host):
        """Establishes a connection to the ScyllaDB database, creates the "wdm" keyspace if it does not exist
        and creates or updates the stock_item table.
        """
        session = Cluster([host]).connect()#
        session.execute("""
            CREATE KEYSPACE IF NOT EXISTS wdm
            WITH replication = { 'class': 'SimpleStrategy', 'replication_factor': '2' }
            """)
        connection.setup([host], "wdm")
        sync_table(ScyllaOrderItem)
        sync_table(ScyllaOrder)
        #Also sync the order table, retrieve everything.

    @staticmethod
    def create_order(user_id):
        """creates an order for the given user, and returns an order_id

        :param price: the user id
        :return: the id of the order
        """
        order = ScyllaOrder.create(user_id=user_id, paid=False)
        return order.order_id

    @staticmethod
    def delete_order(order_id):
        '''
         deletes an order by ID

        '''
        try:
            ScyllaOrder.get(order_id=order_id).delete()
        except QueryException:
            raise ValueError(f"Order with id {order_id} not found") 

    @staticmethod
    def get_order(order_id):
        """Retrieves the item from the database by its id.

        :param item_id: the id of the item
        :raises ValueError: if the item with item_id does not exist or if the format of the item_id is invalid
        :return: the item with id item_id
        """
        try:
            order = ScyllaOrder.get(order_id=order_id)
        except QueryException:
            raise ValueError(f"Order with id {order_id} not found")
        except ValidationError:
            raise ValueError(f"Order id {order_id} is not a valid id")

        return order

    def add_item(self, item_id, order_id, item_price):
        """Adds a given item in the order given


        :param item_id: the id of the item
        :param order_id: the id of the order
        :return: the list of item in order
        """
        if item_price < 0:
            raise ValueError(f"Item price {item_price} is not valid")
        try:
            item = ScyllaOrderItem.get(item_id=item_id, order_id=order_id)
            item.item_num += 1
            ScyllaOrderItem.update(item)
        except QueryException:
            item = ScyllaOrderItem.create(item_id=item_id, order_id=order_id, \
                price=item_price, item_num=1)
        return item.item_num

    def remove_item(self, order_id, item_id, item_price):
        """Removes the given item from the given order

        :param item_id: the id of the item
        :param Order_id: the id of the order
        :raises AssertionError: if the item is not in the order
        :return: the number of the item in stock
        """
        if item_price < 0:
            raise ValueError(f"Item price {item_price} is not valid")
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
    
    def get_order_info(self, order_id):
        order = ScyllaOrder.get(order_id=order_id)
        try:
            items = OrderItem.get(order_id=order_id)
            items = items[:]
            total_cost = 0
            item_list = []
            for item in items:
                total_cost += item.item_num * item.price
                item_list.append(item.item_id)
        except:
            # When there's no item in the order
            item_list = []
            total_cost = 0
        return order.paid, item_list, order.user_id, total_cost
    
    def find_item(self, order_id, item_id):
        try:
            item = ScyllaOrderItem.get(item_id=item_id, order_id=order_id)
            return True, item.price
        except QueryException:
            return False, None
    
    def get_item_num(self, order_id, item_id):
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
        """Establishes a connection to the PostgreSQL database, and creates or updates the stock_item table.
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

        :param price: the user id
        :return: the id of the order
        """
        order = PostgresOrder(user_id=user_id)
        self.db_session.add(order)
        self.db_session.commit()
        return str(order.order_id)
    
    def create_order_item(self, order_id, item_id, price, item_num):
        """creates an order for the given user, and returns an order_id

        :param price: the user id
        :return: the id of the order
        """
        item = PostgresOrderItem(order_id, item_id, price, item_num)
        self.db_session.add(item)
        self.db_session.commit()
        return str(item.order_id)

    def get_order(self, order_id):
        """Retrieves the item from the database by its id.

        :param item_id: the id of the item
        :raises ValueError: if the item with item_id does not exist or if the format of the item_id is invalid
        :return: the item with id item_id
        """
        try:
            order = self.db_session.query(PostgresOrder).filter_by(order_id=order_id).one()
        except NoResultFound:
            raise ValueError(f"Order with id {order_id} not found")
        except DataError:
            raise ValueError(f"Order id {order_id} is not a valid id")

        return order
    
    def get_order_item(self, order_id, item_id):
        try:
            item = self.db_session.query(PostgresOrderItem)\
                .filter_by(order_id=order_id, item_id=item_id).one()
        except DataError:
            raise ValueError(f"Item {item_id} in order {order_id} is not a valid id")
        except:
            raise ValueError(f"Item {item_id} in order {order_id} not found")
        return item

    def delete_order(self, order_id):
        '''
         deletes an order by ID

        '''
        try:
            order = self.get_order(order_id=order_id)
            self.db_session.delete(order)
            self.db_session.commit()
        except QueryException:
            raise ValueError(f"Order with id {order_id} not found")

    
    def add_item(self, item_id, order_id, item_price):
        """Adds a given item in the order given


        :param item_id: the id of the item
        :param order_id: the id of the order
        :return: the list of item in order
        """
        
        if item_price < 0:
            raise ValueError(f"Item price {item_price} is not valid")
        try:
            item = self.get_order_item(order_id, item_id)
            item.item_num += 1
            self.db_session.commit()
        except:
            item_id = self.create_order_item(order_id, item_id, item_price, 1)
            item = self.get_order_item(order_id, item_id)
            self.db_session.commit()
        return item.item_num
    
    def remove_item(self, order_id, item_id, item_price):
        """Removes the given item from the given order

        :param item_id: the id of the item
        :param Order_id: the id of the order
        :raises AssertionError: if the item is not in the order
        :return: the list of the item in stock
        """
        if item_price < 0:
            raise ValueError(f"Item price {item_price} is not valid")
        try:
            item = self.get_order_item(order_id, item_id)
            item.item_num -= 1
            self.db_session.commit()
        except QueryException:
            raise ValueError(f"Order {order_id} does not contain item {item_id}")
        tmp = item.item_num
        if item_price == 0:
            self.db_session.delete(item)
            self.db_session.commit()
        return tmp
    
    def get_order_info(self, order_id):
        order = self.get_order(order_id)
        items = self.db_session.query(PostgresOrderItem)\
                .filter_by(order_id=order_id).all()
        items = items[:]
        total_cost = 0
        item_list = []
        for item in items:
            total_cost += item.item_num * item.price
            item_list.extend([item.item_id] * item.item_num)
        return order.paid, item_list, order.user_id, total_cost
    
    def find_item(self, order_id, item_id):
        try:
            item = self.get_order_item(order_id, item_id)
            if item == None:
                return False, None
            return True, item.price
        except:
            return False, None
    
    def get_item_num(self, order_id, item_id):
        try:
            item = self.get_order_item(order_id, item_id)
            return item.item_num
        except QueryException:
            raise ValueError(f"Order {order_id} does not contain item {item_id}")

    def set_paid(self, order_id):
        order = self.get_order(order_id)
        order.paid = True
        self.db_session.commit()
        return True