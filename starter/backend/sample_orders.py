# Sample orders the app loads at startup, so the page isn't empty.
# Storage is in memory, so these come back fresh on every restart.

SAMPLE_ORDERS = [
    {"order_id": "ORD1001", "item_name": "Laptop", "quantity": 1,
     "customer_id": "CUST001", "status": "pending"},
    {"order_id": "ORD1002", "item_name": "Wireless Mouse", "quantity": 2,
     "customer_id": "CUST002", "status": "processing"},
    {"order_id": "ORD1003", "item_name": "Mechanical Keyboard", "quantity": 1,
     "customer_id": "CUST001", "status": "shipped"},
    {"order_id": "ORD1004", "item_name": "USB-C Hub", "quantity": 3,
     "customer_id": "CUST003", "status": "delivered"},
    {"order_id": "ORD1005", "item_name": "27-inch Monitor", "quantity": 2,
     "customer_id": "CUST002", "status": "pending"},
    {"order_id": "ORD1006", "item_name": "Noise-Cancelling Headphones",
     "quantity": 1, "customer_id": "CUST003", "status": "cancelled"},
]


def load_sample_orders(tracker):
    """Adds every sample order through the tracker, so each is validated."""
    for order in SAMPLE_ORDERS:
        tracker.add_order(**order)
