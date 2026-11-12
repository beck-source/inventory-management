"""
Tests for restocking order API endpoints.
"""
from datetime import date, timedelta

import pytest


@pytest.fixture
def orderable_forecasts(client):
    """Demand forecasts that carry the cost and lead time fields needed to restock."""
    forecasts = client.get("/api/demand").json()
    return [f for f in forecasts if f.get("unit_cost") is not None]


class TestRestockOrdersEndpoints:
    """Test suite for restock order endpoints."""

    def test_demand_forecasts_include_cost_and_lead_time(self, client):
        """Test that demand forecasts expose the fields restocking relies on."""
        data = client.get("/api/demand").json()
        assert len(data) > 0

        for forecast in data:
            assert isinstance(forecast["unit_cost"], (int, float))
            assert forecast["unit_cost"] > 0
            assert isinstance(forecast["lead_time_days"], int)
            assert forecast["lead_time_days"] > 0
            assert forecast["supplier_name"]

    def test_get_restock_orders_empty(self, client):
        """Test that no orders are listed before any are submitted."""
        response = client.get("/api/restock-orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_restock_order(self, client, orderable_forecasts):
        """Test submitting a valid restock order."""
        forecast = orderable_forecasts[0]
        payload = {
            "budget": 100000,
            "items": [{"item_sku": forecast["item_sku"], "quantity": 10}],
        }

        response = client.post("/api/restock-orders", json=payload)
        assert response.status_code == 201

        order = response.json()
        assert order["id"] == "RST-0001"
        assert order["status"] == "Submitted"
        assert order["budget"] == 100000
        assert len(order["items"]) == 1
        assert order["items"][0]["item_sku"] == forecast["item_sku"]
        assert order["items"][0]["quantity"] == 10

    def test_restock_order_totals_computed_server_side(self, client, orderable_forecasts):
        """Test that prices come from forecast data, not the request."""
        first, second = orderable_forecasts[0], orderable_forecasts[1]
        payload = {
            "budget": 100000,
            "items": [
                {"item_sku": first["item_sku"], "quantity": 3},
                {"item_sku": second["item_sku"], "quantity": 5},
            ],
        }

        order = client.post("/api/restock-orders", json=payload).json()

        expected_total = 3 * first["unit_cost"] + 5 * second["unit_cost"]
        assert abs(order["total_cost"] - expected_total) < 0.01
        for line in order["items"]:
            assert abs(line["line_total"] - line["quantity"] * line["unit_cost"]) < 0.01

    def test_restock_order_lead_time_is_longest_line(self, client, orderable_forecasts):
        """Test that order lead time is the longest lead time of its lines and sets the delivery date."""
        first, second = orderable_forecasts[0], orderable_forecasts[1]
        payload = {
            "budget": 100000,
            "items": [
                {"item_sku": first["item_sku"], "quantity": 1},
                {"item_sku": second["item_sku"], "quantity": 1},
            ],
        }

        order = client.post("/api/restock-orders", json=payload).json()

        expected_lead = max(first["lead_time_days"], second["lead_time_days"])
        assert order["lead_time_days"] == expected_lead
        expected_delivery = date.today() + timedelta(days=expected_lead)
        assert order["expected_delivery"] == expected_delivery.isoformat()

    def test_create_restock_order_exceeds_budget(self, client, orderable_forecasts):
        """Test that an order above the budget is rejected."""
        forecast = orderable_forecasts[0]
        payload = {
            "budget": 1,
            "items": [{"item_sku": forecast["item_sku"], "quantity": 10}],
        }

        response = client.post("/api/restock-orders", json=payload)
        assert response.status_code == 400
        assert "budget" in response.json()["detail"].lower()
        assert client.get("/api/restock-orders").json() == []

    def test_create_restock_order_empty_items(self, client):
        """Test that an order with no items is rejected."""
        response = client.post("/api/restock-orders", json={"budget": 1000, "items": []})
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_create_restock_order_invalid_quantity(self, client, orderable_forecasts):
        """Test that zero or negative quantities are rejected."""
        sku = orderable_forecasts[0]["item_sku"]
        for quantity in (0, -5):
            response = client.post(
                "/api/restock-orders",
                json={"budget": 1000, "items": [{"item_sku": sku, "quantity": quantity}]},
            )
            assert response.status_code == 400

    def test_create_restock_order_unknown_sku(self, client):
        """Test that an unknown SKU is rejected."""
        response = client.post(
            "/api/restock-orders",
            json={"budget": 1000, "items": [{"item_sku": "NOPE-000", "quantity": 1}]},
        )
        assert response.status_code == 400
        assert "nope-000" in response.json()["detail"].lower()

    def test_create_restock_order_missing_fields(self, client):
        """Test that a malformed body fails validation."""
        response = client.post("/api/restock-orders", json={"items": []})
        assert response.status_code == 422

    def test_get_restock_orders_newest_first(self, client, orderable_forecasts):
        """Test that submitted orders are listed newest first."""
        sku = orderable_forecasts[0]["item_sku"]
        for quantity in (1, 2):
            client.post(
                "/api/restock-orders",
                json={"budget": 100000, "items": [{"item_sku": sku, "quantity": quantity}]},
            )

        data = client.get("/api/restock-orders").json()
        assert [o["id"] for o in data] == ["RST-0002", "RST-0001"]

    def test_restock_order_structure(self, client, orderable_forecasts):
        """Test that listed orders carry every field the Orders tab needs."""
        sku = orderable_forecasts[0]["item_sku"]
        client.post(
            "/api/restock-orders",
            json={"budget": 100000, "items": [{"item_sku": sku, "quantity": 2}]},
        )

        order = client.get("/api/restock-orders").json()[0]
        for field in ("id", "submitted_at", "budget", "items", "total_cost",
                      "lead_time_days", "expected_delivery", "status"):
            assert field in order
        assert isinstance(order["lead_time_days"], int)
        assert isinstance(order["total_cost"], (int, float))

        line = order["items"][0]
        for field in ("item_sku", "item_name", "supplier_name", "quantity",
                      "unit_cost", "line_total", "lead_time_days"):
            assert field in line
