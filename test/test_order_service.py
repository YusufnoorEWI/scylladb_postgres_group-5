import unittest

from uuid import UUID
from test.endpoints import EndPoints as ep


class TestOrderService(unittest.TestCase):
    user1 = {}
    user2 = {}
    item1 = {}
    item2 = {}
    order1 = {}
    order2 = {}
    order3 = {}

    def setUp(self) -> None:
        self.user1 = ep.users_create().json()
        self.user2 = ep.users_create().json()
        ep.users_credit_add(self.user1['user_id'], 100)
        self.item1 = ep.stock_create(20).json()
        ep.stock_add(self.item1["item_id"], 3)
        self.item2 = ep.stock_create(10).json()
        ep.stock_add(self.item2["item_id"], 3)
        self.order1 = ep.orders_create(self.user1['user_id']).json()
        self.order2 = ep.orders_create(self.user2['user_id']).json()
        self.order3 = ep.orders_create(self.user2['user_id']).json()

        # First order will have item 1 two times and item 2 once, total price is 50
        ep.orders_add_item(self.order1['order_id'], self.item1['item_id'])
        ep.orders_add_item(self.order1['order_id'], self.item1['item_id'])
        ep.orders_add_item(self.order1['order_id'], self.item2['item_id'])

        # Order 2 has total price of 20
        ep.orders_add_item(self.order2['order_id'], self.item1['item_id'])

    def tearDown(self) -> None:
        ep.users_remove(self.user1['user_id'])
        ep.users_remove(self.user2['user_id'])

    def test_order_create_existing_user(self):
        res = ep.orders_create(self.user1['user_id'])
        order_id = res.json()['order_id']
        try:
            uuid_obj = UUID(order_id, version=4)
        except ValueError:
            return False

        self.assertTrue(res.ok)
        self.assertEqual(str(uuid_obj), order_id)

    def test_order_create_non_existing_user(self):
        res = ep.orders_create(self.order1['order_id'])

        self.assertFalse(res.ok)

    def test_order_find_existing(self):
        res = ep.orders_find(self.order1['order_id'])

        order = res.json()

        items = order['items']
        total_cost = 0
        for item in items:
            total_cost += ep.stock_find(item).json()['price']

        self.assertTrue(res.ok)
        self.assertEqual(order['order_id'], self.order1['order_id'])
        self.assertEqual(order['paid'], 'False')
        self.assertIn(self.item1['item_id'], order['items'])
        self.assertIn(self.item2['item_id'], order['items'])
        self.assertEqual(order['total_cost'], str(total_cost))
        self.assertEqual(order['user_id'], self.user1['user_id'])

    def test_order_find_not_existing(self):
        res = ep.orders_find(self.user1['user_id'])

        self.assertFalse(res.ok)

    def test_order_delete_existing(self):
        res = ep.orders_create(self.user1['user_id'])

        self.assertTrue(res.ok)

        res2 = ep.orders_remove(res.json()['order_id'])

        self.assertTrue(res2.ok)

        res3 = ep.orders_find(res.json()['order_id'])

        self.assertFalse(res3.ok)

    def test_order_delete_not_existing(self):
        res = ep.orders_remove(self.user1['user_id'])

        self.assertFalse(res.ok)

    def test_order_find_by_user_existing(self):
        res = ep.orders_find_by_user(self.user1['user_id'])

        orders = res.json()['order_ids']
        self.assertIsInstance(orders, list)
        self.assertIn(self.order1['order_id'], orders)

        res2 = ep.orders_create(self.user1['user_id'])

        self.assertTrue(res2.ok)

        res = ep.orders_find_by_user(self.user1['user_id'])
        orders = res.json()['order_ids']
        self.assertIsInstance(orders, list)
        self.assertIn(self.order1['order_id'], orders)
        self.assertIn(res2.json()['order_id'], orders)

    def test_order_find_by_user_non_existing(self):
        res = ep.orders_find_by_user(self.order1['order_id'])

        orders = res.json()['order_ids']

        self.assertTrue(res.ok)
        self.assertIsInstance(orders, list)
        self.assertEqual(len(orders), 0)

    def test_order_add_item_existing(self):
        res = ep.orders_add_item(self.order3['order_id'], self.item1['item_id'])

        amount = res.json()["item_amount"]

        self.assertTrue(res.ok)
        self.assertEqual(amount, str(1))

    def test_order_add_item_existing_twice(self):
        res = ep.orders_add_item(self.order3['order_id'], self.item1['item_id'])
        res2 = ep.orders_add_item(self.order3['order_id'], self.item1['item_id'])

        amount = res2.json()["item_amount"]

        self.assertTrue(res.ok)
        self.assertTrue(res2.ok)
        self.assertEqual(amount, str(2))

    def test_order_add_item_non_existing_order(self):
        res = ep.orders_add_item(self.user1['user_id'], self.item1['item_id'])
        self.assertFalse(res.ok)

    def test_order_add_item_non_existing_item(self):
        items_before = ep.orders_find(self.order1['order_id']).json()['items']

        res = ep.orders_add_item(self.order1['order_id'], self.user1['user_id'])

        items_after = ep.orders_find(self.order1['order_id']).json()['items']

        self.assertFalse(res.ok)
        self.assertCountEqual(items_before, items_after)

    def test_order_remove_item_existing(self):
        items_before = ep.orders_find(self.order1['order_id']).json()['items']
        res = ep.orders_remove_item(self.order1['order_id'], self.item1['item_id'])

        items_after = ep.orders_find(self.order1['order_id']).json()['items']

        test = items_before.copy()
        test.remove(self.item1['item_id'])

        self.assertTrue(res.ok)
        self.assertNotEqual(items_before, items_after)
        self.assertCountEqual(test, items_after)

    def test_order_remove_item_existing_twice(self):
        items_before = ep.orders_find(self.order1['order_id']).json()['items']
        res = ep.orders_remove_item(self.order1['order_id'], self.item1['item_id'])
        res2 = ep.orders_remove_item(self.order1['order_id'], self.item1['item_id'])
        items_after = ep.orders_find(self.order1['order_id']).json()['items']

        test = items_before.copy()
        test.remove(self.item1['item_id'])
        test.remove(self.item1['item_id'])

        self.assertTrue(res.ok)
        self.assertTrue(res2.ok)
        self.assertNotEqual(items_before, items_after)
        self.assertCountEqual(test, items_after)

    def test_order_remove_item_non_existing_order(self):
        res = ep.orders_remove_item(self.user1['user_id'], self.item1['item_id'])
        self.assertFalse(res.ok)

    def test_order_remove_item_non_existing_item(self):
        items_before = ep.orders_find(self.order1['order_id']).json()['items']

        res = ep.orders_remove_item(self.order1['order_id'], self.user1['user_id'])

        items_after = ep.orders_find(self.order1['order_id']).json()['items']

        self.assertFalse(res.ok)
        self.assertEqual(items_before, items_after)

    def test_order_checkout_enough_balance_payment(self):
        total_cost = float(ep.orders_find(self.order1['order_id']).json()['total_cost'])
        old_balance = float(ep.users_find(self.user1['user_id']).json()['credit'])
        res = ep.orders_checkout(self.order1['order_id'])

        new_balance = float(ep.users_find(self.user1['user_id']).json()['credit'])

        self.assertTrue(res.ok)
        self.assertGreaterEqual(old_balance, total_cost)
        self.assertEqual(new_balance, old_balance - total_cost)

    def test_order_checkout_enough_balance_stock(self):
        items = ep.orders_find(self.order1['order_id']).json()['items']

        stock_dict = {}
        for item in items:
            stock_dict[item] = ep.stock_find(item).json()['stock']

        order_dict = {}
        for item in items:
            if item in order_dict:
                order_dict[item] += 1
            else:
                order_dict[item] = 1

        res = ep.orders_checkout(self.order1['order_id'])

        self.assertTrue(res.ok)

        for item in items:
            self.assertEqual(stock_dict[item] - order_dict[item], ep.stock_find(item).json()['stock'])

    def test_order_checkout_insufficient_balance(self):
        total_cost = float(ep.orders_find(self.order2['order_id']).json()['total_cost'])
        old_balance = float(ep.users_find(self.user2['user_id']).json()['credit'])

        res = ep.orders_checkout(self.order2['order_id'])

        new_balance = float(ep.users_find(self.user2['user_id']).json()['credit'])

        self.assertFalse(res.ok)
        self.assertLessEqual(old_balance, total_cost)
        self.assertEqual(old_balance, new_balance)

    def test_order_checkout_insufficient_stock(self):
        items = ep.orders_find(self.order2['order_id']).json()['items']

        stock_dict = {}
        for item in items:
            stock_dict[item] = ep.stock_find(item).json()['stock']

        order_dict = {}
        for item in items:
            if item in order_dict:
                order_dict[item] += 1
            else:
                order_dict[item] = 1

        res = ep.orders_checkout(self.order2['order_id'])

        self.assertFalse(res.ok)

        for item in items:
            self.assertEqual(stock_dict[item], ep.stock_find(item).json()['stock'])

    def test_order_checkout_non_existing(self):
        res = ep.orders_checkout(self.user1['user_id'])

        self.assertFalse(res.ok)

    def test_order_success_paid(self):
        res = ep.orders_find(self.order1['order_id'])

        self.assertTrue(res.ok)
        paid_before = res.json()['paid']

        self.assertEqual(paid_before, 'False')

        res2 = ep.orders_checkout(self.order1['order_id'])
        res3 = ep.orders_find(self.order1['order_id'])

        self.assertTrue(res2.ok)
        self.assertTrue(res3.ok)
        paid_after = res3.json()['paid']

        self.assertEqual(paid_after, 'True')

    if __name__ == '__main__':
        unittest.main()


