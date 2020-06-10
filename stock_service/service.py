from _decimal import InvalidOperation
from decimal import Decimal
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from flask import Flask, abort, jsonify
from markupsafe import escape
from stock_service.connector import ConnectorFactory

app = Flask(__name__)

connector = ConnectorFactory().get_connector()


@app.route('/stock/find/<item_id>', methods=['GET'])
def find_item(item_id):
    """Returns the item.

    :param item_id: the id of the item
    :return: the number of the item in stock
    """
    try:
        item = connector.get_item(escape(item_id))
        response = {
            "item_id": item.id,
            "stock": item.in_stock,
            "price": item.price
        }

        return jsonify(response)
    except ValueError:
        abort(404)


@app.route('/stock/subtract/<item_id>/<int:number>', methods=['POST'])
def subtract_amount(item_id, number):
    """Subtracts the given number from the item count.

    :param item_id: the id of the item
    :param number: the number to subtract from stock
    :return: the number of the item in stock
    """
    try:
        item_count = connector.subtract_amount(item_id, number)
        return str(item_count)
    except AssertionError:
        abort(400)
    except ValueError:
        abort(404)


@app.route('/stock/add/<item_id>/<int:number>', methods=['POST'])
def add_amount(item_id, number):
    """Adds the given number to the item count.

    :param item_id: the id of the item
    :param number: the number to add to stock
    :return: the number of the item in stock
    """
    try:
        item_count = connector.add_amount(item_id, number)
        return str(item_count)
    except ValueError:
        abort(404)


@app.route('/stock/item/create/<price>', methods=['POST'])
def create_item(price):
    """Creates an item with the specified price.

    :return: the id of the created item
    """
    if Decimal(price) < 0:
        abort(404)

    try:
        item_id = connector.create_item(Decimal(price))
        response = {
            "item_id": item_id,
        }

        return jsonify(response)
    except InvalidOperation:
        abort(404)
