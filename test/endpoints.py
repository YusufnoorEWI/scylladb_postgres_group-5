import os

import requests


class EndPoints:
    order_host = os.getenv('ORDER_SERVICE', 'http://127.0.0.1:8080/')
    stock_host = os.getenv('STOCK_SERVICE', 'http://127.0.0.1:8080/')
    user_host = os.getenv('USERS_SERVICE', 'http://127.0.0.1:8080/')

    @staticmethod
    def users_create():
        return requests.post(f'{EndPoints.user_host}users/create')

    @staticmethod
    def users_remove(user_id):
        return requests.delete(f'{EndPoints.user_host}users/remove/{user_id}')

    @staticmethod
    def users_find(user_id):
        return requests.get(f'{EndPoints.user_host}users/find/{user_id}')

    @staticmethod
    def users_credit_add(user_id, amount):
        return requests.post(f'{EndPoints.user_host}users/credit/add/{user_id}/{amount}')

    @staticmethod
    def users_credit_subtract(user_id, amount):
        return requests.post(f'{EndPoints.user_host}users/credit/subtract/{user_id}/{amount}')

    @staticmethod
    def stock_create(price):
        return requests.post(f'{EndPoints.stock_host}stock/item/create/{price}')

    @staticmethod
    def stock_find(item_id):
        return requests.get(f'{EndPoints.stock_host}stock/find/{item_id}')

    @staticmethod
    def stock_add(item_id, amount):
        return requests.post(f'{EndPoints.stock_host}stock/add/{item_id}/{amount}')

    @staticmethod
    def stock_subtract(item_id, amount):
        return requests.post(f'{EndPoints.stock_host}stock/subtract/{item_id}/{amount}')

    @staticmethod
    def orders_create(user_id):
        return requests.post(f'{EndPoints.order_host}orders/create/{user_id}')

    @staticmethod
    def orders_remove(order_id):
        return requests.delete(f'{EndPoints.order_host}orders/remove/{order_id}')

    @staticmethod
    def orders_find(order_id):
        return requests.get(f'{EndPoints.order_host}orders/find/{order_id}')

    @staticmethod
    def orders_find_by_user(user_id):
        return requests.get(f'{EndPoints.order_host}orders/findByUser/{user_id}')

    @staticmethod
    def orders_add_item(order_id, item_id):
        return requests.post(f'{EndPoints.order_host}orders/addItem/{order_id}/{item_id}')

    @staticmethod
    def orders_remove_item(order_id, item_id):
        return requests.delete(f'{EndPoints.order_host}orders/removeItem/{order_id}/{item_id}')

    @staticmethod
    def orders_checkout(order_id):
        return requests.post(f'{EndPoints.order_host}orders/checkout/{order_id}')
