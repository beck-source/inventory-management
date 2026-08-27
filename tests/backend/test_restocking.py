"""
Tests for restocking API endpoints.

Covers the two new fields on the demand forecast (unit_cost, lead_time_days)
and the /api/restock-orders submit-and-list flow.

Note: submitted restock orders live in a module-level list in main.py, so they
accumulate across tests within a session. Every assertion here is written
relative to a baseline count rather than against an absolute list length.
"""
from datetime import datetime

import pytest


@pytest.fixture
def restock_payload():
    """A valid two-line restocking order that fits inside its budget."""
    return {
        "budget": 6000,
        "items": [
            {
                "item_sku": "WDG-001",
                "item_name": "Industrial Widget Type A",
                "quantity": 150,
                "unit_cost": 24.50,
                "lead_time_days": 14
            },
            {
                "item_sku": "FLT-405",
                "item_name": "Oil Filter Cartridge",
                "quantity": 150,
                "unit_cost": 12.25,
                "lead_time_days": 7
            }
        ]
    }


class TestDemandForecastRestockFields:
    """Test suite for the restocking fields added to the demand forecast."""

    def test_demand_forecasts_include_cost_and_lead_time(self, client):
        """Test that every demand forecast exposes unit_cost and lead_time_days."""
        response = client.get("/api/demand")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        for forecast in data:
            assert "unit_cost" in forecast
            assert "lead_time_days" in forecast

    def test_demand_forecast_field_types(self, client):
        """Test that the new forecast fields have correct types and ranges."""
        response = client.get("/api/demand")
        data = response.json()

        for forecast in data:
            assert isinstance(forecast["unit_cost"], (int, float))
            assert isinstance(forecast["lead_time_days"], int)
            assert forecast["unit_cost"] > 0
            assert forecast["lead_time_days"] > 0

    def test_forecast_unit_cost_matches_inventory_where_sku_exists(self, client):
        """Test that a forecast SKU also held in inventory agrees on unit cost."""
        forecasts = client.get("/api/demand").json()
        inventory = client.get("/api/inventory").json()

        inventory_costs = {item["sku"]: item["unit_cost"] for item in inventory}
        overlapping = [f for f in forecasts if f["item_sku"] in inventory_costs]

        # Only PSU-501 currently exists in both datasets, but assert on whatever
        # overlaps so this test keeps working as the fixtures grow.
        assert len(overlapping) > 0

        for forecast in overlapping:
            expected = inventory_costs[forecast["item_sku"]]
            assert abs(forecast["unit_cost"] - expected) < 0.01

    def test_shortfall_items_exist(self, client):
        """Test that at least one forecast has a positive demand shortfall."""
        data = client.get("/api/demand").json()

        shortfalls = [
            f["forecasted_demand"] - f["current_demand"]
            for f in data
        ]
        assert any(s > 0 for s in shortfalls)


class TestRestockOrdersEndpoints:
    """Test suite for the restock-orders endpoints."""

    def test_get_restock_orders_returns_list(self, client):
        """Test getting all submitted restocking orders."""
        response = client.get("/api/restock-orders")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_restock_order_returns_201(self, client, restock_payload):
        """Test that submitting a restocking order returns 201 with the order."""
        response = client.post("/api/restock-orders", json=restock_payload)
        assert response.status_code == 201

        order = response.json()
        for field in [
            "id", "order_number", "items", "total_value", "budget",
            "status", "submitted_date", "expected_delivery", "lead_time_days"
        ]:
            assert field in order

        assert order["status"] == "Submitted"
        assert order["order_number"].startswith("RO-")
        assert len(order["items"]) == 2

    def test_create_restock_order_total_value_calculation(self, client, restock_payload):
        """Test that total_value is the sum of quantity times unit cost."""
        response = client.post("/api/restock-orders", json=restock_payload)
        order = response.json()

        calculated_total = sum(
            item["quantity"] * item["unit_cost"]
            for item in restock_payload["items"]
        )
        assert abs(order["total_value"] - calculated_total) < 0.01
        assert order["total_value"] <= order["budget"]

    def test_create_restock_order_lead_time_is_slowest_item(self, client, restock_payload):
        """Test that order lead time is the maximum across its line items."""
        response = client.post("/api/restock-orders", json=restock_payload)
        order = response.json()

        expected_lead = max(item["lead_time_days"] for item in restock_payload["items"])
        assert order["lead_time_days"] == expected_lead

    def test_create_restock_order_expected_delivery_matches_lead_time(self, client, restock_payload):
        """Test that expected_delivery is submitted_date plus the lead time."""
        response = client.post("/api/restock-orders", json=restock_payload)
        order = response.json()

        submitted = datetime.fromisoformat(order["submitted_date"])
        delivery = datetime.fromisoformat(order["expected_delivery"])

        assert (delivery - submitted).days == order["lead_time_days"]
        assert delivery > submitted

    def test_created_order_appears_in_list(self, client, restock_payload):
        """Test that a submitted order shows up in the restock-orders list."""
        before = len(client.get("/api/restock-orders").json())

        created = client.post("/api/restock-orders", json=restock_payload).json()

        after = client.get("/api/restock-orders").json()
        assert len(after) == before + 1
        assert any(o["order_number"] == created["order_number"] for o in after)

    def test_restock_orders_returned_newest_first(self, client, restock_payload):
        """Test that the list returns the most recently submitted order first."""
        client.post("/api/restock-orders", json=restock_payload)
        second = client.post("/api/restock-orders", json=restock_payload).json()

        listed = client.get("/api/restock-orders").json()
        assert listed[0]["order_number"] == second["order_number"]

    def test_order_numbers_are_unique(self, client, restock_payload):
        """Test that each submitted order gets a distinct order number."""
        client.post("/api/restock-orders", json=restock_payload)
        client.post("/api/restock-orders", json=restock_payload)

        listed = client.get("/api/restock-orders").json()
        numbers = [o["order_number"] for o in listed]
        assert len(numbers) == len(set(numbers))

    def test_create_restock_order_accepts_exact_budget_match(self, client):
        """Test that an order costing exactly the budget is accepted."""
        payload = {
            "budget": 2450.0,
            "items": [{
                "item_sku": "WDG-001",
                "item_name": "Industrial Widget Type A",
                "quantity": 100,
                "unit_cost": 24.50,
                "lead_time_days": 14
            }]
        }
        response = client.post("/api/restock-orders", json=payload)
        assert response.status_code == 201
        assert abs(response.json()["total_value"] - 2450.0) < 0.01


class TestRestockOrderValidation:
    """Test suite for restock-order rejection paths."""

    def test_rejects_empty_items(self, client):
        """Test that an order with no line items is rejected."""
        response = client.post("/api/restock-orders", json={"budget": 5000, "items": []})
        assert response.status_code == 400

        detail = response.json()["detail"]
        assert "at least one item" in detail.lower()

    def test_rejects_unknown_sku(self, client):
        """Test that a SKU absent from the demand forecast is rejected."""
        payload = {
            "budget": 5000,
            "items": [{
                "item_sku": "NOPE-999",
                "item_name": "Not A Real Part",
                "quantity": 1,
                "unit_cost": 10.0,
                "lead_time_days": 5
            }]
        }
        response = client.post("/api/restock-orders", json=payload)
        assert response.status_code == 400
        assert "NOPE-999" in response.json()["detail"]

    def test_rejects_zero_quantity(self, client):
        """Test that a line item with no quantity is rejected."""
        payload = {
            "budget": 5000,
            "items": [{
                "item_sku": "WDG-001",
                "item_name": "Industrial Widget Type A",
                "quantity": 0,
                "unit_cost": 24.50,
                "lead_time_days": 14
            }]
        }
        response = client.post("/api/restock-orders", json=payload)
        assert response.status_code == 400
        assert "at least 1" in response.json()["detail"].lower()

    def test_rejects_total_over_budget(self, client):
        """Test that an order exceeding its budget is rejected."""
        payload = {
            "budget": 100.0,
            "items": [{
                "item_sku": "WDG-001",
                "item_name": "Industrial Widget Type A",
                "quantity": 150,
                "unit_cost": 24.50,
                "lead_time_days": 14
            }]
        }
        response = client.post("/api/restock-orders", json=payload)
        assert response.status_code == 400

        detail = response.json()["detail"].lower()
        assert "exceeds" in detail
        assert "budget" in detail

    def test_over_budget_order_is_not_stored(self, client):
        """Test that a rejected order does not land in the list."""
        before = len(client.get("/api/restock-orders").json())

        client.post("/api/restock-orders", json={
            "budget": 1.0,
            "items": [{
                "item_sku": "WDG-001",
                "item_name": "Industrial Widget Type A",
                "quantity": 150,
                "unit_cost": 24.50,
                "lead_time_days": 14
            }]
        })

        after = len(client.get("/api/restock-orders").json())
        assert after == before

    def test_rejects_malformed_payload(self, client):
        """Test that a payload missing required fields fails validation."""
        response = client.post("/api/restock-orders", json={"items": []})
        assert response.status_code == 422
        assert "detail" in response.json()
