"""
Tests for restocking API endpoints.
"""
import pytest


class TestRestockingEndpoints:
    """Test suite for restocking-related endpoints."""

    def test_get_recommendations_within_budget(self, client):
        """Test that recommendations never exceed the given budget."""
        response = client.get("/api/restocking/recommendations?budget=5000")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        total = sum(item["line_total"] for item in data)
        assert total <= 5000

    def test_get_recommendations_zero_budget(self, client):
        """Test that a zero budget returns no recommendations."""
        response = client.get("/api/restocking/recommendations?budget=0")
        assert response.status_code == 200
        assert response.json() == []

    def test_recommendations_exclude_decreasing_trend(self, client):
        """Test that items with decreasing demand are never recommended."""
        response = client.get("/api/restocking/recommendations?budget=1000000")
        assert response.status_code == 200

        data = response.json()
        for item in data:
            assert item["trend"] != "decreasing"

    def test_recommendations_respect_warehouse_filter(self, client):
        """Test filtering recommendations by warehouse."""
        response = client.get("/api/restocking/recommendations?budget=1000000&warehouse=Tokyo")
        assert response.status_code == 200

        data = response.json()
        for item in data:
            assert item["warehouse"] == "Tokyo"

    def test_recommendations_respect_category_filter(self, client):
        """Test filtering recommendations by category."""
        response = client.get("/api/restocking/recommendations?budget=1000000&category=Sensors")
        assert response.status_code == 200

        data = response.json()
        for item in data:
            assert item["category"].lower() == "sensors"

    def test_recommendation_fields(self, client):
        """Test that recommendations have all required fields with correct types."""
        response = client.get("/api/restocking/recommendations?budget=1000000")
        data = response.json()
        assert len(data) > 0

        required_fields = [
            "item_sku", "item_name", "category", "warehouse", "unit_cost",
            "current_demand", "forecasted_demand", "trend",
            "recommended_quantity", "line_total"
        ]
        for item in data:
            for field in required_fields:
                assert field in item, f"Missing field: {field}"
            assert isinstance(item["recommended_quantity"], int)
            assert item["recommended_quantity"] > 0

    def test_place_order_creates_submitted_order(self, client):
        """Test that placing a restock order adds it to the submitted orders list."""
        request_body = {
            "items": [
                {"item_sku": "PCB-001", "item_name": "Single Layer PCB Assembly", "quantity": 10, "unit_cost": 24.99}
            ],
            "budget": 500
        }
        response = client.post("/api/restocking/orders", json=request_body)
        assert response.status_code == 200

        order = response.json()
        assert order["total_cost"] == pytest.approx(249.9)
        assert order["lead_time_days"] == 14
        assert order["status"] == "Submitted"
        assert "order_number" in order
        assert "expected_delivery_date" in order

        # Confirm it shows up in the submitted orders list
        list_response = client.get("/api/restocking/orders")
        assert list_response.status_code == 200
        order_ids = [o["id"] for o in list_response.json()]
        assert order["id"] in order_ids

    def test_place_order_rejects_empty_items(self, client):
        """Test that an order with no items is rejected."""
        response = client.post("/api/restocking/orders", json={"items": [], "budget": 500})
        assert response.status_code == 400

    def test_get_restock_orders_returns_list(self, client):
        """Test that the submitted orders endpoint always returns a list."""
        response = client.get("/api/restocking/orders")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
