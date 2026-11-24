# Unit tests for OrderTracker (backend/order_tracker.py).
# Storage is a Mock, so these tests check only the business rules.
# Run from starter/: pytest backend/tests/test_order_tracker.py

from unittest.mock import Mock

import pytest

from ..order_tracker import OrderTracker


# --- Fixtures for Unit Tests ---
@pytest.fixture
def mock_storage():
    """
    Provides a mock storage object for tests.
    This mock will be configured to simulate various storage behaviors.
    """
    mock = Mock()
    # By default, mock get_order to return None (no order found)
    mock.get_order.return_value = None
    # By default, mock get_all_orders to return an empty dict
    mock.get_all_orders.return_value = {}
    return mock


@pytest.fixture
def order_tracker(mock_storage):
    """
    Provides an OrderTracker instance initialized with the mock_storage.
    """
    return OrderTracker(mock_storage)


@pytest.fixture
def mixed_orders(mock_storage):
    """Stores three orders spread across two statuses and two customers."""
    orders = {order["order_id"]: order for order in [
        make_order("ORD001", customer_id="CUST001", status="pending"),
        make_order("ORD002", customer_id="CUST002", status="shipped"),
        make_order("ORD003", customer_id="CUST002", status="pending"),
    ]}
    mock_storage.get_all_orders.return_value = orders
    return orders


# --- Helpers ---
ALL_STATUSES = ["pending", "processing", "shipped", "delivered", "cancelled"]
EMPTY_IDS = ["", "   ", None]


def make_order(order_id="ORD001", item_name="Laptop", quantity=1,
               customer_id="CUST001", status="pending"):
    """Builds an order dict shaped the way OrderTracker stores it."""
    return {
        "order_id": order_id,
        "item_name": item_name,
        "quantity": quantity,
        "customer_id": customer_id,
        "status": status,
    }


def sort_by_id(orders):
    """Sorts orders by ID so comparisons don't depend on result order."""
    return sorted(orders, key=lambda order: order["order_id"])


# --- Construction ---
def test_init_rejects_storage_missing_required_methods():
    """OrderTracker refuses a storage object without the storage API."""
    with pytest.raises(TypeError, match="save_order"):
        OrderTracker(object())


# Storage without delete_order is rejected, since deleting needs it.
def test_init_requires_storage_to_support_deletion():
    storage = Mock(spec=["save_order", "get_order", "get_all_orders"])

    with pytest.raises(TypeError, match="delete_order"):
        OrderTracker(storage)


# --- add_order ---
def test_add_order_successfully(order_tracker, mock_storage):
    """Tests adding a new order with default 'pending' status."""
    order_tracker.add_order("ORD001", "Laptop", 1, "CUST001")

    # We expect save_order to be called once
    mock_storage.save_order.assert_called_once()


# The saved order has every field, and its status defaults to pending.
def test_add_order_stores_details_with_default_pending_status(
        order_tracker, mock_storage):
    order_tracker.add_order("ORD001", "Laptop", 1, "CUST001")

    mock_storage.save_order.assert_called_once_with("ORD001", make_order())


# add_order returns the order it created.
def test_add_order_returns_the_created_order(order_tracker):
    result = order_tracker.add_order("ORD001", "Laptop", 1, "CUST001")

    assert result == make_order()


# Each of the five valid statuses can be set when adding an order.
@pytest.mark.parametrize("status", ALL_STATUSES)
def test_add_order_accepts_explicit_status(
        order_tracker, mock_storage, status):
    order_tracker.add_order("ORD002", "Mouse", 2, "CUST002", status=status)

    saved_order = mock_storage.save_order.call_args.args[1]
    assert saved_order["status"] == status


def test_add_order_raises_error_if_exists(order_tracker, mock_storage):
    """Tests that adding an order with a duplicate ID raises a ValueError."""
    # Simulate that the storage finds an existing order
    mock_storage.get_order.return_value = {"order_id": "ORD_EXISTING"}

    with pytest.raises(ValueError,
                       match="Order with ID 'ORD_EXISTING' already exists."):
        order_tracker.add_order("ORD_EXISTING", "New Item", 1, "CUST001")

    mock_storage.save_order.assert_not_called()


# Zero, negative, decimal, text, None and True are all bad quantities.
@pytest.mark.parametrize("quantity", [0, -1, 1.5, "3", None, True])
def test_add_order_rejects_invalid_quantity(
        order_tracker, mock_storage, quantity):
    with pytest.raises(ValueError,
                       match="Quantity must be a positive integer."):
        order_tracker.add_order("ORD003", "Laptop", quantity, "CUST001")

    mock_storage.save_order.assert_not_called()


# A blank or missing order ID, item name or customer ID is rejected.
@pytest.mark.parametrize("field, value", [
    ("order_id", ""),
    ("order_id", "   "),
    ("order_id", None),
    ("item_name", ""),
    ("customer_id", ""),
])
def test_add_order_rejects_missing_text_fields(
        order_tracker, mock_storage, field, value):
    args = {"order_id": "ORD004", "item_name": "Laptop", "quantity": 1,
            "customer_id": "CUST001"}
    args[field] = value

    with pytest.raises(ValueError,
                       match=f"{field} must be a non-empty string."):
        order_tracker.add_order(**args)

    mock_storage.save_order.assert_not_called()


# A status outside the allowed list is rejected.
def test_add_order_rejects_invalid_status(order_tracker, mock_storage):
    with pytest.raises(ValueError, match="Invalid status 'lost'"):
        order_tracker.add_order("ORD005", "Laptop", 1, "CUST001",
                                status="lost")

    mock_storage.save_order.assert_not_called()


# --- get_order_by_id ---
# Looking up an ID returns the matching order from storage.
def test_get_order_by_id_returns_existing_order(order_tracker, mock_storage):
    mock_storage.get_order.return_value = make_order()

    result = order_tracker.get_order_by_id("ORD001")

    assert result == make_order()
    mock_storage.get_order.assert_called_once_with("ORD001")


# An unknown ID returns None instead of raising an error.
def test_get_order_by_id_returns_none_when_not_found(
        order_tracker, mock_storage):
    # mock_storage.get_order returns None by default
    assert order_tracker.get_order_by_id("MISSING") is None
    mock_storage.get_order.assert_called_once_with("MISSING")


# A blank ID raises an error before storage is checked.
@pytest.mark.parametrize("order_id", EMPTY_IDS)
def test_get_order_by_id_rejects_empty_id(
        order_tracker, mock_storage, order_id):
    with pytest.raises(ValueError,
                       match="order_id must be a non-empty string."):
        order_tracker.get_order_by_id(order_id)

    mock_storage.get_order.assert_not_called()


# --- update_order_status ---
# The new status is saved back to storage.
def test_update_order_status_saves_new_status(order_tracker, mock_storage):
    mock_storage.get_order.return_value = make_order(status="pending")

    order_tracker.update_order_status("ORD001", "shipped")

    mock_storage.save_order.assert_called_once_with(
        "ORD001", make_order(status="shipped"))


# The method returns the order with its new status.
def test_update_order_status_returns_updated_order(
        order_tracker, mock_storage):
    mock_storage.get_order.return_value = make_order(status="pending")

    result = order_tracker.update_order_status("ORD001", "processing")

    assert result == make_order(status="processing")


# The order from storage is copied, not changed in place.
def test_update_order_status_does_not_mutate_stored_dict(
        order_tracker, mock_storage):
    original = make_order(status="pending")
    mock_storage.get_order.return_value = original

    order_tracker.update_order_status("ORD001", "delivered")

    assert original["status"] == "pending"


# Updating an unknown order raises an error and saves nothing.
def test_update_order_status_raises_error_if_order_not_found(
        order_tracker, mock_storage):
    with pytest.raises(ValueError,
                       match="Order with ID 'MISSING' not found."):
        order_tracker.update_order_status("MISSING", "shipped")

    mock_storage.save_order.assert_not_called()


# An invalid status raises an error before storage is read.
def test_update_order_status_rejects_invalid_status_before_storage_read(
        order_tracker, mock_storage):
    with pytest.raises(ValueError, match="Invalid status 'teleported'"):
        order_tracker.update_order_status("ORD001", "teleported")

    # Fail fast: an invalid status never touches storage
    mock_storage.get_order.assert_not_called()
    mock_storage.save_order.assert_not_called()


# A blank ID raises an error before storage is touched.
@pytest.mark.parametrize("order_id", EMPTY_IDS)
def test_update_order_status_rejects_empty_id(
        order_tracker, mock_storage, order_id):
    with pytest.raises(ValueError,
                       match="order_id must be a non-empty string."):
        order_tracker.update_order_status(order_id, "shipped")

    mock_storage.get_order.assert_not_called()
    mock_storage.save_order.assert_not_called()


# --- list_all_orders ---
# No orders in storage gives an empty list.
def test_list_all_orders_returns_empty_list_when_no_orders(order_tracker):
    # mock_storage.get_all_orders returns {} by default
    assert order_tracker.list_all_orders() == []


# Every stored order comes back, as a list.
def test_list_all_orders_returns_every_order_as_a_list(
        order_tracker, mock_storage):
    first = make_order("ORD001", status="pending")
    second = make_order("ORD002", status="shipped")
    mock_storage.get_all_orders.return_value = {
        "ORD001": first, "ORD002": second}

    result = order_tracker.list_all_orders()

    assert isinstance(result, list)
    # The order of results doesn't matter
    assert sort_by_id(result) == [first, second]


# --- list_orders_by_status ---
# Only orders with the requested status are returned.
def test_list_orders_by_status_returns_only_matching_orders(
        order_tracker, mixed_orders):
    result = order_tracker.list_orders_by_status("pending")

    expected = [mixed_orders["ORD001"], mixed_orders["ORD003"]]
    assert sort_by_id(result) == expected


# A valid status that no order has gives an empty list.
def test_list_orders_by_status_returns_empty_list_when_none_match(
        order_tracker, mixed_orders):
    assert order_tracker.list_orders_by_status("processing") == []


# Empty storage gives an empty list.
def test_list_orders_by_status_returns_empty_list_for_empty_storage(
        order_tracker):
    # mock_storage.get_all_orders returns {} by default
    assert order_tracker.list_orders_by_status("pending") == []


# An unknown, empty or missing status raises an error.
@pytest.mark.parametrize("status", ["archived", "", None])
def test_list_orders_by_status_rejects_empty_or_invalid_status(
        order_tracker, mixed_orders, status):
    with pytest.raises(ValueError, match="Invalid status"):
        order_tracker.list_orders_by_status(status)


# --- filter_orders ---
# Filtering by customer returns only that customer's orders.
def test_filter_orders_by_customer_returns_only_their_orders(
        order_tracker, mixed_orders):
    result = order_tracker.filter_orders(customer_id="CUST002")

    expected = [mixed_orders["ORD002"], mixed_orders["ORD003"]]
    assert sort_by_id(result) == expected


# Status and customer filters can be combined.
def test_filter_orders_combines_status_and_customer(
        order_tracker, mixed_orders):
    result = order_tracker.filter_orders(status="pending",
                                         customer_id="CUST002")

    assert result == [mixed_orders["ORD003"]]


# No filters at all returns every order.
def test_filter_orders_with_no_filters_returns_all_orders(
        order_tracker, mixed_orders):
    result = order_tracker.filter_orders()

    assert sort_by_id(result) == list(mixed_orders.values())


# An unknown customer just gives an empty list.
def test_filter_orders_returns_empty_list_for_unknown_customer(
        order_tracker, mixed_orders):
    assert order_tracker.filter_orders(customer_id="NOBODY") == []


# An unknown or empty status filter raises an error.
@pytest.mark.parametrize("status", ["archived", ""])
def test_filter_orders_rejects_empty_or_invalid_status(
        order_tracker, mixed_orders, status):
    with pytest.raises(ValueError, match="Invalid status"):
        order_tracker.filter_orders(status=status)


# A blank customer filter raises an error.
@pytest.mark.parametrize("customer_id", ["", "   "])
def test_filter_orders_rejects_empty_customer_id(
        order_tracker, mixed_orders, customer_id):
    with pytest.raises(ValueError,
                       match="customer_id must be a non-empty string."):
        order_tracker.filter_orders(customer_id=customer_id)


# --- delete_order ---
# Deleting removes the order from storage.
def test_delete_order_removes_it_from_storage(order_tracker, mock_storage):
    mock_storage.get_order.return_value = make_order()

    order_tracker.delete_order("ORD001")

    mock_storage.delete_order.assert_called_once_with("ORD001")


# delete_order returns the order it removed.
def test_delete_order_returns_the_deleted_order(order_tracker, mock_storage):
    mock_storage.get_order.return_value = make_order()

    assert order_tracker.delete_order("ORD001") == make_order()


# Deleting an unknown order raises an error and deletes nothing.
def test_delete_order_raises_error_if_order_not_found(
        order_tracker, mock_storage):
    with pytest.raises(ValueError,
                       match="Order with ID 'MISSING' not found."):
        order_tracker.delete_order("MISSING")

    mock_storage.delete_order.assert_not_called()


# A blank ID raises an error before storage is touched.
@pytest.mark.parametrize("order_id", EMPTY_IDS)
def test_delete_order_rejects_empty_id(
        order_tracker, mock_storage, order_id):
    with pytest.raises(ValueError,
                       match="order_id must be a non-empty string."):
        order_tracker.delete_order(order_id)

    mock_storage.get_order.assert_not_called()
    mock_storage.delete_order.assert_not_called()
