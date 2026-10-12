"""
Tests for the restock order endpoint (POST /api/orders/restock) and the
unit_cost field added to demand forecasts.
"""
from datetime import datetime, timedelta

import pytest


class TestRestockOrderEndpoint:
    """Test suite for the POST /api/orders/restock endpoint."""

    def _sample_payload(self):
        """A valid two-item restock request."""
        return {
            "items": [
                {"sku": "WDG-001", "name": "Industrial Widget Type A", "quantity": 150, "unit_price": 85.0},
                {"sku": "GSK-203", "name": "High-Temperature Gasket", "quantity": 100, "unit_price": 42.0},
            ]
        }

    def test_create_restock_order_success(self, client):
        """A valid restock order is created with Submitted status and a 14-day lead time."""
        response = client.post("/api/orders/restock", json=self._sample_payload())
        assert response.status_code == 200

        order = response.json()
        assert order["status"] == "Submitted"
        assert order["customer"] == "Internal Restock"
        assert order["lead_time_days"] == 14
        assert order["order_number"].startswith("ORD-2025-")
        assert len(order["items"]) == 2

    def test_restock_order_total_value_calculation(self, client):
        """total_value equals the sum of quantity * unit_price across items."""
        payload = self._sample_payload()
        response = client.post("/api/orders/restock", json=payload)
        assert response.status_code == 200

        order = response.json()
        expected_total = sum(item["quantity"] * item["unit_price"] for item in payload["items"])
        assert abs(order["total_value"] - expected_total) < 0.01

    def test_restock_order_lead_time_matches_dates(self, client):
        """expected_delivery is exactly 14 days after order_date."""
        response = client.post("/api/orders/restock", json=self._sample_payload())
        assert response.status_code == 200

        order = response.json()
        order_date = datetime.fromisoformat(order["order_date"])
        expected_delivery = datetime.fromisoformat(order["expected_delivery"])
        assert expected_delivery - order_date == timedelta(days=14)

    def test_restock_order_appears_in_orders_list(self, client):
        """A newly created restock order is returned by GET /api/orders."""
        create_response = client.post("/api/orders/restock", json=self._sample_payload())
        new_id = create_response.json()["id"]

        list_response = client.get("/api/orders")
        assert list_response.status_code == 200
        all_ids = [order["id"] for order in list_response.json()]
        assert new_id in all_ids

    def test_restock_order_retrievable_by_id(self, client):
        """A newly created restock order can be fetched by its id."""
        new_id = client.post("/api/orders/restock", json=self._sample_payload()).json()["id"]

        response = client.get(f"/api/orders/{new_id}")
        assert response.status_code == 200
        assert response.json()["id"] == new_id
        assert response.json()["status"] == "Submitted"

    def test_restock_order_empty_items_rejected(self, client):
        """An order with no items returns a 400 error."""
        response = client.post("/api/orders/restock", json={"items": []})
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_restock_order_missing_items_field(self, client):
        """A malformed payload (missing required items) returns a 422 validation error."""
        response = client.post("/api/orders/restock", json={"notes": "no items"})
        assert response.status_code == 422


class TestDemandForecastUnitCost:
    """Verify the unit_cost field added to demand forecasts."""

    def test_demand_forecasts_include_unit_cost(self, client):
        """Every demand forecast item exposes a non-negative numeric unit_cost."""
        response = client.get("/api/demand")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0
        for forecast in data:
            assert "unit_cost" in forecast
            assert isinstance(forecast["unit_cost"], (int, float))
            assert forecast["unit_cost"] >= 0
