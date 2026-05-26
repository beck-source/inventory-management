"""
Tests for the Restocking API endpoints (restock orders) and the
unit_cost field added to demand forecasts.
"""
from datetime import datetime

import pytest


@pytest.fixture
def sample_restock_payload():
    """A valid create-restock-order request body."""
    return {
        "items": [
            {"sku": "WDG-001", "name": "Industrial Widget Type A", "quantity": 150, "unit_price": 12.5},
            {"sku": "GSK-203", "name": "High-Temperature Gasket", "quantity": 100, "unit_price": 4.25},
        ],
        "budget": 3000,
    }


class TestDemandUnitCost:
    """The demand forecast must now expose unit_cost for budget math."""

    def test_demand_forecasts_have_unit_cost(self, client):
        """Every demand forecast has a positive numeric unit_cost."""
        response = client.get("/api/demand")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0
        for forecast in data:
            assert "unit_cost" in forecast, f"{forecast['item_sku']} missing unit_cost"
            assert isinstance(forecast["unit_cost"], (int, float))
            assert forecast["unit_cost"] > 0


class TestRestockOrderEndpoints:
    """Test suite for the restock-order create/list endpoints."""

    def test_get_restock_orders_returns_list(self, client):
        """GET returns a list (the in-memory store)."""
        response = client.get("/api/restock-orders")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_restock_order(self, client, sample_restock_payload):
        """POST creates an Order-shaped restock order."""
        response = client.post("/api/restock-orders", json=sample_restock_payload)
        assert response.status_code == 200

        order = response.json()
        # Order-model shape
        for field in ("id", "order_number", "customer", "items", "status",
                      "order_date", "expected_delivery", "total_value"):
            assert field in order

        assert order["order_number"].startswith("RST-")
        assert order["status"] == "Processing"
        assert order["customer"] == "Internal Restock"
        assert len(order["items"]) == 2

    def test_restock_total_value_calculation(self, client, sample_restock_payload):
        """total_value equals sum(quantity * unit_price)."""
        response = client.post("/api/restock-orders", json=sample_restock_payload)
        order = response.json()

        expected = sum(i["quantity"] * i["unit_price"] for i in sample_restock_payload["items"])
        assert abs(order["total_value"] - expected) < 0.01

    def test_restock_lead_time_is_14_days(self, client, sample_restock_payload):
        """expected_delivery is 14 days after order_date (the lead time)."""
        response = client.post("/api/restock-orders", json=sample_restock_payload)
        order = response.json()

        order_date = datetime.fromisoformat(order["order_date"])
        expected_delivery = datetime.fromisoformat(order["expected_delivery"])
        assert (expected_delivery - order_date).days == 14

    def test_created_order_appears_in_list(self, client, sample_restock_payload):
        """A created restock order is returned by the GET endpoint."""
        created = client.post("/api/restock-orders", json=sample_restock_payload).json()

        listed = client.get("/api/restock-orders").json()
        numbers = [o["order_number"] for o in listed]
        assert created["order_number"] in numbers

    def test_restock_orders_separate_from_regular_orders(self, client, sample_restock_payload):
        """Restock orders must not leak into the main /api/orders list."""
        client.post("/api/restock-orders", json=sample_restock_payload)

        orders = client.get("/api/orders").json()
        assert not any(o["id"].startswith("RST-") for o in orders)
        assert not any(o["order_number"].startswith("RST-") for o in orders)

    def test_create_restock_order_validation_error(self, client):
        """Missing required item fields returns a 422 validation error."""
        bad_payload = {"items": [{"sku": "WDG-001"}]}  # missing name/quantity/unit_price
        response = client.post("/api/restock-orders", json=bad_payload)
        assert response.status_code == 422
