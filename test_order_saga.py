import os
from decimal import Decimal

import requests
import unittest

user_host = os.getenv('user', 'http://127.0.0.1:8080/')
stock_host = os.getenv('stock', 'http://127.0.0.1:8080/')
payment_host = os.getenv('payment', 'http://127.0.0.1:8080/')
order_host = os.getenv('order', 'http://127.0.0.1:5000/')


def stock_create(price):
    return requests.post(f'{stock_host}stock/item/create/{price}').json()['item_id']


def stock_add(item_id, count):
    requests.post(f'{stock_host}stock/add/{item_id}/{count}')


def stock_find(item_id):
    return requests.get(f'{stock_host}stock/find/{item_id}').json()['stock']


def user_create():
    return requests.post(f'{user_host}users/create').json()['user_id']


def user_credit_add(user_id, amount):
    requests.post(f'{user_host}users/credit/add/{user_id}/{amount}')


def user_credit(user_id):
    return requests.get(f'{user_host}users/find/{user_id}').json()['credit']


def order_create(user_id):
    return requests.post(f'{order_host}orders/create/{user_id}').json()['order_id']


def order_add_item(order_id, item_id):
    requests.post(f'{order_host}orders/addItem/{order_id}/{item_id}')


def order_checkout(order_id):
    return requests.post(f'{order_host}orders/checkout/{order_id}')


class TestOrderSAGA(unittest.TestCase):

    def test_happy_flow(self):
        item_id = stock_create(5.5)
        item_id2 = stock_create(1)
        stock_add(item_id, 10)
        stock_add(item_id2, 10)

        user_id = user_create()
        user_credit_add(user_id, 500)

        order_id = order_create(user_id)
        order_add_item(order_id, item_id)
        order_add_item(order_id, item_id2)

        response = order_checkout(order_id)

        self.assertTrue(response.ok)
        self.assertEqual(int(stock_find(item_id)), 9)
        self.assertEqual(int(stock_find(item_id2)), 9)
        self.assertEqual(Decimal(user_credit(user_id)), Decimal(493.5))

    def test_insufficient_credit(self):
        item_id = stock_create(5.5)
        item_id2 = stock_create(1)
        stock_add(item_id, 10)
        stock_add(item_id2, 10)

        user_id = user_create()
        user_credit_add(user_id, 1)

        order_id = order_create(user_id)
        order_add_item(order_id, item_id)
        order_add_item(order_id, item_id2)

        response = order_checkout(order_id)

        self.assertFalse(response.ok)
        self.assertEqual(int(stock_find(item_id)), 10)
        self.assertEqual(int(stock_find(item_id2)), 10)
        self.assertEqual(Decimal(user_credit(user_id)), Decimal(1))

    def test_insufficient_stock(self):
        item_id = stock_create(5.5)
        item_id2 = stock_create(1)
        stock_add(item_id, 10)
        stock_add(item_id2, 0)

        user_id = user_create()
        user_credit_add(user_id, 500)

        order_id = order_create(user_id)
        order_add_item(order_id, item_id)
        order_add_item(order_id, item_id2)

        response = order_checkout(order_id)

        self.assertFalse(response.ok)
        self.assertEqual(int(stock_find(item_id)), 10)
        self.assertEqual(int(stock_find(item_id2)), 0)
        self.assertEqual(Decimal(user_credit(user_id)), Decimal(500))

    def test_insufficient_stock2(self):
        item_id = stock_create(5.5)
        item_id2 = stock_create(1)
        stock_add(item_id, 0)
        stock_add(item_id2, 10)

        user_id = user_create()
        user_credit_add(user_id, 500)

        order_id = order_create(user_id)
        order_add_item(order_id, item_id)
        order_add_item(order_id, item_id2)

        response = order_checkout(order_id)

        self.assertFalse(response.ok)
        self.assertEqual(int(stock_find(item_id)), 0)
        self.assertEqual(int(stock_find(item_id2)), 10)
        self.assertEqual(Decimal(user_credit(user_id)), Decimal(500))

    def test_insufficient_stock3(self):
        item_id = stock_create(5.5)
        item_id2 = stock_create(1)
        stock_add(item_id, 10)
        stock_add(item_id2, 1)

        user_id = user_create()
        user_credit_add(user_id, 500)

        order_id = order_create(user_id)
        order_add_item(order_id, item_id)
        order_add_item(order_id, item_id2)
        order_add_item(order_id, item_id2)

        response = order_checkout(order_id)

        self.assertFalse(response.ok)
        self.assertEqual(int(stock_find(item_id)), 10)
        self.assertEqual(int(stock_find(item_id2)), 1)
        self.assertEqual(Decimal(user_credit(user_id)), Decimal(500))
