"""
Tests for restocking API endpoints.
"""
from datetime import date, timedelta

import pytest

import mock_data


@pytest.fixture(autouse=True)
def clean_restock_orders():
    """Submitted orders live in a module-level list shared by every test, so reset it around each test."""
    mock_data.restock_orders.clear()
    yield
    mock_data.restock_orders.clear()


def _items_by_sku(client):
    return {item["item_sku"]: item for item in client.get("/api/restocking/items").json()}


class TestRestockingItemsEndpoint:
    """Test suite for GET /api/restocking/items."""

    def test_get_restocking_items(self, client):
        """Test that every forecast item is returned joined with its catalog entry."""
        response = client.get("/api/restocking/items")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == len(client.get("/api/demand").json())

        first = data[0]
        for field in ["item_sku", "item_name", "current_demand", "forecasted_demand", "trend",
                      "growth_pct", "suggested_qty", "unit_cost", "supplier_name", "lead_time_days"]:
            assert field in first

    def test_restocking_items_numeric_types(self, client):
        """Test that numeric fields have valid types and ranges."""
        for item in client.get("/api/restocking/items").json():
            assert isinstance(item["suggested_qty"], int)
            assert item["suggested_qty"] >= 0
            assert isinstance(item["unit_cost"], (int, float))
            assert item["unit_cost"] > 0
            assert isinstance(item["lead_time_days"], int)
            assert item["lead_time_days"] > 0

    def test_suggested_qty_calculation(self, client):
        """Test that suggested quantity is forecast growth, floored at zero."""
        demand = {d["item_sku"]: d for d in client.get("/api/demand").json()}

        for sku, item in _items_by_sku(client).items():
            expected = max(demand[sku]["forecasted_demand"] - demand[sku]["current_demand"], 0)
            assert item["suggested_qty"] == expected

    def test_declining_demand_suggests_nothing(self, client):
        """Test that an item with falling demand is not suggested for restocking."""
        declining = [i for i in client.get("/api/restocking/items").json() if i["trend"] == "decreasing"]
        assert len(declining) > 0
        for item in declining:
            assert item["suggested_qty"] == 0


class TestRestockingOrdersEndpoint:
    """Test suite for POST and GET /api/restocking/orders."""

    def test_create_order(self, client):
        """Test submitting a valid order."""
        response = client.post("/api/restocking/orders", json={
            "items": [{"item_sku": "WDG-001", "quantity": 10}]
        })
        assert response.status_code == 201

        order = response.json()
        assert order["order_number"] == "RST-0001"
        assert order["status"] == "Submitted"
        assert order["submitted_date"] == date.today().isoformat()
        assert len(order["items"]) == 1
        assert order["items"][0]["sku"] == "WDG-001"
        assert order["items"][0]["quantity"] == 10

    def test_order_totals_use_catalog_prices(self, client):
        """Test that totals are computed server-side from catalog unit costs."""
        catalog = _items_by_sku(client)
        response = client.post("/api/restocking/orders", json={
            "items": [
                {"item_sku": "WDG-001", "quantity": 10},
                {"item_sku": "FLT-405", "quantity": 20},
            ]
        })
        order = response.json()

        expected = 10 * catalog["WDG-001"]["unit_cost"] + 20 * catalog["FLT-405"]["unit_cost"]
        assert abs(order["total_value"] - expected) < 0.01
        for line in order["items"]:
            assert abs(line["line_total"] - line["quantity"] * line["unit_cost"]) < 0.01

    def test_client_supplied_price_is_ignored(self, client):
        """Test that a price sent by the client cannot change the order total."""
        catalog = _items_by_sku(client)
        response = client.post("/api/restocking/orders", json={
            "items": [{"item_sku": "WDG-001", "quantity": 1, "unit_cost": 0.01}]
        })
        assert response.status_code == 201
        assert response.json()["items"][0]["unit_cost"] == catalog["WDG-001"]["unit_cost"]

    def test_order_lead_time_is_slowest_item(self, client):
        """Test that the order lead time is the maximum across its items."""
        catalog = _items_by_sku(client)
        response = client.post("/api/restocking/orders", json={
            "items": [
                {"item_sku": "FLT-405", "quantity": 5},
                {"item_sku": "GSK-203", "quantity": 5},
            ]
        })
        order = response.json()

        slowest = max(catalog["FLT-405"]["lead_time_days"], catalog["GSK-203"]["lead_time_days"])
        assert order["lead_time_days"] == slowest
        expected_date = date.today() + timedelta(days=slowest)
        assert order["expected_delivery"] == expected_date.isoformat()

    def test_create_order_unknown_sku(self, client):
        """Test that an unknown SKU is rejected."""
        response = client.post("/api/restocking/orders", json={
            "items": [{"item_sku": "NOPE-999", "quantity": 1}]
        })
        assert response.status_code == 400
        assert "unknown sku" in response.json()["detail"].lower()
        assert client.get("/api/restocking/orders").json() == []

    def test_create_order_duplicate_sku(self, client):
        """Test that the same SKU twice in one order is rejected."""
        response = client.post("/api/restocking/orders", json={
            "items": [
                {"item_sku": "WDG-001", "quantity": 1},
                {"item_sku": "WDG-001", "quantity": 2},
            ]
        })
        assert response.status_code == 400

    def test_create_order_empty_items(self, client):
        """Test that an order with no items fails validation."""
        response = client.post("/api/restocking/orders", json={"items": []})
        assert response.status_code == 422

    @pytest.mark.parametrize("quantity", [0, -5])
    def test_create_order_invalid_quantity(self, client, quantity):
        """Test that zero or negative quantities fail validation."""
        response = client.post("/api/restocking/orders", json={
            "items": [{"item_sku": "WDG-001", "quantity": quantity}]
        })
        assert response.status_code == 422

    def test_get_orders_empty(self, client):
        """Test that no submitted orders returns an empty list."""
        response = client.get("/api/restocking/orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_orders_newest_first(self, client):
        """Test that submitted orders are listed newest first."""
        client.post("/api/restocking/orders", json={"items": [{"item_sku": "WDG-001", "quantity": 1}]})
        client.post("/api/restocking/orders", json={"items": [{"item_sku": "FLT-405", "quantity": 1}]})

        data = client.get("/api/restocking/orders").json()
        assert [o["order_number"] for o in data] == ["RST-0002", "RST-0001"]
