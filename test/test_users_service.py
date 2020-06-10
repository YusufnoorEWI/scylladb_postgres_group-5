import os

import requests
import unittest

from random import randint, uniform
from uuid import UUID

user_host = os.getenv('USERS_SERVICE', 'http://127.0.0.1:8080/')
stock_host = os.getenv('STOCK_SERVICE', 'http://127.0.0.1:8080/')
payment_host = os.getenv('PAYMENT_SERVICE', 'http://127.0.0.1:8080/')
order_host = os.getenv('ORDER_SERVICE', 'http://127.0.0.1:8080/')


def users_create():
    return requests.post(f'{user_host}users/create')


def users_remove(user_id):
    return requests.delete(f'{user_host}users/remove/{user_id}')


def users_find(user_id):
    return requests.get(f'{user_host}users/find/{user_id}')


def users_credit_add(user_id, amount):
    return requests.post(f'{user_host}users/credit/add/{user_id}/{amount}')


def users_credit_subtract(user_id, amount):
    return requests.post(f'{user_host}users/credit/subtract/{user_id}/{amount}')


class TestUsersService(unittest.TestCase):
    user_id = ''
    old_credit = -1.0

    def setUp(self) -> None:
        self.user_id = users_create().json()['user_id']
        self.old_credit = users_find(self.user_id).json()['credit']

    def tearDown(self) -> None:
        users_remove(self.user_id)

    def test_users_create(self):
        res = users_create()
        user_id = res.json()['user_id']
        try:
            uuid_obj = UUID(user_id, version=4)
        except ValueError:
            return False

        self.assertTrue(res.ok)
        self.assertEqual(str(uuid_obj), user_id)

    def test_users_find(self):
        res = users_find(self.user_id)

        self.assertTrue(res.ok)

        user = res.json()
        self.assertEqual(user['credit'], 0.0)
        self.assertEqual(user['user_id'], self.user_id)

    def test_users_remove(self):
        res = users_find(self.user_id)

        self.assertTrue(res.ok)

        res2 = users_remove(self.user_id)
        self.assertTrue(res2.ok)

        res3 = users_find(self.user_id)
        self.assertFalse(res3.ok)

    def test_users_credit_add_positive_int(self):
        addition = randint(0, 100)
        res = users_credit_add(self.user_id, addition)
        new_credit = self.old_credit + addition

        self.assertTrue(res.ok)
        self.assertEqual(new_credit, res.json()['credit'])

    def test_users_credit_add_positive_float(self):
        addition = uniform(0, 100)
        res = users_credit_add(self.user_id, addition)
        new_credit = self.old_credit + addition

        self.assertTrue(res.ok)
        self.assertEqual(new_credit, res.json()['credit'])

    def test_users_credit_add_negative_int(self):
        addition = randint(-100, -1)
        res = users_credit_add(self.user_id, addition)

        new_credit = users_find(self.user_id).json()['credit']

        self.assertFalse(res.ok)
        self.assertEqual(self.old_credit, new_credit)

    def test_users_credit_add_negative_float(self):
        addition = uniform(-100, -1)
        res = users_credit_add(self.user_id, addition)

        new_credit = users_find(self.user_id).json()['credit']

        self.assertFalse(res.ok)
        self.assertEqual(self.old_credit, new_credit)

    def test_users_credit_subtract_positive_int(self):
        amount = randint(0, 100)
        res = users_credit_add(self.user_id, amount)
        new_credit = self.old_credit + amount

        self.assertTrue(res.ok)
        self.assertEqual(new_credit, res.json()['credit'])

        res2 = users_credit_subtract(self.user_id, amount)

        self.assertTrue(res2.ok)
        self.assertEqual(self.old_credit, res2.json()['credit'])

    def test_users_credit_subtract_positive_float(self):
        amount = uniform(0, 100)
        res = users_credit_add(self.user_id, amount)
        new_credit = self.old_credit + amount

        self.assertTrue(res.ok)
        self.assertEqual(new_credit, res.json()['credit'])

        res2 = users_credit_subtract(self.user_id, amount)

        self.assertTrue(res2.ok)
        self.assertEqual(self.old_credit, res2.json()['credit'])

    def test_users_credit_subtract_negative_int(self):
        amount = randint(-100, -1)
        res = users_credit_subtract(self.user_id, amount)
        new_credit = users_find(self.user_id).json()['credit']

        self.assertFalse(res.ok)
        self.assertEqual(self.old_credit, new_credit)

    def test_users_credit_subtract_negative_float(self):
        amount = uniform(-100, -1)
        res = users_credit_subtract(self.user_id, amount)
        new_credit = users_find(self.user_id).json()['credit']

        self.assertFalse(res.ok)
        self.assertEqual(self.old_credit, new_credit)

    def test_users_credit_subtract_insufficient(self):
        amount = uniform(0, 100)
        res = users_credit_add(self.user_id, amount)
        new_credit = self.old_credit + amount

        self.assertTrue(res.ok)
        self.assertEqual(new_credit, res.json()['credit'])

        res2 = users_credit_subtract(self.user_id, amount + 1.0)

        new_credit2 = users_find(self.user_id).json()['credit']

        self.assertFalse(res2.ok)
        self.assertEqual(new_credit, new_credit2)

    if __name__ == '__main__':
        unittest.main()

