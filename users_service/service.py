from decimal import *
from flask import Flask, abort, jsonify
import sys
import os
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from users_service.connector import ConnectorFactory

app = Flask(__name__)
connector = ConnectorFactory().get_connector()


order_host = os.getenv('ORDER_SERVICE', '127.0.0.1:8080')


@app.route('/users/create', methods=['POST'])
def create():
    """Creates a user with zero initial credit.

    :return: the id of the created user
    """
    try:
        user_id = connector.create()
        return jsonify({"user_id": user_id}), 200
    except:
        abort(500)


@app.route('/users/remove/<user_id>', methods=['DELETE'])
def remove(user_id):
    """Removes a user with the given user id.

    :return: success if successful, 404 error otherwise
    """
    # try:
    res = requests.get(f"http://{order_host}/orders/findByUser/{user_id}")
    res = res.json()
    connector.remove(user_id)
    order_ids = res['order_ids']
    for order_id in order_ids:
        requests.delete(f"http://{order_host}/orders/remove/{order_id}")
    return jsonify({"success": True}), 200
    # except:
    #     abort(404)


@app.route('/users/find/<user_id>', methods=['GET'])
def find_user(user_id):
    """Returns the user given the user is

    :param user_id: the id of the user
    :return: the user object
    """
    try:
        user = connector.get_user(user_id)
        return jsonify({"user_id": user.id, "credit": user.credit}), 200
    except ValueError:
        abort(404)


@app.route('/users/credit/subtract/<user_id>/<number>', methods=['POST'])
def subtract_amount(user_id, number):
    """Subtracts the given number from the user's credit.

    :param user_id: the id of the user
    :param number: the number to subtract from credit
    :return: the remaining credit if successful, error otherwise
    """
    try:
        amount = Decimal(number)
        if amount < 0:
            abort(404)

        result = connector.subtract_amount(user_id, amount)
        return jsonify({"success": True, "credit": result}), 200
    except AssertionError:
        abort(400)
    except (ValueError, InvalidOperation):
        abort(404)


@app.route('/users/credit/add/<user_id>/<number>', methods=['POST'])
def add_amount(user_id, number):
    """Adds the given number to the user's credit.

    :param user_id: the id of the user
    :param number: the number to add to credit
    :return: the total credit of the user if successful, error otherwise
    """
    try:
        amount = Decimal(number)
        if amount < 0:
            abort(404)

        result = connector.add_amount(user_id, amount)
        return jsonify({"success": True, "credit": result}), 200
    except (ValueError, InvalidOperation):
        abort(404)
