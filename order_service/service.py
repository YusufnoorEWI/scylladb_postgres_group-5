import requests
import sys
import os

from _decimal import InvalidOperation
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from flask import Flask, abort, jsonify
from markupsafe import escape
from order_service.connector import ScyllaConnector

app = Flask(__name__)
connector = ScyllaConnector()

user_host = os.getenv('user', 'http://127.0.0.1:5000/')
stock_host = os.getenv('stock', 'http://127.0.0.1:5000/')
payment_host = os.getenv('payment', 'http://127.0.0.1:5000/')
   
@app.route('/order/create/<user_id>', methods=['POST'])
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
    

@app.route('/order/remove/<order_id>', methods=['DELETE'])
def delete_order(order_id):
    '''
    deletes an order by ID
    '''
    try:
        connector.delete_order(escape(order_id))
    except ValueError:
        abort(404)
    return jsonify({"success":True}), 200

@app.route('/order/find/<order_id>', methods=['GET'])
def retrieve_order(order_id):
    try:
        order_paid, order_items, order_userid,\
        order_totalcost = connector.get_order_info(escape(order_id))
        response = {
            "order_id": order_id,
            "paid": str(order_paid),
            "items": ' '.join(order_items),
            "user_id": order_userid,
            "total_cost": str(order_totalcost)
        }
        return jsonify(response)
    except ValueError:
        abort(404)

@app.route('/order/addItem/<order_id>/<item_id>', methods=['POST'])
def add_item(order_id, item_id):
    try:
        response = requests.get(stock_host + 'stock/find/'+ str(item_id))
        item_list = connector.add_item(order_id, item_id, response['price'])
        return jsonify({'item_list':str(' '.join(str(k) for k in item_list))})
    except ValueError:
        abort(404)

@app.route('/order/removeItem/<order_id>/<item_id>', methods=['DELETE'])
def remove_item(order_id, item_id):
    try:
        response = requests.get(stock_host + 'stock/find/'+ str(item_id))
        item_list = connector.remove_item(order_id, item_id, response['price'])
        return jsonify({'item_list':str(' '.join(str(k) for k in item_list))})
    except ValueError:
        abort(404)

@app.route('/order/checkout/<order_id>', methods=['POST'])
def checkout(order_id):
    ''' 
    makes the payment (via calling the payment service), subtracts 
    the stock (via the stock service) and returns a status (success/
    failure).

    '''
    #BUG: completely have no idea on how to call payment serv
    try:
        order_paid, order_items, order_userid,\
        totalcost = connector.get_order_info(escape(order_id))
        user_id = connector.get_user_id(order_id)
        response = requests.get(payment_host + 'payment/pay/'+ str(user_id) +'/' \
            + str(order_id))
        if response.ok is False:
            abort(404)
        items = connector.get_items(order_id)
        for item in items:
            response = requests.get(stock_host + 'stock/subtract/'+ str(item) +'/' \
                + str(1))
            if response.ok is False:
                abort(404)
        return jsonify({'status':'success'})
    except:
        return jsonify({'status':'fail'})
    