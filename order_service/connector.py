import sys
import os

from cassandra.cluster import Cluster
from cassandra.cqlengine import connection, ValidationError
from cassandra.cqlengine.management import sync_table
from cassandra.cqlengine.query import QueryException

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from order_service.order_item import OrderItem
from order_service.order import Order


class ScyllaConnector:
    def __init__(self):
        """Establishes a connection to the ScyllaDB database, creates the "wdm" keyspace if it does not exist
        and creates or updates the stock_item table.
        """
        session = Cluster(['localhost']).connect()#
        session.execute("""
            CREATE KEYSPACE IF NOT EXISTS wdm
            WITH replication = { 'class': 'SimpleStrategy', 'replication_factor': '2' }
            """)

        connection.setup(['localhost'], "wdm")
        sync_table(OrderItem)
        sync_table(Order)
        #Also sync the order table, retrieve everything.

    @staticmethod
    def create_order(user_id):
        """creates an order for the given user, and returns an order_id

        :param price: the user id
        :return: the id of the order
        """
        order = Order.create(user_id=user_id, paid=False)
        return order.order_id

    @staticmethod
    def delete_order(order_id):
        '''
         deletes an order by ID

        '''
        try:
            Order.get(order_id=order_id).delete()
            # BUG: should I delete it?
            # OrderItem.get(order_id=order_id).delete()
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
            order = Order.get(order_id=order_id)
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
            item = OrderItem.get(item_id=item_id, order_id=order_id)
            item.item_num += 1
            OrderItem.update(item)
        except QueryException:
            item = OrderItem.create(item_id=item_id, order_id=order_id, \
                price=item_price, item_num=1)
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
            item = OrderItem.get(item_id=item_id, order_id=order_id)
            item.item_num -= 1
            OrderItem.update(item)
        except QueryException:
            raise ValueError(f"Order {order_id} does not contain item {item_id}")
        tmp = item.item_num
        if item_price == 0:
            OrderItem.get(item_id=item_id, order_id=order_id).delete()
        return tmp
    
    def get_order_info(self, order_id):
        order = Order.get(order_id=order_id)
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
            item = OrderItem.get(item_id=item_id, order_id=order_id)
            return True, item.price
        except QueryException:
            return False, None
    
    def get_item_num(self, order_id, item_id):
        try:
            item = OrderItem.get(item_id=item_id, order_id=order_id)
            return item.item_num
        except QueryException:
            raise ValueError(f"Order {order_id} does not contain item {item_id}")

    def set_paid(self, order_id):
        order = self.get_order(order_id)
        order.paid = True
        Order.update(order)
        return True
