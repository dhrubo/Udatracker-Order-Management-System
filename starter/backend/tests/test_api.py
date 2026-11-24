import pytest
from backend.app import app, in_memory_storage

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['DEBUG'] = False
    in_memory_storage.clear()
    with app.test_client() as client:
        yield client

def test_add_order_api_success(client):
    order_data = {
        "order_id": "API001", "item_name": "API Laptop", "quantity": 1, "customer_id": "APICUST001"
    }
    response = client.post('/api/orders', json=order_data)
    assert response.status_code == 201
    assert response.json['order_id'] == "API001"

def test_get_order_api_success(client):
    client.post('/api/orders', json={
        "order_id": "GET001", "item_name": "Test Item", "quantity": 1, "customer_id": "C1"
    })
    response = client.get('/api/orders/GET001')
    assert response.status_code == 200
    assert response.json['order_id'] == "GET001"

def test_get_order_api_not_found(client):
    response = client.get('/api/orders/NONEXISTENT')
    assert response.status_code == 404

def test_update_order_status_api_success(client):
    client.post('/api/orders', json={
        "order_id": "UPDATE001", "item_name": "Test Item", "quantity": 1, "customer_id": "C1"
    })
    response = client.put('/api/orders/UPDATE001/status', json={"new_status": "shipped"})
    assert response.status_code == 200
    assert response.json['status'] == "shipped"

def test_list_all_orders_api_with_data(client):
    client.post('/api/orders', json={"order_id": "LST001", "item_name": "Item A", "quantity": 1, "customer_id": "C1"})
    client.post('/api/orders', json={"order_id": "LST002", "item_name": "Item B", "quantity": 2, "customer_id": "C2"})
    response = client.get('/api/orders')
    assert response.status_code == 200
    assert len(response.json) == 2

def test_list_orders_by_status_api_matching(client):
    client.post('/api/orders', json={"order_id": "S001", "item_name": "A", "quantity": 1, "customer_id": "C1", "status": "pending"})
    client.post('/api/orders', json={"order_id": "S002", "item_name": "B", "quantity": 2, "customer_id": "C2", "status": "shipped"})
    response = client.get('/api/orders?status=pending')
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['order_id'] == "S001"


# --- Additional tests: error paths and edge cases ---
VALID_ORDER = {
    "order_id": "ERR001", "item_name": "Item", "quantity": 1,
    "customer_id": "C1",
}


def put_status(client, order_id, new_status):
    """Sends a status update for order_id and returns the response."""
    return client.put(f'/api/orders/{order_id}/status',
                      json={"new_status": new_status})


def test_add_order_api_returns_full_order_with_default_status(client):
    response = client.post('/api/orders', json=VALID_ORDER)
    assert response.status_code == 201
    assert response.json == {**VALID_ORDER, "status": "pending"}


def test_add_order_api_duplicate_returns_409(client):
    client.post('/api/orders', json=VALID_ORDER)
    response = client.post('/api/orders', json=VALID_ORDER)
    assert response.status_code == 409
    assert "already exists" in response.json['error']


@pytest.mark.parametrize(
    "missing_field", ["order_id", "item_name", "quantity", "customer_id"])
def test_add_order_api_missing_field_returns_400(client, missing_field):
    payload = {k: v for k, v in VALID_ORDER.items() if k != missing_field}
    response = client.post('/api/orders', json=payload)
    assert response.status_code == 400
    assert missing_field in response.json['error']


def test_add_order_api_invalid_quantity_returns_400(client):
    payload = {**VALID_ORDER, "quantity": 0}
    response = client.post('/api/orders', json=payload)
    assert response.status_code == 400
    assert "Quantity" in response.json['error']


def test_add_order_api_non_json_body_returns_400(client):
    response = client.post('/api/orders', data="not json",
                           content_type="text/plain")
    assert response.status_code == 400
    assert "error" in response.json


def test_get_order_api_not_found_returns_error_message(client):
    response = client.get('/api/orders/NONEXISTENT')
    assert "NONEXISTENT" in response.json['error']


def test_get_order_api_blank_id_returns_400(client):
    response = client.get('/api/orders/%20')
    assert response.status_code == 400
    assert "order_id" in response.json['error']


def test_update_order_status_api_persists_change(client):
    client.post('/api/orders', json=VALID_ORDER)
    put_status(client, "ERR001", "processing")
    response = client.get('/api/orders/ERR001')
    assert response.json['status'] == "processing"


def test_update_order_status_api_accepts_delivered(client):
    client.post('/api/orders', json=VALID_ORDER)
    response = put_status(client, "ERR001", "delivered")
    assert response.status_code == 200
    assert response.json['status'] == "delivered"


def test_update_order_status_api_not_found_returns_404(client):
    response = put_status(client, "NONEXISTENT", "shipped")
    assert response.status_code == 404
    assert "not found" in response.json['error']


def test_update_order_status_api_invalid_status_returns_400(client):
    client.post('/api/orders', json=VALID_ORDER)
    response = put_status(client, "ERR001", "lost")
    assert response.status_code == 400
    assert "Invalid status" in response.json['error']


def test_update_order_status_api_missing_new_status_returns_400(client):
    client.post('/api/orders', json=VALID_ORDER)
    response = client.put('/api/orders/ERR001/status', json={})
    assert response.status_code == 400
    assert "new_status" in response.json['error']


def test_list_orders_api_empty_returns_empty_list(client):
    response = client.get('/api/orders')
    assert response.status_code == 200
    assert response.json == []


@pytest.mark.parametrize("query", ["status=bogus", "status="])
def test_list_orders_api_empty_or_invalid_status_returns_400(client, query):
    response = client.get(f'/api/orders?{query}')
    assert response.status_code == 400
    assert "Invalid status" in response.json['error']


# --- Filtering by customer: GET /api/orders?customer_id=<id> ---
SEED_ORDERS = [
    ("F1", "C1", "pending"),
    ("F2", "C2", "pending"),
    ("F3", "C2", "shipped"),
]


@pytest.fixture
def seeded_client(client):
    """A client whose store holds orders for two customers."""
    for order_id, customer_id, status in SEED_ORDERS:
        client.post('/api/orders', json={
            **VALID_ORDER, "order_id": order_id,
            "customer_id": customer_id, "status": status})
    return client


def order_ids(response):
    """Returns the sorted order IDs in a list response."""
    return sorted(order["order_id"] for order in response.json)


def test_list_orders_api_filters_by_customer(seeded_client):
    response = seeded_client.get('/api/orders?customer_id=C2')
    assert response.status_code == 200
    assert order_ids(response) == ["F2", "F3"]


def test_list_orders_api_combines_customer_and_status(seeded_client):
    url = '/api/orders?customer_id=C2&status=pending'
    response = seeded_client.get(url)
    assert response.status_code == 200
    assert order_ids(response) == ["F2"]


def test_list_orders_api_empty_customer_filter_returns_400(seeded_client):
    response = seeded_client.get('/api/orders?customer_id=')
    assert response.status_code == 400
    assert "customer_id" in response.json['error']


# --- DELETE /api/orders/<order_id> ---
def test_delete_order_api_returns_deleted_order(client):
    client.post('/api/orders', json=VALID_ORDER)
    response = client.delete('/api/orders/ERR001')
    assert response.status_code == 200
    assert response.json == {**VALID_ORDER, "status": "pending"}


def test_delete_order_api_removes_the_order(client):
    client.post('/api/orders', json=VALID_ORDER)
    client.delete('/api/orders/ERR001')
    assert client.get('/api/orders/ERR001').status_code == 404
    assert client.get('/api/orders').json == []


def test_delete_order_api_not_found_returns_404(client):
    response = client.delete('/api/orders/NONEXISTENT')
    assert response.status_code == 404
    assert "not found" in response.json['error']


# --- Consistent JSON errors from the central error handlers ---
def test_unsupported_method_returns_json_405(client):
    response = client.patch('/api/orders/ERR001')
    assert response.status_code == 405
    assert "error" in response.json


def test_unknown_api_route_returns_json_404(client):
    response = client.get('/api/unknown')
    assert response.status_code == 404
    assert "error" in response.json
