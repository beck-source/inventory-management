"""
Tests for restocking API endpoints (/api/restock/recommendations, /api/restock/orders).

Note: `restock_orders` is module-level state on the imported `main` app and is
NOT reset between tests within a pytest session (the `client` fixture creates a
fresh TestClient per test, but the underlying module is imported once). Tests
that place orders must assert against the specific order_number/data a POST
returns rather than assuming the list starts empty or hardcoding sequence
numbers like "PO-2026-0001".
"""
import re
from datetime import datetime

import pytest


@pytest.fixture
def sample_restock_line_items():
    """Two known items with different unit costs and lead times."""
    return [
        {"item_sku": "FLT-405", "quantity": 50},
        {"item_sku": "WDG-001", "quantity": 20}
    ]


class TestRestockRecommendationsEndpoint:
    """Test suite for GET /api/restock/recommendations."""

    def test_get_recommendations_happy_path(self, client):
        """Test getting recommendations for a mid-size budget."""
        response = client.get("/api/restock/recommendations?budget=5000")
        assert response.status_code == 200

        data = response.json()
        assert data["budget"] == 5000
        assert isinstance(data["items"], list)
        assert len(data["items"]) == 9

        calculated_total = sum(item["suggested_cost"] for item in data["items"])
        assert abs(data["total_suggested_cost"] - calculated_total) < 0.01
        assert abs(data["remaining_budget"] - (data["budget"] - data["total_suggested_cost"])) < 0.01

    def test_recommendations_worked_example_budget_5000(self, client):
        """Test the exact greedy-fill result at budget=5000."""
        response = client.get("/api/restock/recommendations?budget=5000")
        data = response.json()

        by_sku = {item["item_sku"]: item for item in data["items"]}
        assert by_sku["FLT-405"]["suggested_quantity"] == 340
        assert by_sku["WDG-001"]["suggested_quantity"] == 108
        assert by_sku["GSK-203"]["suggested_quantity"] == 1

        for sku in ["BRG-102", "MTR-304", "VLV-506", "PSU-501", "SNR-420", "CTL-330"]:
            assert by_sku[sku]["suggested_quantity"] == 0
            assert by_sku[sku]["within_budget"] is False

        assert abs(data["total_suggested_cost"] - 4993.25) < 0.01
        assert abs(data["remaining_budget"] - 6.75) < 0.01

    def test_recommendations_budget_zero(self, client):
        """Test that a zero budget suggests nothing."""
        response = client.get("/api/restock/recommendations?budget=0")
        assert response.status_code == 200

        data = response.json()
        for item in data["items"]:
            assert item["suggested_quantity"] == 0
            assert item["within_budget"] is False
        assert data["total_suggested_cost"] == 0

    def test_recommendations_budget_covers_everything(self, client):
        """Test that a huge budget suggests every item at its target quantity."""
        response = client.get("/api/restock/recommendations?budget=100000")
        assert response.status_code == 200

        data = response.json()
        for item in data["items"]:
            assert item["suggested_quantity"] == item["target_quantity"]
            assert item["within_budget"] is True
        assert data["remaining_budget"] > 0

    def test_recommendations_missing_budget_param(self, client):
        """Test that budget is a required query param."""
        response = client.get("/api/restock/recommendations")
        assert response.status_code == 422

    def test_recommendations_negative_budget(self, client):
        """Test that a negative budget is rejected."""
        response = client.get("/api/restock/recommendations?budget=-100")
        assert response.status_code == 422

    def test_recommendation_item_structure_and_types(self, client):
        """Test that every recommendation item has valid structure and types."""
        response = client.get("/api/restock/recommendations?budget=5000")
        data = response.json()

        for item in data["items"]:
            assert "item_sku" in item
            assert "item_name" in item
            assert "trend" in item
            assert isinstance(item["unit_cost"], (int, float))
            assert item["unit_cost"] >= 0
            assert isinstance(item["lead_time_days"], int)
            assert item["lead_time_days"] > 0
            assert isinstance(item["target_quantity"], int)
            assert isinstance(item["suggested_quantity"], int)
            assert item["suggested_quantity"] <= item["target_quantity"]
            assert isinstance(item["within_budget"], bool)

    def test_recommendations_priority_order(self, client):
        """Test that items are returned in priority-rank order."""
        response = client.get("/api/restock/recommendations?budget=5000")
        data = response.json()

        assert data["items"][0]["item_sku"] == "FLT-405"
        assert data["items"][-1]["item_sku"] == "MTR-304"


class TestRestockOrdersEndpoints:
    """Test suite for POST/GET /api/restock/orders."""

    def test_place_order_happy_path(self, client, sample_restock_line_items):
        """Test placing a valid multi-item restocking order."""
        response = client.post("/api/restock/orders", json={
            "budget": 5000,
            "items": sample_restock_line_items
        })
        assert response.status_code == 201

        order = response.json()
        assert re.match(r"^PO-2026-\d{4}$", order["order_number"])
        assert order["status"] == "Processing"
        assert len(order["items"]) == 2

        # Costs must come from the server-side catalog, not the client
        by_sku = {item["item_sku"]: item for item in order["items"]}
        assert by_sku["FLT-405"]["unit_cost"] == 4.50
        assert by_sku["FLT-405"]["line_total"] == 50 * 4.50
        assert by_sku["WDG-001"]["unit_cost"] == 32.00
        assert by_sku["WDG-001"]["line_total"] == 20 * 32.00

        calculated_total = sum(item["line_total"] for item in order["items"])
        assert abs(order["total_cost"] - calculated_total) < 0.01

    def test_place_order_computes_lead_time_and_delivery(self, client):
        """Test that lead time is the max across items and delivery date follows."""
        response = client.post("/api/restock/orders", json={
            "budget": 20000,
            "items": [
                {"item_sku": "FLT-405", "quantity": 10},   # lead_time_days = 5
                {"item_sku": "MTR-304", "quantity": 1}     # lead_time_days = 21
            ]
        })
        assert response.status_code == 201

        order = response.json()
        assert order["lead_time_days"] == 21

        created = datetime.fromisoformat(order["created_date"])
        expected = datetime.fromisoformat(order["expected_delivery"])
        assert (expected - created).days == 21

    def test_place_order_dates_format(self, client, sample_restock_line_items):
        """Test that date fields are ISO datetime strings."""
        response = client.post("/api/restock/orders", json={
            "budget": 5000,
            "items": sample_restock_line_items
        })
        order = response.json()

        assert "T" in order["created_date"]
        assert "T" in order["expected_delivery"]

    def test_place_order_empty_items(self, client):
        """Test that an order with no items is rejected."""
        response = client.post("/api/restock/orders", json={
            "budget": 5000,
            "items": []
        })
        assert response.status_code == 422

    def test_place_order_invalid_sku(self, client):
        """Test that an unknown SKU is rejected with a clear error."""
        response = client.post("/api/restock/orders", json={
            "budget": 5000,
            "items": [{"item_sku": "FAKE-999", "quantity": 10}]
        })
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert "FAKE-999" in data["detail"]

    def test_place_order_zero_quantity(self, client):
        """Test that a zero quantity line item is rejected."""
        response = client.post("/api/restock/orders", json={
            "budget": 5000,
            "items": [{"item_sku": "FLT-405", "quantity": 0}]
        })
        assert response.status_code == 422

    def test_place_order_negative_quantity(self, client):
        """Test that a negative quantity line item is rejected."""
        response = client.post("/api/restock/orders", json={
            "budget": 5000,
            "items": [{"item_sku": "FLT-405", "quantity": -5}]
        })
        assert response.status_code == 422

    def test_place_order_then_appears_in_get(self, client, sample_restock_line_items):
        """Test that a placed order shows up in the GET list."""
        post_response = client.post("/api/restock/orders", json={
            "budget": 5000,
            "items": sample_restock_line_items
        })
        placed_order = post_response.json()

        get_response = client.get("/api/restock/orders")
        assert get_response.status_code == 200

        all_orders = get_response.json()
        matching = [o for o in all_orders if o["order_number"] == placed_order["order_number"]]
        assert len(matching) == 1
        assert abs(matching[0]["total_cost"] - placed_order["total_cost"]) < 0.01
        assert matching[0]["items"] == placed_order["items"]

    def test_place_order_number_increments(self, client, sample_restock_line_items):
        """Test that sequential orders get incrementing order numbers."""
        first = client.post("/api/restock/orders", json={
            "budget": 5000,
            "items": sample_restock_line_items
        }).json()
        second = client.post("/api/restock/orders", json={
            "budget": 5000,
            "items": sample_restock_line_items
        }).json()

        first_seq = int(first["order_number"].split("-")[-1])
        second_seq = int(second["order_number"].split("-")[-1])
        assert second_seq == first_seq + 1

    def test_get_restock_orders_structure(self, client, sample_restock_line_items):
        """Test that GET returns orders matching the RestockOrder shape."""
        client.post("/api/restock/orders", json={
            "budget": 5000,
            "items": sample_restock_line_items
        })

        response = client.get("/api/restock/orders")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        order = data[0]
        for field in ["id", "order_number", "items", "total_cost", "budget",
                      "status", "created_date", "expected_delivery", "lead_time_days"]:
            assert field in order

    def test_get_restock_orders_sorted_most_recent_first(self, client, sample_restock_line_items):
        """Test that the most recently placed order appears first."""
        client.post("/api/restock/orders", json={
            "budget": 5000,
            "items": sample_restock_line_items
        })
        second = client.post("/api/restock/orders", json={
            "budget": 5000,
            "items": sample_restock_line_items
        }).json()

        response = client.get("/api/restock/orders")
        data = response.json()

        assert data[0]["order_number"] == second["order_number"]
