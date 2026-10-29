"""
Tests for restocking order API endpoints and the demand fields they depend on.
"""
from datetime import datetime, timedelta

import pytest

from main import restocking_orders


@pytest.fixture(autouse=True)
def clearRestockingOrders():
    """Submitted orders are global in-memory state, so isolate each test."""
    restocking_orders.clear()
    yield
    restocking_orders.clear()


def getForecastsBySku(client):
    """Return demand forecasts keyed by SKU."""
    return {f["item_sku"]: f for f in client.get("/api/demand").json()}


class TestDemandCostFields:
    """Test suite for the cost and lead time fields on demand forecasts."""

    def test_demand_forecasts_have_cost_and_lead_time(self, client):
        """Test that every forecast has a positive unit cost and lead time."""
        data = client.get("/api/demand").json()
        assert len(data) > 0

        for forecast in data:
            assert isinstance(forecast["unit_cost"], (int, float))
            assert isinstance(forecast["lead_time_days"], int)
            assert forecast["unit_cost"] > 0
            assert forecast["lead_time_days"] > 0


class TestRestockingOrderEndpoints:
    """Test suite for the restocking order endpoints."""

    def test_get_restocking_orders_empty(self, client):
        """Test that no orders are returned before any are submitted."""
        response = client.get("/api/restocking-orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_restocking_order(self, client):
        """Test submitting a valid order."""
        response = client.post("/api/restocking-orders", json={
            "budget": 10000,
            "items": [{"sku": "WDG-001", "quantity": 450}]
        })
        assert response.status_code == 200

        order = response.json()
        assert order["order_number"] == "RST-0001"
        assert order["status"] == "Submitted"
        assert len(order["items"]) == 1
        assert order["items"][0]["sku"] == "WDG-001"
        assert order["items"][0]["name"] == "Industrial Widget Type A"

    def test_create_order_uses_server_prices(self, client):
        """Test that line totals are priced from forecast data, not the client."""
        forecasts = getForecastsBySku(client)
        response = client.post("/api/restocking-orders", json={
            "budget": 100000,
            "items": [
                {"sku": "WDG-001", "quantity": 450},
                {"sku": "GSK-203", "quantity": 600}
            ]
        })
        order = response.json()

        expected_total = sum(
            line["quantity"] * forecasts[line["sku"]]["unit_cost"]
            for line in order["items"]
        )
        assert abs(order["total_cost"] - expected_total) < 0.01
        for line in order["items"]:
            assert line["unit_cost"] == forecasts[line["sku"]]["unit_cost"]

    def test_order_lead_time_is_longest_item(self, client):
        """Test that the order lead time is the maximum item lead time."""
        forecasts = getForecastsBySku(client)
        response = client.post("/api/restocking-orders", json={
            "budget": 100000,
            "items": [
                {"sku": "FLT-405", "quantity": 10},
                {"sku": "BRG-102", "quantity": 10}
            ]
        })
        order = response.json()

        expected = max(forecasts["FLT-405"]["lead_time_days"], forecasts["BRG-102"]["lead_time_days"])
        assert order["lead_time_days"] == expected

    def test_expected_delivery_is_order_date_plus_lead_time(self, client):
        """Test that expected delivery is the order date plus the lead time."""
        order = client.post("/api/restocking-orders", json={
            "budget": 10000,
            "items": [{"sku": "WDG-001", "quantity": 10}]
        }).json()

        placed = datetime.fromisoformat(order["order_date"])
        delivery = datetime.fromisoformat(order["expected_delivery"])
        assert delivery - placed == timedelta(days=order["lead_time_days"])

    def test_orders_listed_newest_first(self, client):
        """Test that submitted orders are returned newest first."""
        for _ in range(2):
            client.post("/api/restocking-orders", json={
                "budget": 10000,
                "items": [{"sku": "WDG-001", "quantity": 10}]
            })

        data = client.get("/api/restocking-orders").json()
        assert [o["order_number"] for o in data] == ["RST-0002", "RST-0001"]

    def test_order_at_exact_budget_is_accepted(self, client):
        """Test that a total equal to the budget is allowed."""
        response = client.post("/api/restocking-orders", json={
            "budget": 125.0,
            "items": [{"sku": "WDG-001", "quantity": 10}]
        })
        assert response.status_code == 200

    def test_order_over_budget_rejected(self, client):
        """Test that a total over budget returns 400 and stores nothing."""
        response = client.post("/api/restocking-orders", json={
            "budget": 124.99,
            "items": [{"sku": "WDG-001", "quantity": 10}]
        })
        assert response.status_code == 400
        assert "budget" in response.json()["detail"].lower()
        assert client.get("/api/restocking-orders").json() == []

    def test_empty_order_rejected(self, client):
        """Test that an order with no items returns 400."""
        response = client.post("/api/restocking-orders", json={"budget": 1000, "items": []})
        assert response.status_code == 400

    def test_unknown_sku_rejected(self, client):
        """Test that an unknown SKU returns 400."""
        response = client.post("/api/restocking-orders", json={
            "budget": 1000,
            "items": [{"sku": "NOPE-999", "quantity": 1}]
        })
        assert response.status_code == 400
        assert "unknown sku" in response.json()["detail"].lower()

    def test_duplicate_sku_rejected(self, client):
        """Test that repeating a SKU returns 400."""
        response = client.post("/api/restocking-orders", json={
            "budget": 100000,
            "items": [
                {"sku": "WDG-001", "quantity": 1},
                {"sku": "WDG-001", "quantity": 1}
            ]
        })
        assert response.status_code == 400

    @pytest.mark.parametrize("quantity", [0, -5])
    def test_non_positive_quantity_rejected(self, client, quantity):
        """Test that zero or negative quantities return 400."""
        response = client.post("/api/restocking-orders", json={
            "budget": 1000,
            "items": [{"sku": "WDG-001", "quantity": quantity}]
        })
        assert response.status_code == 400

    def test_missing_fields_return_validation_error(self, client):
        """Test that a malformed body returns 422."""
        response = client.post("/api/restocking-orders", json={"items": []})
        assert response.status_code == 422


class TestRestockingIsolation:
    """Restocking orders must not affect customer-order calculations."""

    def test_restocking_order_does_not_change_dashboard_or_orders(self, client):
        """Test that placing a restocking order leaves customer data untouched."""
        orders_before = client.get("/api/orders").json()
        summary_before = client.get("/api/dashboard/summary").json()

        client.post("/api/restocking-orders", json={
            "budget": 10000,
            "items": [{"sku": "WDG-001", "quantity": 100}]
        })

        assert client.get("/api/orders").json() == orders_before
        assert client.get("/api/dashboard/summary").json() == summary_before
