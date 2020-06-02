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

user_host = os.getenv('user', 'http://127.0.0.1:5000/')
stock_host = os.getenv('stock', 'http://127.0.0.1:5000/')
payment_host = os.getenv('payment', 'http://127.0.0.1:5000/')
@app.route('/orders/create/<user_id>', methods=['POST'])
def create_order(user_id):
    '''
    creates an order for the given user, and returns an order_id
   
    return: the order’s id
    '''
    response = requests.get(user_host + 'users/find/'+ str(user_id))
    if response.ok == False:
        abort(404)
    order_id = connector.create_order(user_id)
    response = {
        "order_id": order_id
    }
    return jsonify(response)


@app.route('/orders/remove/<order_id>', methods=['DELETE'])
def delete_order(order_id):
    '''
    deletes an order by ID
    '''
    try:
        connector.delete_order(escape(order_id))
    except ValueError:
        abort(404)
    return jsonify({"success":True}), 200

@app.route('/orders/find/<order_id>', methods=['GET'])
def retrieve_order(order_id):
    try:
        order_paid, order_items, order_userid,\
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
            response = requests.get(stock_host + 'stock/find/'+ str(item_id))
            price = Decimal(response.json()['price'])
        item_num = connector.add_item(order_id=order_id, item_id=item_id, item_price=price)
        return jsonify({'item_amount':str(item_num)})
    except ValueError:
        abort(404)

@app.route('/orders/removeItem/<order_id>/<item_id>', methods=['DELETE'])
def remove_item(order_id, item_id):
    try:
        item_in, price = connector.find_item(order_id, item_id)
        if not item_in:
            raise ValueError('Item not in order')
        item_num = connector.remove_item(order_id, item_id)
        return jsonify({'item_list':str(item_num)})
    except ValueError:
        abort(404)

@app.route('/orders/checkout/<order_id>', methods=['POST'])
def checkout(order_id):
    ''' 
    makes the payment (via calling the payment service), subtracts 
    the stock (via the stock service) and returns a status (success/
    failure).

    '''
    try:
        order_paid, order_items, order_userid,\
        totalcost = connector.get_order_info(escape(order_id))
        response = requests.post(payment_host + 'payment/pay/'+ str(order_userid) +'/' \
            + str(order_id)+'/'+str(totalcost))
        if response.ok is False:
            abort(404)

        for item in order_items:
            item = connector.get_order_item(order_id, item)
            item_num = connector.get_item_num(order_id=order_id, item_id=item.item_id)
            response = requests.post(stock_host + 'stock/subtract/'+ str(item) +'/' \
                + str(item_num))
            if response.ok is False:
                abort(404)
        connector.set_paid(order_id=order_id)
        return jsonify({'status':'success'})
    except ValueError:
        return jsonify({'status':'fail'})
    