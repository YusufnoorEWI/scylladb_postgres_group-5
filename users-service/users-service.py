from flask import Flask, abort
from .connector import ScyllaConnector

app = Flask(__name__)
connector = ScyllaConnector()

@app.route('/users/create', methods=['POST'])
def create():
    """Creates an item with the price defined in the request body.

    :return: the id of the created item
    """
    try:
        user_id = connector.create()
        return str(user_id)
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

@app.route('/users/find/<user_id>', methods=['GET'])
def find_user(user_id):
    """Returns the availability of the item.

    :param item_id: the id of the item
    :return: the number of the item in stock
    """
    try:
        user = connector.get_user(user_id)
        return str(user)
    except ValueError:
        abort(404)

@app.route('/users/credit/<user_id>', methods=['GET'])
def credit(user_id):
    """Returns the availability of the item.

    :param item_id: the id of the item
    :return: the number of the item in stock
    """
    try:
        user = connector.get_user(user_id)
        return str(user.credit)
    except ValueError:
        abort(404)


@app.route('/users/credit/subtract/<user_id>/<int:number>', methods=['POST'])
def subtract_amount(user_id, number):
    """Subtracts the given number from the item count.

    :param item_id: the id of the item
    :param number: the number to subtract from stock
    :return: the number of the item in stock
    """
    try:
        connector.subtract_amount(user_id, number)
        return "success"
    except AssertionError:
        abort(400)
    except ValueError:
        abort(404)


@app.route('/users/credit/add/<user_id>/<int:number>', methods=['POST'])
def add_amount(user_id, number):
    """Adds the given number to the item count.

    :param item_id: the id of the item
    :param number: the number to add to stock
    :return: the number of the item in stock
    """
    try:
        connector.add_amount(user_id, number)
        return "success"
    except ValueError:
        abort(404)



