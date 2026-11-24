# Tests for the sample orders the app loads at startup
# (backend/sample_orders.py). These use the real tracker and storage.

from ..in_memory_storage import InMemoryStorage
from ..order_tracker import VALID_STATUSES, OrderTracker
from ..sample_orders import SAMPLE_ORDERS, load_sample_orders


def make_tracker():
    """Returns an OrderTracker backed by fresh, empty storage."""
    return OrderTracker(InMemoryStorage())


# Loading adds every sample order to an empty tracker.
def test_load_sample_orders_adds_every_order():
    tracker = make_tracker()

    load_sample_orders(tracker)

    loaded_ids = sorted(o["order_id"] for o in tracker.list_all_orders())
    assert loaded_ids == sorted(o["order_id"] for o in SAMPLE_ORDERS)


# Each loaded order keeps the exact details from the sample data.
def test_load_sample_orders_keeps_each_orders_details():
    tracker = make_tracker()

    load_sample_orders(tracker)

    for sample in SAMPLE_ORDERS:
        assert tracker.get_order_by_id(sample["order_id"]) == sample


# The samples use every status, so each filter has something to show.
def test_sample_orders_cover_every_status():
    assert {o["status"] for o in SAMPLE_ORDERS} == set(VALID_STATUSES)
