import os
from flask import Flask, abort, Response, jsonify, request
from .connector import ScyllaConnector

app = Flask(__name__)
connector = ScyllaConnector()


@app.route('/payment/pay/<user_id>/<order_id>/<amount>', methods=['POST'])
def pay(user_id, order_id, amount):
    try:
        connector.pay(user_id, order_id, amount)
    except:
        return Response('Error in the database', status=500)
    else:
        return Response('success', status=200)


@app.route('/payment/cancel/<user_id>/<order_id>', methods=['POST'])
def cancel_pay(user_id, order_id):
    try:
        connector.cancel_pay(user_id, order_id)
    except:
        return Response('Error in the database', status=500)
    else:
        return Response('success', status=200)


@app.route('/payment/status/<order_id>', methods=['GET'])
def status(order_id):
    try:
        payment = connector.status(order_id)
        return jsonify({"id": payment.id, "order_id": payment.order_id, "paid": payment.status}), 200
    except:
        return Response('Error in the database', status=500)


if __name__ == '__main__':
    app.run()
