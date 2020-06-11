import unittest

from random import randint, uniform
from uuid import UUID
from test.endpoints import EndPoints as ep


class TestUsersService(unittest.TestCase):
    user_id = ''
    old_credit = -1.0

    def setUp(self) -> None:
        self.user_id = ep.users_create().json()['user_id']
        self.old_credit = ep.users_find(self.user_id).json()['credit']

    def tearDown(self) -> None:
        ep.users_remove(self.user_id)

    def test_users_create(self):
        res = ep.users_create()
        user_id = res.json()['user_id']
        try:
            uuid_obj = UUID(user_id, version=4)
        except ValueError:
            return False

        self.assertTrue(res.ok)
        self.assertEqual(str(uuid_obj), user_id)

    def test_users_find(self):
        res = ep.users_find(self.user_id)

        self.assertTrue(res.ok)

        user = res.json()
        self.assertEqual(user['credit'], 0.0)
        self.assertEqual(user['user_id'], self.user_id)

    def test_users_remove(self):
        res = ep.users_find(self.user_id)

        self.assertTrue(res.ok)

        res2 = ep.users_remove(self.user_id)
        self.assertTrue(res2.ok)

        res3 = ep.users_find(self.user_id)
        self.assertFalse(res3.ok)

    def test_users_credit_add_positive_int(self):
        addition = randint(0, 100)
        res = ep.users_credit_add(self.user_id, addition)
        new_credit = self.old_credit + addition

        self.assertTrue(res.ok)
        self.assertEqual(new_credit, res.json()['credit'])

    def test_users_credit_add_positive_float(self):
        addition = uniform(0, 100)
        res = ep.users_credit_add(self.user_id, addition)
        new_credit = self.old_credit + addition

        self.assertTrue(res.ok)
        self.assertEqual(new_credit, res.json()['credit'])

    def test_users_credit_add_negative_int(self):
        addition = randint(-100, -1)
        res = ep.users_credit_add(self.user_id, addition)

        new_credit = ep.users_find(self.user_id).json()['credit']

        self.assertFalse(res.ok)
        self.assertEqual(self.old_credit, new_credit)

    def test_users_credit_add_negative_float(self):
        addition = uniform(-100, -1)
        res = ep.users_credit_add(self.user_id, addition)

        new_credit = ep.users_find(self.user_id).json()['credit']

        self.assertFalse(res.ok)
        self.assertEqual(self.old_credit, new_credit)

    def test_users_credit_subtract_positive_int(self):
        amount = randint(0, 100)
        res = ep.users_credit_add(self.user_id, amount)
        new_credit = self.old_credit + amount

        self.assertTrue(res.ok)
        self.assertEqual(new_credit, res.json()['credit'])

        res2 = ep.users_credit_subtract(self.user_id, amount)

        self.assertTrue(res2.ok)
        self.assertEqual(self.old_credit, res2.json()['credit'])

    def test_users_credit_subtract_positive_float(self):
        amount = uniform(0, 100)
        res = ep.users_credit_add(self.user_id, amount)
        new_credit = self.old_credit + amount

        self.assertTrue(res.ok)
        self.assertEqual(new_credit, res.json()['credit'])

        res2 = ep.users_credit_subtract(self.user_id, amount)

        self.assertTrue(res2.ok)
        self.assertEqual(self.old_credit, res2.json()['credit'])

    def test_users_credit_subtract_negative_int(self):
        amount = randint(-100, -1)
        res = ep.users_credit_subtract(self.user_id, amount)
        new_credit = ep.users_find(self.user_id).json()['credit']

        self.assertFalse(res.ok)
        self.assertEqual(self.old_credit, new_credit)

    def test_users_credit_subtract_negative_float(self):
        amount = uniform(-100, -1)
        res = ep.users_credit_subtract(self.user_id, amount)
        new_credit = ep.users_find(self.user_id).json()['credit']

        self.assertFalse(res.ok)
        self.assertEqual(self.old_credit, new_credit)

    def test_users_credit_subtract_insufficient(self):
        amount = uniform(0, 100)
        res = ep.users_credit_add(self.user_id, amount)
        new_credit = self.old_credit + amount

        self.assertTrue(res.ok)
        self.assertEqual(new_credit, res.json()['credit'])

        res2 = ep.users_credit_subtract(self.user_id, amount + 1.0)

        new_credit2 = ep.users_find(self.user_id).json()['credit']

        self.assertFalse(res2.ok)
        self.assertEqual(new_credit, new_credit2)

    if __name__ == '__main__':
        unittest.main()
