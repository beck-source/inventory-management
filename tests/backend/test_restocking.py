"""
Tests for the restocking order submission endpoint.
"""
from datetime import datetime

import pytest


class TestRestockingEndpoints:
    """Test suite for restocking order endpoints."""

    def _sample_items(self):
        return [
            {"sku": "WDG-001", "name": "Industrial Widget Type A", "quantity": 10, "unit_price": 42.50},
            {"sku": "GSK-203", "name": "High-Temperature Gasket", "quantity": 5, "unit_price": 24.00},
        ]

    def test_create_restocking_order(self, client):
        """Test submitting a restocking order returns a Submitted order."""
        response = client.post("/api/restocking", json={"items": self._sample_items()})
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "Submitted"
        assert data["order_number"].startswith("RST-")
        assert data["customer"] == "Internal Restocking"
        assert len(data["items"]) == 2

    def test_restocking_order_total_value_calculation(self, client):
        """Test that total_value is computed server-side from the submitted items."""
        items = self._sample_items()
        response = client.post("/api/restocking", json={"items": items})
        data = response.json()

        expected_total = sum(item["quantity"] * item["unit_price"] for item in items)
        assert abs(data["total_value"] - expected_total) < 0.01

    def test_restocking_order_lead_time(self, client):
        """Test that expected_delivery is 7-14 days after order_date."""
        response = client.post("/api/restocking", json={"items": self._sample_items()})
        data = response.json()

        order_date = datetime.fromisoformat(data["order_date"])
        expected_delivery = datetime.fromisoformat(data["expected_delivery"])
        lead_time_days = (expected_delivery - order_date).days

        assert 7 <= lead_time_days <= 14

    def test_restocking_order_appears_in_orders_endpoint(self, client):
        """Test that a submitted restocking order round-trips via GET /api/orders."""
        response = client.post("/api/restocking", json={"items": self._sample_items()})
        order_number = response.json()["order_number"]

        response = client.get("/api/orders?status=Submitted")
        assert response.status_code == 200

        data = response.json()
        assert any(order["order_number"] == order_number for order in data)

    def test_restocking_order_rejects_empty_items(self, client):
        """Test that an empty items list is rejected."""
        response = client.post("/api/restocking", json={"items": []})
        assert response.status_code == 422

    def test_restocking_order_rejects_non_positive_quantity(self, client):
        """Test that a non-positive quantity is rejected."""
        items = [{"sku": "WDG-001", "name": "Industrial Widget Type A", "quantity": 0, "unit_price": 42.50}]
        response = client.post("/api/restocking", json={"items": items})
        assert response.status_code == 422

    def test_demand_forecasts_include_unit_cost(self, client):
        """Test that demand forecast items now expose unit_cost for restocking math."""
        response = client.get("/api/demand")
        data = response.json()

        for forecast in data:
            assert "unit_cost" in forecast
            assert isinstance(forecast["unit_cost"], (int, float))
            assert forecast["unit_cost"] > 0
