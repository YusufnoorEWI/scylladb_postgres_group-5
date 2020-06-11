import unittest

from random import uniform
from test.endpoints import EndPoints as ep


class TestStockService(unittest.TestCase):
    user1 = {}
    order1 = {}
    item1 = {}
    price = -1
    balance_sufficient = -1
    balance_insufficient = -1

    def setUp(self) -> None:
        self.user1 = ep.users_create().json()
        self.user2 = ep.users_create().json()
        self.order1 = ep.orders_create(self.user1['user_id']).json()
        self.order2 = ep.orders_create(self.user2['user_id']).json()

        self.price = uniform(0, 100)
        self.balance_sufficient = self.price
        self.balance_insufficient = uniform(0, self.price - 1.0)

        self.item1 = ep.stock_create(self.price).json()
        ep.users_credit_add(self.user1['user_id'], self.balance_sufficient)
        ep.users_credit_add(self.user2['user_id'], self.balance_insufficient)

        ep.orders_add_item(self.order1['order_id'], self.item1['item_id'])
        ep.orders_add_item(self.order2['order_id'], self.item1['item_id'])

    def test_payment_sufficient_funds(self):
        status_before = ep.payment_status(self.order1['order_id'])

        self.assertFalse(status_before.ok)

        balance_before = ep.users_find(self.user1['user_id']).json()['credit']

        res = ep.payment_pay(self.user1['user_id'], self.order1['order_id'], self.price)

        status_after = ep.payment_status(self.order1['order_id'])
        balance_after = ep.users_find(self.user1['user_id']).json()['credit']

        self.assertTrue(res.ok)
        self.assertTrue(status_after.ok)
        self.assertEqual(balance_after + self.price, balance_before)
        self.assertEqual(status_after.json()['paid'], True)

    def test_payment_insufficient_funds(self):
        status_before = ep.payment_status(self.order2['order_id'])

        self.assertFalse(status_before.ok)

        balance_before = ep.users_find(self.user1['user_id']).json()['credit']

        res = ep.payment_pay(self.user2['user_id'], self.order2['order_id'], self.price)

        status_after = ep.payment_status(self.order1['order_id'])
        balance_after = ep.users_find(self.user1['user_id']).json()['credit']

        self.assertFalse(res.ok)
        self.assertFalse(status_after.ok)
        self.assertEqual(balance_before, balance_after)

    def test_payment_non_existing_user(self):
        status_before = ep.payment_status(self.order1['order_id'])

        self.assertFalse(status_before.ok)

        res = ep.payment_pay(self.order1['order_id'], self.order1['order_id'], self.price)

        status_after = ep.payment_status(self.order1['order_id'])

        self.assertFalse(res.ok)
        self.assertFalse(status_after.ok)





