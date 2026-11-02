"""
Tests for the POST /api/orders endpoint and the GET /api/demand unit_cost
model change.

Test-isolation note: the module-global ``orders`` list is shared and mutated
across the whole pytest session. These tests therefore NEVER assert on list
length, total order counts, dashboard totals, or monthly-trend buckets. Every
created order is identified by the unique ``order_number``/``id`` returned from
its POST response.
"""
from datetime import datetime

import pytest


class TestDemandUnitCost:
    """Test suite for the demand forecast unit_cost model change."""

    def test_demand_returns_nine_items_with_numeric_unit_cost(self, client):
        """GET /api/demand returns 200, a list of 9 items, each with a numeric unit_cost."""
        response = client.get("/api/demand")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 9

        for forecast in data:
            assert "unit_cost" in forecast
            assert isinstance(forecast["unit_cost"], (int, float))


class TestCreateOrder:
    """Test suite for the POST /api/orders endpoint."""

    def test_create_order_happy_path(self, client):
        """POST /api/orders returns 201 with server-stamped fields and computed total."""
        payload = {
            "items": [
                {"sku": "PCB-001", "name": "Single Layer PCB Assembly",
                 "quantity": 10, "unit_price": 24.99},
                {"sku": "SPR-602", "name": "Compression Spring",
                 "quantity": 5, "unit_price": 89.5},
            ],
            "warehouse": "San Francisco",
            "category": "Circuit Boards",
        }
        response = client.post("/api/orders", json=payload)
        assert response.status_code == 201

        order = response.json()
        assert order["status"] == "Submitted"
        assert order["customer"] == "Restock (Internal)"
        assert order["actual_delivery"] is None

        expected_total = sum(item["quantity"] * item["unit_price"] for item in payload["items"])
        assert abs(order["total_value"] - expected_total) < 0.01

        # expected_delivery must be strictly after order_date (relation, not a
        # hardcoded day count).
        order_date = datetime.fromisoformat(order["order_date"])
        expected_delivery = datetime.fromisoformat(order["expected_delivery"])
        assert expected_delivery > order_date

    def test_create_order_surfaces_in_get_orders_by_status(self, client):
        """A created order appears in GET /api/orders?status=Submitted, matched by order_number."""
        payload = {
            "items": [
                {"sku": "PCB-001", "name": "Single Layer PCB Assembly",
                 "quantity": 3, "unit_price": 12.5},
            ],
        }
        create_response = client.post("/api/orders", json=payload)
        assert create_response.status_code == 201
        created_order_number = create_response.json()["order_number"]

        list_response = client.get("/api/orders?status=Submitted")
        assert list_response.status_code == 200

        order_numbers = [order["order_number"] for order in list_response.json()]
        assert created_order_number in order_numbers

    def test_create_order_returns_distinct_identifiers(self, client):
        """Two consecutive POSTs return distinct id and order_number values."""
        payload = {
            "items": [
                {"sku": "PCB-001", "name": "Single Layer PCB Assembly",
                 "quantity": 1, "unit_price": 10.0},
            ],
        }
        first = client.post("/api/orders", json=payload)
        second = client.post("/api/orders", json=payload)
        assert first.status_code == 201
        assert second.status_code == 201

        first_order = first.json()
        second_order = second.json()
        assert first_order["id"] != second_order["id"]
        assert first_order["order_number"] != second_order["order_number"]

    def test_create_order_total_value_computed_server_side(self, client):
        """total_value is derived server-side from item math, not trusted from the client."""
        payload = {
            "items": [
                {"sku": "SNR-420", "name": "Temperature Sensor Module",
                 "quantity": 7, "unit_price": 33.33},
                {"sku": "CTL-330", "name": "Logic Controller Board",
                 "quantity": 2, "unit_price": 150.0},
            ],
        }
        response = client.post("/api/orders", json=payload)
        assert response.status_code == 201

        order = response.json()
        expected_total = sum(item["quantity"] * item["unit_price"] for item in payload["items"])
        assert abs(order["total_value"] - expected_total) < 0.01


class TestCreateOrderValidation:
    """Test suite for POST /api/orders input validation."""

    def test_empty_items_returns_400(self, client):
        """An empty items list is rejected with 400."""
        response = client.post("/api/orders", json={"items": []})
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data

    def test_zero_quantity_returns_422(self, client):
        """A quantity of 0 violates the gt=0 constraint and returns 422."""
        payload = {
            "items": [
                {"sku": "PCB-001", "name": "Single Layer PCB Assembly",
                 "quantity": 0, "unit_price": 10.0},
            ],
        }
        response = client.post("/api/orders", json=payload)
        assert response.status_code == 422

    def test_negative_quantity_returns_422(self, client):
        """A negative quantity violates the gt=0 constraint and returns 422."""
        payload = {
            "items": [
                {"sku": "PCB-001", "name": "Single Layer PCB Assembly",
                 "quantity": -1, "unit_price": 10.0},
            ],
        }
        response = client.post("/api/orders", json=payload)
        assert response.status_code == 422

    def test_negative_unit_price_returns_422(self, client):
        """A negative unit_price violates the ge=0 constraint and returns 422."""
        payload = {
            "items": [
                {"sku": "PCB-001", "name": "Single Layer PCB Assembly",
                 "quantity": 5, "unit_price": -1.0},
            ],
        }
        response = client.post("/api/orders", json=payload)
        assert response.status_code == 422

    def test_missing_unit_price_returns_422(self, client):
        """An item missing the required unit_price field returns 422."""
        payload = {
            "items": [
                {"sku": "PCB-001", "name": "Single Layer PCB Assembly",
                 "quantity": 5},
            ],
        }
        response = client.post("/api/orders", json=payload)
        assert response.status_code == 422
