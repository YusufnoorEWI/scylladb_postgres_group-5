import unittest
from decimal import Decimal
from test.endpoints import EndPoints as ep


class TestOrderSAGA(unittest.TestCase):

    def setUp(self):
        self.item_id = ep.stock_create(5.5).json()['item_id']
        self.item_id2 = ep.stock_create(1).json()['item_id']
        self.user_id = ep.users_create().json()['user_id']
        self.order_id = ep.orders_create(self.user_id).json()['order_id']

    def test_happy_flow(self):
        ep.stock_add(self.item_id, 10)
        ep.stock_add(self.item_id2, 10)
        ep.users_credit_add(self.user_id, 500)
        ep.orders_add_item(self.order_id, self.item_id)
        ep.orders_add_item(self.order_id, self.item_id2)

        response = ep.orders_checkout(self.order_id)

        item1_stock = int(ep.stock_find(self.item_id).json()['stock'])
        item2_stock = int(ep.stock_find(self.item_id2).json()['stock'])
        user_credit = Decimal(ep.users_find(self.user_id).json()['credit'])

        self.assertTrue(response.ok)
        self.assertEqual(item1_stock, 9)
        self.assertEqual(item2_stock, 9)
        self.assertEqual(user_credit, Decimal(493.5))

    def test_insufficient_credit(self):
        ep.stock_add(self.item_id, 10)
        ep.stock_add(self.item_id2, 10)
        ep.users_credit_add(self.user_id, 1)
        ep.orders_add_item(self.order_id, self.item_id)
        ep.orders_add_item(self.order_id, self.item_id2)

        response = ep.orders_checkout(self.order_id)

        item1_stock = int(ep.stock_find(self.item_id).json()['stock'])
        item2_stock = int(ep.stock_find(self.item_id2).json()['stock'])
        user_credit = Decimal(ep.users_find(self.user_id).json()['credit'])

        self.assertFalse(response.ok)
        self.assertEqual(item1_stock, 10)
        self.assertEqual(item2_stock, 10)
        self.assertEqual(user_credit, Decimal(1))

    def test_insufficient_stock(self):
        ep.stock_add(self.item_id, 10)
        ep.stock_add(self.item_id2, 0)
        ep.users_credit_add(self.user_id, 500)
        ep.orders_add_item(self.order_id, self.item_id)
        ep.orders_add_item(self.order_id, self.item_id2)

        response = ep.orders_checkout(self.order_id)

        item1_stock = int(ep.stock_find(self.item_id).json()['stock'])
        item2_stock = int(ep.stock_find(self.item_id2).json()['stock'])
        user_credit = Decimal(ep.users_find(self.user_id).json()['credit'])

        self.assertFalse(response.ok)
        self.assertEqual(item1_stock, 10)
        self.assertEqual(item2_stock, 0)
        self.assertEqual(user_credit, Decimal(500))

    def test_insufficient_stock2(self):
        ep.stock_add(self.item_id, 0)
        ep.stock_add(self.item_id2, 10)
        ep.users_credit_add(self.user_id, 500)
        ep.orders_add_item(self.order_id, self.item_id)
        ep.orders_add_item(self.order_id, self.item_id2)

        response = ep.orders_checkout(self.order_id)

        item1_stock = int(ep.stock_find(self.item_id).json()['stock'])
        item2_stock = int(ep.stock_find(self.item_id2).json()['stock'])
        user_credit = Decimal(ep.users_find(self.user_id).json()['credit'])

        self.assertFalse(response.ok)
        self.assertEqual(item1_stock, 0)
        self.assertEqual(item2_stock, 10)
        self.assertEqual(user_credit, Decimal(500))

    def test_insufficient_stock3(self):
        ep.stock_add(self.item_id, 10)
        ep.stock_add(self.item_id2, 1)
        ep.users_credit_add(self.user_id, 500)
        ep.orders_add_item(self.order_id, self.item_id)
        ep.orders_add_item(self.order_id, self.item_id2)
        ep.orders_add_item(self.order_id, self.item_id2)

        response = ep.orders_checkout(self.order_id)

        item1_stock = int(ep.stock_find(self.item_id).json()['stock'])
        item2_stock = int(ep.stock_find(self.item_id2).json()['stock'])
        user_credit = Decimal(ep.users_find(self.user_id).json()['credit'])

        self.assertFalse(response.ok)
        self.assertEqual(item1_stock, 10)
        self.assertEqual(item2_stock, 1)
        self.assertEqual(user_credit, Decimal(500))

    if __name__ == '__main__':
        unittest.main()
