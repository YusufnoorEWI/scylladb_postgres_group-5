import os
import requests
from flask import Flask, abort, Response, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.postgresql import UUID

app = Flask(__name__)

# change the IP in the docker-compose.yml
user_ip = os.environ['USER_SERVICE_URL']

db_user = os.environ['POSTGRES_USER']
db_password = os.environ['POSTGRES_PASSWORD']
db_host = os.environ['POSTGRES_HOST']
db_port = os.environ['POSTGRES_PORT']
db_name = os.environ['POSTGRES_DB']

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Payment(db.Model):
    # Define Payment table
    __table_name__ = 'payments'
    id = db.Column(UUID(as_uuid=True), primary_key=True)
    user_id = db.Column(UUID(as_uuid=True), nullable=False)
    order_id = db.Column(UUID(as_uuid=True), nullable=False)
    status = db.Column(db.Boolean())
    amount = db.Column(db.Float())

    # Define all the views
    def get_data(self):
        return {
            'user_id': str(self.user_id),
            'payment_id': str(self.payment_id),
            'status': self.status,
            'order_id': str(self.order_id),
            'amount': str(self.amount)
        }

    def get_status(self):
        return {
            'status': self.status
        }


db.create_all()
db.session.commit()


@app.route('/payment/pay/<user_id>/<order_id>/<amount>', methods=['POST'])
def pay(user_id, order_id, amount):
    try:
        payment: Payment = Payment.query.filter_by(order_id=order_id, user_id=user_id).first()
        if payment is not None:  # payment exists in the database
            if payment.status is True:
                abort(400, "the payment is already made")

        users_response = requests.post(f"http://{user_ip}/users/credit/subtract/{user_id}/{amount}")
        if users_response.status_code == 400 or users_response.status_code == 404:
            abort(400, "User service failure")

        if payment is not None:
            payment.status = True
            payment.amount = amount
        else:
            payment = Payment(user_id=user_id, order_id=order_id, status=True, amount=amount)
        db.session.add(payment)
        db.session.commit()
    except SQLAlchemyError:
        return Response('Error in the database', status=400)
    else:
        return Response('success', status=200)


@app.route('/payment/cancel/<user_id>/<order_id>', methods=['POST'])
def cancel_pay(user_id, order_id):
    try:
        payment: Payment = Payment.query.filter_by(order_id=order_id, user_id=user_id).first()
        if payment is None:
            abort(400, 'payment does not exist')
        if payment.status is False:
            abort(400, "the payment is not made")
        users_response = requests.post(f"http://{user_ip}/users/credit/add/{user_id}/{payment.amount}")
        if users_response.status_code == 400 or users_response.status_code == 404:
            abort(400, "User service failure")
        payment.status = False
        db.session.add(payment)
        db.session.commit()
    except SQLAlchemyError:
        return Response('Error in the database', status=400)
    else:
        return Response('success', status=200)


@app.route('/payment/status/<order_id>', methods=['GET'])
def status(order_id):
    try:
        payment: Payment = Payment.query.filter_by(order_id=order_id).first()
        if payment is None:
            abort(400, 'payment does not exist')
    except SQLAlchemyError:
        return Response('Error in the database', status=400)
    else:
        return jsonify({"paid": payment.status})


if __name__ == '__main__':
    app.run()
