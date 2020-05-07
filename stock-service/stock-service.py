from flask import Flask
from flask import request
from markupsafe import escape

app = Flask(__name__)


@app.route('/stock/availability/<item_id>', methods=['GET'])
def get_availability(item_id):
    pass


@app.route('/stock/subtract/<item_id>/<number>', methods=['POST'])
def subtract_item(item_id, number):
    pass


@app.route('/stock/add/<item_id>/<number>', methods=['POST'])
def add_item(item_id, number):
    pass


@app.route('/stock/create', methods=['POST'])
def create_item():
    pass

