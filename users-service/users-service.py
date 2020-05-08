from flask import Flask, abort
from markupsafe import escape
from .connector import ScyllaConnector

app = Flask(__name__)
connector = ScyllaConnector()

@app.route('/users/create', methods=['POST'])
def create():
    """Creates an item with the price defined in the request body.

    :return: the id of the created item
    """
    try:
        item_id = connector.create()
        return str(item_id)
    except:
        abort(500)

@app.route('/users/remove/<user_id>', methods=['DELETE'])
def remove(user_id):
    """Creates an item with the price defined in the request body.

    :return: the id of the created item
    """
    try:
        connector.remove(user_id)
        return "success"
    except:
        abort(500)



@app.route('/stock/availability/<item_id>', methods=['GET'])
def get_availability(item_id):
    """Returns the availability of the item.

    :param item_id: the id of the item
    :return: the number of the item in stock
    """
    try:
        item_count = connector.get_availability(escape(item_id))
        return str(item_count)
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



