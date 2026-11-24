import os

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import BadRequest, HTTPException

from backend.in_memory_storage import InMemoryStorage
from backend.order_tracker import (
    DuplicateOrderError, OrderError, OrderNotFoundError, OrderTracker)
from backend.sample_orders import load_sample_orders

app = Flask(__name__, static_folder='../frontend')
in_memory_storage = InMemoryStorage()
order_tracker = OrderTracker(in_memory_storage)
# Start with a few sample orders so the page isn't empty. The API tests clear
# storage before each test, so these never affect test results.
load_sample_orders(order_tracker)

REQUIRED_ORDER_FIELDS = ("order_id", "item_name", "quantity", "customer_id")
LIST_FILTERS = ("status", "customer_id")

# HTTP status for each OrderError subclass; any other OrderError is a 400.
ERROR_STATUS_CODES = {DuplicateOrderError: 409, OrderNotFoundError: 404}


def error_response(message, status_code):
    return jsonify({"error": message}), status_code


def read_json_body():
    """Returns the request's JSON object, or raises a 400 Bad Request."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise BadRequest("Request body must be a JSON object.")
    return data


# --- Error handlers: every API error is {"error": "<message>"} ---
@app.errorhandler(OrderError)
def handle_order_error(error):
    status_code = ERROR_STATUS_CODES.get(type(error), 400)
    return error_response(str(error), status_code)


@app.errorhandler(HTTPException)
def handle_http_error(error):
    """Returns JSON for HTTP errors on API routes (e.g. 400, 404, 405)."""
    if request.path.startswith("/api/"):
        return error_response(error.description, error.code)
    return error


# --- Frontend ---
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)


# --- API ---
@app.route('/api/orders', methods=['POST'])
def add_order_api():
    data = read_json_body()
    missing = [field for field in REQUIRED_ORDER_FIELDS if field not in data]
    if missing:
        raise BadRequest(f"Missing required field(s): {', '.join(missing)}")

    order = order_tracker.add_order(
        order_id=data["order_id"],
        item_name=data["item_name"],
        quantity=data["quantity"],
        customer_id=data["customer_id"],
        status=data.get("status", "pending"),
    )
    return jsonify(order), 201


@app.route('/api/orders/<string:order_id>', methods=['GET'])
def get_order_api(order_id):
    order = order_tracker.get_order_by_id(order_id)
    if order is None:
        return error_response(f"Order with ID '{order_id}' not found.", 404)
    return jsonify(order), 200


@app.route('/api/orders/<string:order_id>/status', methods=['PUT'])
def update_order_status_api(order_id):
    data = read_json_body()
    if "new_status" not in data:
        raise BadRequest("Request body must include a 'new_status' field.")

    order = order_tracker.update_order_status(order_id, data["new_status"])
    return jsonify(order), 200


@app.route('/api/orders/<string:order_id>', methods=['DELETE'])
def delete_order_api(order_id):
    return jsonify(order_tracker.delete_order(order_id)), 200


@app.route('/api/orders', methods=['GET'])
def list_orders_api():
    # A filter left out matches everything; one that is present but empty
    # (e.g. ?status=) is passed through so OrderTracker rejects it.
    filters = {name: request.args[name]
               for name in LIST_FILTERS if name in request.args}
    if not filters:
        return jsonify(order_tracker.list_all_orders()), 200
    return jsonify(order_tracker.filter_orders(**filters)), 200


if __name__ == '__main__':
    # Defaults to 5000 (the Workspace port); set PORT to use another.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)),
            debug=True)
