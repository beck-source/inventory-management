"""
Tests for the orders API endpoint (/api/orders).

Covers:
  - Empty filter set returns all orders.
  - Month filter returns only matching orders.
  - Quarter filter expands to Jan/Feb/Mar.
  - Status filter restricts results.
  - Combined warehouse + category + status filters compose correctly.
  - GET /api/orders/{invalid_id} returns 404.
  - Fuzz: random filter combos yield valid, schema-compliant, filter-consistent lists.
"""
import random

import pytest


# Required fields that every order in the response must have.
ORDER_REQUIRED_FIELDS = [
    "id",
    "order_number",
    "customer",
    "items",
    "status",
    "order_date",
    "expected_delivery",
    "total_value",
]

# Valid filter values drawn from the dataset.
VALID_WAREHOUSES = ["London", "San Francisco", "Tokyo"]
VALID_CATEGORIES = ["Actuators", "Circuit Boards", "Controllers", "Power Supplies", "Sensors"]
VALID_STATUSES = ["Backordered", "Delivered", "Processing", "Shipped"]


def _assert_order_schema(order: dict) -> None:
    """Assert that a single order dict has all required fields with valid types."""
    for field in ORDER_REQUIRED_FIELDS:
        assert field in order, f"Order missing required field '{field}': {order.get('order_number')}"

    assert isinstance(order["id"], str)
    assert isinstance(order["order_number"], str)
    assert isinstance(order["customer"], str)
    assert isinstance(order["items"], list)
    assert isinstance(order["status"], str)
    assert isinstance(order["order_date"], str)
    assert isinstance(order["expected_delivery"], str)
    assert isinstance(order["total_value"], (int, float))
    assert order["total_value"] >= 0, (
        f"total_value must be non-negative, got {order['total_value']}"
    )


class TestOrdersFilters:
    """Test GET /api/orders filtering behaviour."""

    def test_no_filters_returns_all_orders(self, client):
        """Empty filter set returns the complete orders list.

        Verifies that calling the endpoint without any query parameters returns
        all orders, and that each item conforms to the expected schema.
        """
        response = client.get("/api/orders")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        for order in data:
            _assert_order_schema(order)

    def test_month_filter_returns_only_january_orders(self, client):
        """?month=2025-01 returns only orders whose order_date is in January 2025.

        A bug here would return orders from other months — for example if the
        filter logic checked the wrong field or used substring matching incorrectly.
        """
        response = client.get("/api/orders?month=2025-01")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, "Expected at least one January 2025 order in dataset"

        for order in data:
            assert "2025-01" in order["order_date"], (
                f"Order {order['order_number']} has order_date '{order['order_date']}' "
                f"but month filter was 2025-01"
            )

    def test_quarter_filter_returns_q1_months(self, client):
        """?month=Q1-2025 returns orders from January, February, and March 2025.

        Quarter expansion is a real parsing path — a bug here would either return
        nothing (unrecognised quarter key) or return all orders (guard clause skipped).
        """
        response = client.get("/api/orders?month=Q1-2025")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, "Expected Q1-2025 to match orders in the dataset"

        q1_months = {"2025-01", "2025-02", "2025-03"}
        for order in data:
            order_month = order["order_date"][:7]
            assert order_month in q1_months, (
                f"Order {order['order_number']} has order_date '{order['order_date']}' "
                f"which is outside Q1-2025"
            )

    def test_status_filter_delivered_returns_only_delivered(self, client):
        """?status=Delivered returns only orders with status 'Delivered'.

        A bug here would return orders of other statuses, breaking the
        dashboard pending-orders count and the orders view filtering.
        """
        response = client.get("/api/orders?status=Delivered")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, "Expected delivered orders in dataset"

        for order in data:
            assert order["status"] == "Delivered", (
                f"Order {order['order_number']} has status '{order['status']}' "
                f"but status filter was 'Delivered'"
            )

    def test_combined_filters_compose_correctly(self, client):
        """?warehouse=X&category=Y&status=Z applies all three constraints.

        Tests the composition of three independent filters. A bug here would
        typically arise when a filter early-exits or short-circuits on the 'all'
        sentinel but the logic also skips the remaining explicit filters.
        """
        response = client.get(
            "/api/orders?warehouse=Tokyo&category=Actuators&status=Delivered"
        )
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        for order in data:
            assert order.get("warehouse") == "Tokyo", (
                f"Expected warehouse=Tokyo, got '{order.get('warehouse')}'"
            )
            assert order.get("category", "").lower() == "actuators", (
                f"Expected category=Actuators, got '{order.get('category')}'"
            )
            assert order["status"] == "Delivered", (
                f"Expected status=Delivered, got '{order['status']}'"
            )

    def test_all_filter_sentinel_returns_same_as_no_filter(self, client):
        """Passing warehouse=all&category=all&status=all returns the full dataset.

        The 'all' sentinel is a special no-op value. This test catches the bug
        where the sentinel is not recognised and is instead used as a literal
        filter value, returning zero results.
        """
        response_explicit_all = client.get(
            "/api/orders?warehouse=all&category=all&status=all&month=all"
        )
        response_no_filter = client.get("/api/orders")

        assert response_explicit_all.status_code == 200
        assert response_no_filter.status_code == 200

        assert len(response_explicit_all.json()) == len(response_no_filter.json()), (
            "Passing 'all' for all filters should return same count as no filters"
        )


class TestOrdersById:
    """Test GET /api/orders/{order_id}."""

    def test_valid_id_returns_order(self, client):
        """Fetching a known order ID returns the correct order document."""
        all_orders = client.get("/api/orders").json()
        assert len(all_orders) > 0

        first_id = all_orders[0]["id"]
        response = client.get(f"/api/orders/{first_id}")
        assert response.status_code == 200

        order = response.json()
        assert order["id"] == first_id

    def test_invalid_id_returns_404(self, client):
        """GET /api/orders/{invalid_id} returns 404 with a detail message.

        This catches the missing guard clause — without it, the endpoint would
        either raise an unhandled exception (500) or return None incorrectly.
        """
        response = client.get("/api/orders/nonexistent-order-id-999")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data, "404 response must include a 'detail' field"


class TestOrdersFuzz:
    """Fuzz-style tests: random filter combos must always return valid order lists."""

    def test_random_filter_combos_return_valid_schema(self, client):
        """For 10 random filter combinations, verify every response is a valid
        list where each item has all required fields and respects the applied
        status filter.

        Catches: schema regressions introduced when new fields are added/removed,
        filter interactions that crash the server, and status filter leakage.
        """
        random.seed(42)

        # Build a pool of 10 combos; None means 'omit the parameter' (server default).
        warehouse_pool = VALID_WAREHOUSES + [None]
        category_pool = VALID_CATEGORIES + [None]
        status_pool = VALID_STATUSES + [None]
        month_pool = ["2025-01", "2025-06", "2025-12", "Q1-2025", "Q3-2025", None]

        for _ in range(10):
            warehouse = random.choice(warehouse_pool)
            category = random.choice(category_pool)
            status = random.choice(status_pool)
            month = random.choice(month_pool)

            params = {}
            if warehouse is not None:
                params["warehouse"] = warehouse
            if category is not None:
                params["category"] = category
            if status is not None:
                params["status"] = status
            if month is not None:
                params["month"] = month

            query = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"/api/orders?{query}" if query else "/api/orders"

            response = client.get(url)
            assert response.status_code == 200, (
                f"Expected 200 for params={params}, got {response.status_code}"
            )

            data = response.json()
            assert isinstance(data, list), f"Response must be a list for params={params}"

            for order in data:
                _assert_order_schema(order)

                # If status was specified, every returned order must match it.
                if status is not None:
                    assert order["status"].lower() == status.lower(), (
                        f"Filter status={status} but order has status={order['status']}"
                    )

                # If warehouse was specified, every returned order must match it.
                if warehouse is not None:
                    assert order.get("warehouse") == warehouse, (
                        f"Filter warehouse={warehouse} but order has warehouse={order.get('warehouse')}"
                    )
