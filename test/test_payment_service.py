import os

import requests
import unittest

from random import randint, uniform
from uuid import UUID

stock_host = os.getenv('PAYMENT_SERVICE', 'http://127.0.0.1:8080/')

def users_create():
    return requests.post(f'{user_host}users/create')


def users_remove(user_id):
    return requests.delete(f'{user_host}users/remove/{user_id}')


def users_find(user_id):
    return requests.get(f'{user_host}users/find/{user_id}')


def users_credit_add(user_id, amount):
    return requests.post(f'{user_host}users/credit/add/{user_id}/{amount}')

def orders_create(user_id):
    return requests.post(f'{order_host}orders/create/{user_id}')


def orders_remove(order_id):
    return requests.delete(f'{order_host}orders/remove/{order_id}')


def orders_find(order_id):
    return requests.get(f'{order_host}orders/find/{order_id}')


def payment_pay(user_id, order_id, amount):
    return requests.post(f'{stock_host}stock/item/create/{price}')


def payment_cancel_pay(user_id, order_id):
    return requests.get(f'{stock_host}stock/find/{item_id}')


def payment_status(order_id):
    return requests.post(f'{stock_host}stock/add/{item_id}/{amount}')


class TestStockService(unittest.TestCase):
    item_id = ''
    price = -1
    stock_item = {}
    old_amount = -1
    res = {}
    rand_int_pos = 0
    rand_int_neg = 0
    rand_float_pos = 0.0
    rand_float_neg = 0.0

    def setUp(self) -> None:
        self.price = uniform(0, 100)
        self.item_id = stock_create(self.price).json()['item_id']
        self.res = stock_find(self.item_id)
        self.stock_item = self.res.json()
        self.old_amount = self.stock_item['stock']
        self.rand_int_pos = randint(0, 100)
        self.rand_int_neg = randint(-100, -1)
        self.rand_float_pos = uniform(0, 100)
        self.rand_float_neg = uniform(-100, -1)

    def test_stock_create(self):
        price = uniform(0, 100)
        res = stock_create(price)
        item_id = res.json()['item_id']
        try:
            uuid_obj = UUID(item_id, version=4)
        except ValueError:
            return False

        self.assertTrue(res.ok)
        self.assertEqual(str(uuid_obj), item_id)

    def test_stock_find(self):

        self.assertTrue(self.res.ok)
        self.assertEqual(self.stock_item['item_id'], self.item_id)
        self.assertEqual(self.stock_item['price'], self.price)
        self.assertEqual(self.stock_item['stock'], 0.0)

    def test_stock_add_positive_integer(self):

        res2 = stock_add(self.stock_item['item_id'], self.rand_int_pos)
        new_amount = self.old_amount + self.rand_int_pos

        self.assertTrue(res2.ok)
        self.assertEqual(res2.json(), new_amount)

    def test_stock_add_positive_float(self):
        res2 = stock_add(self.stock_item['item_id'], self.rand_float_pos)
        new_amount = stock_find(self.item_id).json()['stock']

        self.assertFalse(res2.ok)
        self.assertEqual(new_amount, self.old_amount)

    def test_stock_add_negative_integer(self):
        res2 = stock_add(self.stock_item['item_id'], self.rand_int_neg)
        new_amount = stock_find(self.item_id).json()['stock']

        self.assertFalse(res2.ok)
        self.assertEqual(new_amount, self.old_amount)

    def test_stock_add_negative_float(self):
        res2 = stock_add(self.stock_item['item_id'], self.rand_float_neg)
        new_amount = stock_find(self.item_id).json()['stock']

        self.assertFalse(res2.ok)
        self.assertEqual(new_amount, self.old_amount)

    def test_stock_subtract_positive_integer(self):
        res2 = stock_add(self.stock_item['item_id'], self.rand_int_pos)

        self.assertTrue(res2.ok)

        res3 = stock_subtract(self.stock_item['item_id'], self.rand_int_pos)

        self.assertTrue(res3.ok)
        self.assertEqual(res3.json(), self.old_amount)

    def test_stock_subtract_positive_float(self):
        res2 = stock_add(self.stock_item['item_id'], self.rand_float_pos)
        new_amount = stock_find(self.item_id).json()['stock']

        self.assertFalse(res2.ok)
        self.assertEqual(new_amount, self.old_amount)

    def test_stock_subtract_negative_integer(self):
        res2 = stock_add(self.stock_item['item_id'], self.rand_int_neg)
        new_amount = stock_find(self.item_id).json()['stock']

        self.assertFalse(res2.ok)
        self.assertEqual(new_amount, self.old_amount)

    def test_stock_subtract_negative_float(self):
        res2 = stock_add(self.stock_item['item_id'], self.rand_float_neg)
        new_amount = stock_find(self.item_id).json()['stock']

        self.assertFalse(res2.ok)
        self.assertEqual(new_amount, self.old_amount)

    def test_stock_subtract_positive_integer_too_much(self):
        res2 = stock_add(self.stock_item['item_id'], self.rand_int_pos)

        self.assertTrue(res2.ok)

        res3 = stock_subtract(self.stock_item['item_id'], self.rand_int_pos + 1)

        self.assertFalse(res3.ok)
        self.assertEqual(stock_find(self.item_id).json()['stock'], self.rand_int_pos)

    if __name__ == '__main__':
        unittest.main()

