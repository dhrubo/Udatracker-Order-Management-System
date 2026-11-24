# This module contains the OrderTracker class, which encapsulates the core
# business logic for managing orders. It has no Flask code: the API layer in
# app.py decides which HTTP status code each error maps to.

from typing import Optional


VALID_STATUSES = (
    "pending", "processing", "shipped", "delivered", "cancelled")


class OrderError(ValueError):
    """Raised when order input fails validation."""


class DuplicateOrderError(OrderError):
    """Raised when an order is added with an ID that already exists."""


class OrderNotFoundError(OrderError):
    """Raised when an operation targets an order ID that does not exist."""


class OrderTracker:
    """
    Manages customer orders, providing functionalities to add, update,
    and retrieve order information.
    """
    REQUIRED_STORAGE_METHODS = (
        "save_order", "get_order", "get_all_orders", "delete_order")

    def __init__(self, storage):
        for method in self.REQUIRED_STORAGE_METHODS:
            if not callable(getattr(storage, method, None)):
                raise TypeError(
                    f"Storage object must implement a callable "
                    f"'{method}' method.")
        self.storage = storage

    def add_order(self, order_id: str, item_name: str, quantity: int,
                  customer_id: str, status: str = "pending"):
        """Validates, saves and returns a new order."""
        _require_text("order_id", order_id)
        _require_text("item_name", item_name)
        _require_text("customer_id", customer_id)
        _require_positive_int(quantity)
        _require_valid_status(status)

        if self.storage.get_order(order_id):
            raise DuplicateOrderError(
                f"Order with ID '{order_id}' already exists.")

        order = {
            "order_id": order_id,
            "item_name": item_name,
            "quantity": quantity,
            "customer_id": customer_id,
            "status": status,
        }
        self.storage.save_order(order_id, order)
        return order

    def get_order_by_id(self, order_id: str):
        """Returns the order with this ID, or None if it does not exist."""
        _require_text("order_id", order_id)
        return self.storage.get_order(order_id)

    def update_order_status(self, order_id: str, new_status: str):
        """Changes an order's status and returns the updated order."""
        # Validate everything before touching storage (fail fast).
        _require_text("order_id", order_id)
        _require_valid_status(new_status)

        order = self._get_existing_order(order_id)
        # Save an updated copy rather than mutating the stored dict.
        updated_order = {**order, "status": new_status}
        self.storage.save_order(order_id, updated_order)
        return updated_order

    def delete_order(self, order_id: str):
        """Removes an order and returns what was deleted."""
        _require_text("order_id", order_id)

        order = self._get_existing_order(order_id)
        self.storage.delete_order(order_id)
        return order

    def list_all_orders(self):
        """Returns every order as a list of dicts."""
        return list(self.storage.get_all_orders().values())

    def list_orders_by_status(self, status: str):
        """Returns only the orders whose status matches."""
        _require_valid_status(status)
        return [order for order in self.list_all_orders()
                if order["status"] == status]

    def filter_orders(self, status: Optional[str] = None,
                      customer_id: Optional[str] = None):
        """
        Returns the orders that match every filter given. A filter left as
        None matches anything, so calling with no filters returns all orders.
        """
        if status is not None:
            _require_valid_status(status)
        if customer_id is not None:
            _require_text("customer_id", customer_id)

        return [
            order for order in self.list_all_orders()
            if (status is None or order["status"] == status)
            and (customer_id is None or order["customer_id"] == customer_id)
        ]

    def _get_existing_order(self, order_id: str):
        order = self.storage.get_order(order_id)
        if not order:
            raise OrderNotFoundError(
                f"Order with ID '{order_id}' not found.")
        return order


def _require_text(field: str, value):
    if not isinstance(value, str) or not value.strip():
        raise OrderError(f"{field} must be a non-empty string.")


def _require_positive_int(quantity):
    # bool is a subclass of int, so exclude it explicitly.
    if (isinstance(quantity, bool) or not isinstance(quantity, int)
            or quantity <= 0):
        raise OrderError("Quantity must be a positive integer.")


def _require_valid_status(status):
    if status not in VALID_STATUSES:
        allowed = ", ".join(VALID_STATUSES)
        raise OrderError(
            f"Invalid status '{status}'. Must be one of: {allowed}.")
