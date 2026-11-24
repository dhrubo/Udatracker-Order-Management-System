from ..in_memory_storage import InMemoryStorage


def test_delete_order_removes_the_order():
    storage = InMemoryStorage()
    storage.save_order("ORD001", {"order_id": "ORD001"})

    storage.delete_order("ORD001")

    assert storage.get_order("ORD001") is None
    assert storage.get_all_orders() == {}


def test_delete_order_leaves_other_orders_untouched():
    storage = InMemoryStorage()
    storage.save_order("ORD001", {"order_id": "ORD001"})
    storage.save_order("ORD002", {"order_id": "ORD002"})

    storage.delete_order("ORD001")

    assert storage.get_all_orders() == {"ORD002": {"order_id": "ORD002"}}


def test_delete_order_for_missing_id_does_nothing():
    storage = InMemoryStorage()

    storage.delete_order("MISSING")  # must not raise

    assert storage.get_all_orders() == {}
