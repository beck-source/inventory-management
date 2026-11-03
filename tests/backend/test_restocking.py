"""
Tests for restocking order API endpoints.
"""
import sys

import pytest


@pytest.fixture(autouse=True)
def clear_restocking_orders():
    """Orders are stored in a module-level list; reset it so tests are independent."""
    main = sys.modules["main"]
    main.restocking_orders.clear()
    yield
    main.restocking_orders.clear()


@pytest.fixture
def forecasts(client):
    return client.get("/api/demand").json()


def _item(forecast, quantity=10):
    return {
        "sku": forecast["item_sku"],
        "name": forecast["item_name"],
        "quantity": quantity,
        "unit_cost": forecast["unit_cost"],
        "lead_time_days": forecast["lead_time_days"],
    }


class TestRestockingEndpoints:
    """Test suite for restocking order endpoints."""

    def test_list_empty(self, client):
        """No orders exist before anything is submitted."""
        response = client.get("/api/restocking-orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_order(self, client, forecasts):
        """Lead time is the longest item lead time and total is the sum of line costs."""
        items = [_item(f) for f in forecasts[:3]]
        expected_total = round(sum(i["quantity"] * i["unit_cost"] for i in items), 2)

        response = client.post("/api/restocking-orders", json={"budget": expected_total + 1, "items": items})
        assert response.status_code == 200

        order = response.json()
        assert order["status"] == "Submitted"
        assert order["order_number"].startswith("RST-")
        assert order["total_value"] == expected_total
        assert order["lead_time_days"] == max(i["lead_time_days"] for i in items)
        assert "expected_delivery" in order and "submitted_date" in order

    def test_list_newest_first(self, client, forecasts):
        """Submitted orders are listed newest first."""
        for f in forecasts[:2]:
            client.post("/api/restocking-orders", json={"budget": 1e9, "items": [_item(f)]})

        orders = client.get("/api/restocking-orders").json()
        assert [o["id"] for o in orders] == ["2", "1"]

    def test_empty_items_rejected(self, client):
        response = client.post("/api/restocking-orders", json={"budget": 1000, "items": []})
        assert response.status_code == 400

    def test_non_positive_quantity_rejected(self, client, forecasts):
        response = client.post("/api/restocking-orders", json={"budget": 1e9, "items": [_item(forecasts[0], quantity=0)]})
        assert response.status_code == 422

    def test_over_budget_rejected(self, client, forecasts):
        response = client.post("/api/restocking-orders", json={"budget": 0, "items": [_item(forecasts[0])]})
        assert response.status_code == 400
        assert "budget" in response.json()["detail"].lower()

    def test_unknown_sku_rejected(self, client, forecasts):
        item = {**_item(forecasts[0]), "sku": "NOPE-000"}
        response = client.post("/api/restocking-orders", json={"budget": 1e9, "items": [item]})
        assert response.status_code == 400

    def test_server_uses_forecast_cost_and_lead_time(self, client, forecasts):
        """Client-supplied cost and lead time are ignored in favour of forecast values."""
        f = forecasts[0]
        item = {**_item(f), "unit_cost": 0.01, "lead_time_days": 1}
        response = client.post("/api/restocking-orders", json={"budget": 1e9, "items": [item]})
        order = response.json()
        assert order["items"][0]["unit_cost"] == f["unit_cost"]
        assert order["lead_time_days"] == f["lead_time_days"]
