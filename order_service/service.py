from decimal import Decimal

import requests
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from flask import Flask, abort, jsonify
from markupsafe import escape
from order_service.connector import ConnectorFactory

app = Flask(__name__)

connector = ConnectorFactory().get_connector()

user_host = os.getenv('USERS_SERVICE', 'http://127.0.0.1:5000/')
stock_host = os.getenv('STOCK_SERVICE', 'http://127.0.0.1:5000/')
payment_host = os.getenv('PAYMENT_SERVICE', 'http://127.0.0.1:5000/')


@app.route('/orders/create/<user_id>', methods=['POST'])
def create_order(user_id):
    """
    creates an order for the given user, and returns an order_id

    :param user_id: id of user to create order for
    :return: the order’s id
    """
    response = requests.get(user_host + 'users/find/' + str(user_id))
    if not response.ok:
        abort(404)
    order_id = connector.create_order(user_id)
    response = {
        "order_id": order_id
    }
    return jsonify(response)


@app.route('/orders/remove/<order_id>', methods=['DELETE'])
def delete_order(order_id):
    """
    deletes an order by ID

    :param order_id: id of order to be deleted
    """
    try:
        connector.delete_order(escape(order_id))
    except ValueError:
        abort(404)
    return jsonify({"success": True}), 200


@app.route('/orders/find/<order_id>', methods=['GET'])
def retrieve_order(order_id):
    try:
        order_paid, order_items, order_userid, \
            order_totalcost = connector.get_order_info(escape(order_id))
        response = {
            "order_id": order_id,
            "paid": str(order_paid),
            "items": order_items,
            "user_id": order_userid,
            "total_cost": str(order_totalcost)
        }
        return jsonify(response)
    except ValueError:
        abort(404)


@app.route('/orders/addItem/<order_id>/<item_id>', methods=['POST'])
def add_item(order_id, item_id):
    try:
        item_in, price = connector.find_item(order_id, item_id)
        if not item_in:
            response = requests.get(stock_host + 'stock/find/' + str(item_id))
            price = Decimal(response.json()['price'])
        item_num = connector.add_item(order_id=order_id, item_id=item_id, item_price=price)
        return jsonify({'item_amount': str(item_num)})
    except ValueError:
        abort(404)


@app.route('/orders/removeItem/<order_id>/<item_id>', methods=['DELETE'])
def remove_item(order_id, item_id):
    try:
        item_in, price = connector.find_item(order_id, item_id)
        if not item_in:
            raise ValueError('Item not in order')
        item_num = connector.remove_item(order_id, item_id)
        return jsonify({'item_list': str(item_num)})
    except ValueError:
        abort(404)


@app.route('/orders/checkout/<order_id>', methods=['POST'])
def checkout(order_id):
    """
    makes the payment (via calling the payment service), subtracts
    the stock (via the stock service) and returns a status (success/
    failure).

    """
    try:
        order_paid, order_items, user_id, totalcost = connector.get_order_info(escape(order_id))

        pay_order(user_id, order_id, totalcost)
        reserve_items(order_id, user_id, order_items)
        connector.set_paid(order_id=order_id)

        return jsonify({'status': 'success'})
    except ValueError as error:
        abort(400, error.args[0])


def pay_order(user_id, order_id, amount):
    response = requests.post(f'{payment_host}payment/pay/{user_id}/{order_id}/{amount}')
    if not response.ok:
        raise ValueError("Not enough credit")


def rollback_payment(user_id, order_id):
    return requests.post(f'{payment_host}payment/cancel/{user_id}/{order_id}')


def reserve_item(item_id, number):
    return requests.post(f'{stock_host}stock/subtract/{item_id}/{number}')


def reserve_items(order_id, user_id, items):
    reserved_items = []

    for item in items:
        item_num = connector.get_item_num(order_id=order_id, item_id=item)
        response = reserve_item(item, item_num)
        if response.ok:
            reserved_items.append(item)
        else:
            rollback_payment(user_id, order_id)
            rollback_items(order_id, reserved_items)
            raise ValueError("Not enough stock")


def rollback_item(item_id, number):
    return requests.post(f'{stock_host}stock/add/{item_id}/{number}')


def rollback_items(order_id, item_ids):
    for item_id in item_ids:
        number = connector.get_item_num(order_id=order_id, item_id=item_id)
        rollback_item(item_id, number)
