from flask import Flask, abort
from flask import request
from markupsafe import escape
from .connector import ScyllaConnector

app = Flask(__name__)
connector = ScyllaConnector()


@app.route('/stock/availability/<item_id>', methods=['GET'])
def get_availability(item_id):
    try:
        item_count = connector.get_availability(escape(item_id))
        return str(item_count)
    except ValueError:
        abort(404)


@app.route('/stock/subtract/<item_id>/<int:number>', methods=['POST'])
def subtract_amount(item_id, number):
    try:
        item_count = connector.subtract_amount(item_id, number)
        return str(item_count)
    except AssertionError:
        abort(400)
    except ValueError:
        abort(404)


@app.route('/stock/add/<item_id>/<int:number>', methods=['POST'])
def add_amount(item_id, number):
    try:
        item_count = connector.add_amount(item_id, number)
        return str(item_count)
    except ValueError:
        abort(404)


@app.route('/stock/create', methods=['POST'])
def create_item():
    try:
        price = int(escape(request.form['price']))
        item_id = connector.create_item(price)
        return str(item_id)
    except:
        abort(500)
