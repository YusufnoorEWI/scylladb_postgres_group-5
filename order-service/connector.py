from cassandra.cluster import Cluster
from cassandra.cqlengine import connection, ValidationError
from cassandra.cqlengine.management import sync_table
from cassandra.cqlengine.query import QueryException

from .order_item import OrderItem


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
        sync_table(OrderItem)

    @staticmethod
    def create_order(user_id):
        """creates an order for the given user, and returns an order_id

        :param price: the user id
        :return: the id of the order
        """
        #BUG: check whether this user exist
        order = OrderItem.create(user_id=user_id, items_list=[],\
             paid=False, total_cost=0)
        return order.order_id

    @staticmethod
    def delete_order(order_id):
        '''
         deletes an order by ID

        '''
        try:
            order = OrderItem.get(order_id=order_id).delete()
        except QueryException:
            raise ValueError(f"User with id {order_id} not found")
        #BUG: not sure if it's the right method
        #order.delete()
        #return 

    @staticmethod
    def get_order(order_id):
        """Retrieves the item from the database by its id.

        :param item_id: the id of the item
        :raises ValueError: if the item with item_id does not exist or if the format of the item_id is invalid
        :return: the item with id item_id
        """
        try:
            order = OrderItem.get(order_id=order_id)
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
        order = self.get_order(order_id)
        order.items_list.append(item_id)
        #BUG: How to update the total cost
        #Could try to use stock service to get it
        order.total_cost += item_price 
        OrderItem.update(order)
        return order.items_list

    def remove_item(self, order_id, item_id, item_price):
        """Removes the given item from the given order

        :param item_id: the id of the item
        :param Order_id: the id of the order
        :raises AssertionError: if the item is not in the order
        :return: the list of the item in stock
        """
        order = self.get_order(order_id)
        try:
            order.items_list.remove(item_id)
        except ValueError:
            assert True, 'Item not in order'
        #BUG: How to update the total cost
        order.total_cost -= item_price
        assert order.total_cost < 0, 'Total cost < 0'
        OrderItem.update(order)
        return order.items_list
    
    def get_paid(self, order_id):
        order = self.get_order(order_id)
        return order.paid
    
    def get_items(self, order_id):
        order = self.get_order(order_id)
        return order.items_list

    def get_user_id(self, order_id):
        order = self.get_order(order_id)
        return order.user_id
    
    def get_total_cost(self, order_id):
        order = self.get_order(order_id)
        return order.total_cost
