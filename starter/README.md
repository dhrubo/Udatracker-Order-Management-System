# Udatracker

## Reflection

<!-- Draft: put this in your own words before submitting. -->

- **Design decision:** `OrderTracker` holds every business rule and contains no Flask code. It raises `OrderError` (a `ValueError`) or one of its subclasses, `DuplicateOrderError` and `OrderNotFoundError`. A single Flask error handler maps these to 400, 409 and 404, always with an `{"error": ...}` body. Each route stays a few lines long and never parses error messages. The cost is a small set of exception classes to maintain.
- **Testing insight:** `test_get_order_api_blank_id_returns_400` caught a gap. Once `get_order_by_id` started rejecting empty IDs, the GET route let that error escape as a 500. A unit test checking that the stored dict isn't modified also led me to copy the order before saving in `update_order_status`.
- **Next step:** Replace the in-memory store with SQLite behind the same four storage methods, so orders survive a restart. Then add delete and the `delivered`/`cancelled` statuses to the frontend.

## Project structure

```
.
├── backend
│   ├── __init__.py
│   ├── app.py                  # Flask routes and JSON error handlers
│   ├── in_memory_storage.py    # dict-backed storage (resets on restart)
│   ├── order_tracker.py        # business logic, no Flask code
│   ├── requirements.txt
│   └── tests
│       ├── __init__.py
│       ├── test_api.py             # integration tests through Flask
│       ├── test_in_memory_storage.py
│       └── test_order_tracker.py   # unit tests with mocked storage
├── frontend
│   ├── css
│   │   └── style.css
│   ├── index.html
│   └── js
│       └── script.js
├── .dockerignore
├── Dockerfile
├── pytest.ini
└── README.md
```

## Running the project

Run every command from this `starter/` directory. If you run `pytest` from inside `backend/`, the `backend` imports fail.

```bash
python3 -m venv backend/venv && source backend/venv/bin/activate
pip install -r backend/requirements.txt
pytest                      # 93 tests: 58 OrderTracker, 3 storage, 32 API
python -m backend.app       # http://127.0.0.1:5000/
```

If port 5000 is in use (on macOS, AirPlay Receiver often takes it), choose another port: `PORT=8000 python -m backend.app`.

### With Docker (optional, local only)

```bash
docker build -t udatracker .
docker run --rm -p 5000:5000 udatracker     # http://127.0.0.1:5000/
docker run --rm udatracker pytest           # run the tests in the container
```

## API reference

| Method | Path | Success | Errors |
| --- | --- | --- | --- |
| `POST` | `/api/orders` | `201` + created order | `400` invalid/missing fields or non-JSON body, `409` duplicate ID |
| `GET` | `/api/orders/<order_id>` | `200` + order | `400` blank ID, `404` not found |
| `PUT` | `/api/orders/<order_id>/status` | `200` + updated order | `400` invalid/missing `new_status`, `404` not found |
| `DELETE` | `/api/orders/<order_id>` | `200` + deleted order | `404` not found |
| `GET` | `/api/orders` | `200` + list of all orders | none |
| `GET` | `/api/orders?status=<s>&customer_id=<c>` | `200` + orders matching every filter given | `400` empty or invalid filter |

- **Order fields:** `order_id`, `item_name`, `customer_id` (non-empty strings), `quantity` (positive integer) and `status`.
- **Valid statuses:** `pending` (the default), `processing`, `shipped`, `delivered` and `cancelled`.
- **Errors:** every error, including 405 and unknown `/api/...` routes, returns JSON shaped like `{"error": "Order with ID 'NOPE' not found."}`.

### Sample requests

```bash
# Create an order -> 201
curl -X POST http://127.0.0.1:5000/api/orders \
     -H "Content-Type: application/json" \
     -d '{"order_id": "CURL001", "item_name": "Headphones", "quantity": 1, "customer_id": "CUST123"}'

# Fetch it -> 200 (or 404 if it doesn't exist)
curl http://127.0.0.1:5000/api/orders/CURL001

# Update its status -> 200 with the updated order
curl -X PUT http://127.0.0.1:5000/api/orders/CURL001/status \
     -H "Content-Type: application/json" \
     -d '{"new_status": "shipped"}'

# List all orders, or filter by status and/or customer -> 200
curl http://127.0.0.1:5000/api/orders
curl "http://127.0.0.1:5000/api/orders?status=shipped&customer_id=CUST123"

# Delete it -> 200 with the deleted order
curl -X DELETE http://127.0.0.1:5000/api/orders/CURL001
```
