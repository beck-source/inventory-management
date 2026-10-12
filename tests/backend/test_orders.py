"""
Tests for the orders API endpoints, focused on the POST /api/orders write endpoint.

Note on isolation: the FastAPI app keeps orders in a single module-level list that
persists for the whole test session, so created orders accumulate across tests.
Every assertion here is therefore order-independent: we capture a GET baseline,
assert on deltas, and locate created orders by their unique order_number / id
rather than by absolute counts or list positions.
"""
import re
from datetime import datetime

import pytest


ORDER_NUMBER_PATTERN = re.compile(r"^ORD-\d{4}-\d{4}$")


def _valid_payload():
    """A well-formed create-order request with two positive-quantity line items."""
    return {
        "customer": "Internal Restock",
        "lead_time_days": 14,
        "items": [
            {"sku": "WDG-001", "name": "Industrial Widget Type A", "quantity": 10, "unit_price": 12.50},
            {"sku": "FLT-405", "name": "Oil Filter Cartridge", "quantity": 25, "unit_price": 6.20},
        ],
    }


class TestCreateOrder:
    """Test suite for the POST /api/orders endpoint."""

    def test_create_order_returns_201_and_submitted_status(self, client):
        """A valid POST returns 201 with a Submitted order and a well-formed number."""
        response = client.post("/api/orders", json=_valid_payload())
        assert response.status_code == 201

        order = response.json()
        assert order["status"] == "Submitted"
        assert ORDER_NUMBER_PATTERN.match(order["order_number"]), \
            f"order_number {order['order_number']!r} does not match ORD-YYYY-NNNN"
        assert order["actual_delivery"] is None
        assert order["customer"] == "Internal Restock"

    def test_create_order_total_value_calculation(self, client):
        """total_value equals the rounded sum of quantity * unit_price over items."""
        payload = _valid_payload()
        response = client.post("/api/orders", json=payload)
        assert response.status_code == 201

        order = response.json()
        expected_total = round(
            sum(item["quantity"] * item["unit_price"] for item in payload["items"]), 2
        )
        assert order["total_value"] == expected_total

    def test_create_order_expected_delivery_after_order_date(self, client):
        """expected_delivery is after order_date by exactly lead_time_days days."""
        payload = _valid_payload()
        payload["lead_time_days"] = 21
        response = client.post("/api/orders", json=payload)
        assert response.status_code == 201

        order = response.json()
        order_date = datetime.fromisoformat(order["order_date"])
        expected_delivery = datetime.fromisoformat(order["expected_delivery"])

        assert expected_delivery > order_date
        assert (expected_delivery - order_date).days == payload["lead_time_days"]

    def test_create_order_appears_in_get_orders(self, client):
        """A created order appears in a subsequent GET /api/orders (count +1)."""
        baseline = client.get("/api/orders?status=all&month=all").json()
        baseline_count = len(baseline)

        response = client.post("/api/orders", json=_valid_payload())
        assert response.status_code == 201
        created = response.json()

        after = client.get("/api/orders?status=all&month=all").json()
        assert len(after) == baseline_count + 1

        # Locate by unique id rather than position.
        match = next((o for o in after if o["id"] == created["id"]), None)
        assert match is not None, "created order not found in GET /api/orders"
        assert match["order_number"] == created["order_number"]
        assert match["status"] == "Submitted"

    def test_create_order_new_id_and_order_number_are_unique(self, client):
        """Two consecutive creates produce distinct ids and order numbers."""
        first = client.post("/api/orders", json=_valid_payload()).json()
        second = client.post("/api/orders", json=_valid_payload()).json()

        assert first["id"] != second["id"]
        assert first["order_number"] != second["order_number"]

    def test_create_order_empty_items_returns_400(self, client):
        """An order with no items is rejected with 400."""
        payload = _valid_payload()
        payload["items"] = []
        response = client.post("/api/orders", json=payload)
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_create_order_all_zero_quantity_returns_400(self, client):
        """An order whose items all have quantity 0 is rejected with 400."""
        payload = _valid_payload()
        for item in payload["items"]:
            item["quantity"] = 0
        response = client.post("/api/orders", json=payload)
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_create_order_mixed_quantities_persists_only_positive(self, client):
        """Only positive-quantity line items are persisted; total reflects them."""
        payload = {
            "customer": "Internal Restock",
            "lead_time_days": 7,
            "items": [
                {"sku": "WDG-001", "name": "Industrial Widget Type A", "quantity": 5, "unit_price": 12.50},
                {"sku": "GSK-203", "name": "High-Temperature Gasket", "quantity": 0, "unit_price": 8.75},
                {"sku": "FLT-405", "name": "Oil Filter Cartridge", "quantity": 3, "unit_price": 6.20},
            ],
        }
        response = client.post("/api/orders", json=payload)
        assert response.status_code == 201

        order = response.json()
        persisted_skus = {item["sku"] for item in order["items"]}
        assert persisted_skus == {"WDG-001", "FLT-405"}
        assert all(item["quantity"] > 0 for item in order["items"])

        expected_total = round(5 * 12.50 + 3 * 6.20, 2)
        assert order["total_value"] == expected_total

    def test_create_order_missing_required_field_returns_422(self, client):
        """A request missing a required field fails Pydantic validation with 422."""
        payload = _valid_payload()
        del payload["customer"]
        response = client.post("/api/orders", json=payload)
        assert response.status_code == 422
