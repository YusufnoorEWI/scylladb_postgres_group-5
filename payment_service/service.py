import os
import sys
from flask import Flask, Response, jsonify

from payment_service.connector import ConnectorFactory


sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
#from payment_service.connector import ConnectorFactory

from payment_service.connector import ScyllaConnector

app = Flask(__name__)
db_host = os.getenv("DB_HOST", "127.0.0.1")
connector = ScyllaConnector(db_host)
#connector = ConnectorFactory().get_connector()






@app.route('/payment/pay/<user_id>/<order_id>/<amount>', methods=['POST'])
def pay(user_id, order_id, amount):
    connector.pay(user_id, order_id, amount)
    return Response('success', status=200)


@app.route('/payment/cancel/<user_id>/<order_id>', methods=['POST'])
def cancel_pay(user_id, order_id):
    connector.cancel_pay(user_id, order_id)
    return Response('success', status=200)


@app.route('/payment/status/<order_id>', methods=['GET'])
def status(order_id):
    payment_status = connector.status(order_id)
    return jsonify({"paid": payment_status})


if __name__ == '__main__':
    app.run()
