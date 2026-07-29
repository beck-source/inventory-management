"""
Tests for restocking API endpoints.
"""
import re

import pytest

import mock_data


@pytest.fixture(autouse=True)
def reset_restock_orders():
    """Isolate restock order state between tests.

    mock_data.restock_orders is a module-level global and main.py holds a
    reference to the same list object, so it must be mutated in place -
    rebinding would leave main.py appending to the old list.
    """
    saved = list(mock_data.restock_orders)
    mock_data.restock_orders.clear()
    yield
    mock_data.restock_orders.clear()
    mock_data.restock_orders.extend(saved)


class TestDemandForecastCostFields:
    """Tests for the unit_cost and lead_time_days fields on demand forecasts."""

    def test_demand_forecasts_have_unit_cost(self, client):
        """Every demand forecast exposes a positive unit_cost."""
        response = client.get("/api/demand")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

        for forecast in data:
            assert "unit_cost" in forecast
            assert isinstance(forecast["unit_cost"], (int, float))
            assert forecast["unit_cost"] > 0, f"{forecast['item_sku']} has a non-positive unit_cost"

    def test_demand_forecasts_have_lead_time(self, client):
        """Every demand forecast exposes a lead_time_days in a sensible range."""
        response = client.get("/api/demand")
        assert response.status_code == 200
        data = response.json()

        for forecast in data:
            assert "lead_time_days" in forecast
            assert isinstance(forecast["lead_time_days"], int)
            assert 1 <= forecast["lead_time_days"] <= 60, (
                f"{forecast['item_sku']} lead time {forecast['lead_time_days']} is out of range"
            )

    def test_psu_501_cost_matches_inventory(self, client):
        """PSU-501 exists in both datasets - the unit_cost must not drift apart."""
        demand = client.get("/api/demand").json()
        inventory = client.get("/api/inventory").json()

        demand_item = next(f for f in demand if f["item_sku"] == "PSU-501")
        inventory_item = next(i for i in inventory if i["sku"] == "PSU-501")

        assert abs(demand_item["unit_cost"] - inventory_item["unit_cost"]) < 0.01


class TestRestockOrdersEndpoints:
    """Tests for the /api/restock-orders endpoints."""

    def test_get_restock_orders_empty(self, client):
        """A clean server has no submitted restock orders."""
        response = client.get("/api/restock-orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_restock_order(self, client, sample_restock_order_request):
        """Submitting a valid restock order returns 201 with derived fields."""
        response = client.post("/api/restock-orders", json=sample_restock_order_request)
        assert response.status_code == 201

        data = response.json()
        assert data["id"] == "RO-1"
        assert data["status"] == "Submitted"
        assert len(data["items"]) == 2
        assert abs(data["total_cost"] - 1965.00) < 0.01
        assert data["budget"] == sample_restock_order_request["budget"]
        assert data["max_lead_time_days"] == 14
        assert data["expected_delivery"] > data["order_date"]

    def test_create_restock_order_appears_in_list(self, client, sample_restock_order_request):
        """A submitted order is returned by the list endpoint."""
        created = client.post("/api/restock-orders", json=sample_restock_order_request).json()

        response = client.get("/api/restock-orders")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["order_number"] == created["order_number"]

    def test_restock_orders_newest_first(self, client, sample_restock_order_request):
        """The list endpoint returns the most recently submitted order first."""
        first = client.post("/api/restock-orders", json=sample_restock_order_request).json()
        second = client.post("/api/restock-orders", json=sample_restock_order_request).json()

        data = client.get("/api/restock-orders").json()
        assert len(data) == 2
        assert data[0]["order_number"] == second["order_number"]
        assert data[1]["order_number"] == first["order_number"]

    def test_order_number_format(self, client, sample_restock_order_request):
        """Order numbers follow the RSO-YYYY-NNNN convention."""
        data = client.post("/api/restock-orders", json=sample_restock_order_request).json()
        assert re.match(r"^RSO-\d{4}-\d{4}$", data["order_number"]), data["order_number"]

    def test_create_restock_order_rejects_unknown_sku(self, client):
        """An item SKU not present in the demand forecast is rejected."""
        response = client.post("/api/restock-orders", json={
            "budget": 5000,
            "items": [{
                "item_sku": "NOPE-999",
                "item_name": "Nonexistent Part",
                "quantity": 1,
                "unit_cost": 10.0,
                "lead_time_days": 5,
                "line_total": 10.0
            }]
        })
        assert response.status_code == 400
        assert "unknown item sku" in response.json()["detail"].lower()

    def test_create_restock_order_rejects_over_budget(self, client):
        """An order totalling more than the stated budget is rejected."""
        response = client.post("/api/restock-orders", json={
            "budget": 100,
            "items": [{
                "item_sku": "WDG-001",
                "item_name": "Industrial Widget Type A",
                "quantity": 150,
                "unit_cost": 12.50,
                "lead_time_days": 10,
                "line_total": 1875.00
            }]
        })
        assert response.status_code == 400
        assert "budget" in response.json()["detail"].lower()

    def test_create_restock_order_rejects_line_total_mismatch(self, client):
        """A line_total inconsistent with quantity * unit_cost is rejected."""
        response = client.post("/api/restock-orders", json={
            "budget": 5000,
            "items": [{
                "item_sku": "WDG-001",
                "item_name": "Industrial Widget Type A",
                "quantity": 150,
                "unit_cost": 12.50,
                "lead_time_days": 10,
                "line_total": 99.00
            }]
        })
        assert response.status_code == 400
        assert "line_total" in response.json()["detail"]

    def test_create_restock_order_rejects_empty_items(self, client):
        """An order with no items fails Pydantic validation."""
        response = client.post("/api/restock-orders", json={"budget": 5000, "items": []})
        assert response.status_code == 422

    def test_create_restock_order_rejects_zero_quantity(self, client):
        """An item with a zero quantity fails Pydantic validation."""
        response = client.post("/api/restock-orders", json={
            "budget": 5000,
            "items": [{
                "item_sku": "WDG-001",
                "item_name": "Industrial Widget Type A",
                "quantity": 0,
                "unit_cost": 12.50,
                "lead_time_days": 10,
                "line_total": 0.0
            }]
        })
        assert response.status_code == 422

    def test_create_restock_order_does_not_touch_orders(self, client, sample_restock_order_request):
        """Restock orders stay separate from customer orders."""
        before = client.get("/api/orders").json()

        client.post("/api/restock-orders", json=sample_restock_order_request)

        after = client.get("/api/orders").json()
        assert len(after) == len(before)
        assert not any(order["order_number"].startswith("RSO-") for order in after)
