import os
from decimal import Decimal

import requests
import unittest

from random import randint, uniform
from uuid import UUID

stock_host = os.getenv('STOCK_SERVICE', 'http://127.0.0.1:8080/')


def stock_create(price):
    return requests.post(f'{stock_host}stock/item/create/{price}')


def stock_find(item_id):
    return requests.get(f'{stock_host}stock/find/{item_id}')


def stock_add(item_id, amount):
    return requests.post(f'{stock_host}stock/add/{item_id}/{amount}')


def stock_subtract(item_id, amount):
    return requests.post(f'{stock_host}stock/subtract/{item_id}/{amount}')


class TestStockService(unittest.TestCase):
    item_id = ''
    price = -1
    stock_item = {}
    old_amount = -1
    res = {}

    def setUp(self) -> None:
        self.price = uniform(0, 100)
        self.item_id = stock_create(self.price).json()['item_id']
        self.res = stock_find(self.item_id)
        self.stock_item = self.res.json()
        self.old_amount = self.stock_item['stock']

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
        amount = randint(0, 100)

        res2 = stock_add(self.stock_item['item_id'], amount)
        new_amount = self.old_amount + amount

        self.assertTrue(res2.ok)
        self.assertEqual(res2.json(), new_amount)

    def test_stock_add_positive_float(self):
        amount = uniform(0, 100)

        res2 = stock_add(self.stock_item['item_id'], amount)
        new_amount = stock_find(self.item_id).json()['stock']

        self.assertFalse(res2.ok)
        self.assertEqual(new_amount, self.old_amount)

    def test_stock_add_negative_integer(self):
        amount = randint(-100, -1)

        res2 = stock_add(self.stock_item['item_id'], amount)
        new_amount = stock_find(self.item_id).json()['stock']

        self.assertFalse(res2.ok)
        self.assertEqual(new_amount, self.old_amount)

    def test_stock_add_negative_float(self):
        amount = uniform(-100, -1)

        res2 = stock_add(self.stock_item['item_id'], amount)
        new_amount = stock_find(self.item_id).json()['stock']

        self.assertFalse(res2.ok)
        self.assertEqual(new_amount, self.old_amount)


