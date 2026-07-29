"""
Tests for restocking API endpoints.
"""
import pytest


class TestRestockingEndpoints:
    """Test suite for restocking-related endpoints."""

    def test_get_recommendations_returns_budget_max(self, client):
        """Test that recommendations endpoint returns a positive, stable budget_max."""
        response = client.get("/api/restocking/recommendations?budget=0")
        assert response.status_code == 200

        data = response.json()
        assert "budget_max" in data
        assert isinstance(data["budget_max"], (int, float))
        assert data["budget_max"] > 0

        # Should be stable across repeated calls regardless of budget param
        response_again = client.get("/api/restocking/recommendations?budget=999999")
        assert response_again.json()["budget_max"] == data["budget_max"]

    def test_recommendations_structure(self, client):
        """Test that recommended items have the expected fields."""
        response = client.get("/api/restocking/recommendations?budget=0")
        data = response.json()

        assert "budget" in data
        assert "recommended_items" in data
        assert "total_cost" in data
        assert isinstance(data["recommended_items"], list)

    def test_zero_budget_returns_no_items(self, client):
        """Test that a budget of 0 recommends no items but still exposes budget_max."""
        response = client.get("/api/restocking/recommendations?budget=0")
        assert response.status_code == 200

        data = response.json()
        assert data["recommended_items"] == []
        assert data["total_cost"] == 0

    def test_increasing_budget_never_decreases_recommendations(self, client):
        """Test that a larger budget never recommends fewer items or less total cost."""
        budget_max = client.get("/api/restocking/recommendations?budget=0").json()["budget_max"]

        low = client.get(f"/api/restocking/recommendations?budget={budget_max * 0.25}").json()
        mid = client.get(f"/api/restocking/recommendations?budget={budget_max * 0.5}").json()
        full = client.get(f"/api/restocking/recommendations?budget={budget_max}").json()

        assert len(low["recommended_items"]) <= len(mid["recommended_items"]) <= len(full["recommended_items"])
        assert low["total_cost"] <= mid["total_cost"] <= full["total_cost"]

    def test_full_budget_covers_every_candidate(self, client):
        """Test that budget == budget_max includes every recommendable item."""
        budget_max = client.get("/api/restocking/recommendations?budget=0").json()["budget_max"]

        response = client.get(f"/api/restocking/recommendations?budget={budget_max}")
        data = response.json()

        assert abs(data["total_cost"] - budget_max) < 0.01

    def test_items_only_included_when_fully_affordable(self, client):
        """Test that every recommended item's line_total fits within total_cost <= budget."""
        budget_max = client.get("/api/restocking/recommendations?budget=0").json()["budget_max"]
        budget = budget_max * 0.4

        response = client.get(f"/api/restocking/recommendations?budget={budget}")
        data = response.json()

        assert data["total_cost"] <= budget + 0.01
        calculated_total = sum(item["line_total"] for item in data["recommended_items"])
        assert abs(calculated_total - data["total_cost"]) < 0.01

    def test_submit_restocking_order(self, client):
        """Test submitting a restocking order returns a Submitted order with lead time."""
        payload = {
            "items": [
                {"sku": "WDG-001", "name": "Industrial Widget Type A", "quantity": 150, "unit_price": 15.5}
            ]
        }
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 200

        order = response.json()["order"]
        assert order["status"] == "Submitted"
        assert order["lead_time_days"] == 14
        assert order["total_value"] == 150 * 15.5

        from datetime import datetime
        order_date = datetime.fromisoformat(order["order_date"])
        expected_delivery = datetime.fromisoformat(order["expected_delivery"])
        assert (expected_delivery - order_date).days == 14

    def test_submitted_order_appears_in_orders(self, client):
        """Test that a submitted restocking order shows up via GET /api/orders."""
        payload = {
            "items": [
                {"sku": "GSK-203", "name": "High-Temperature Gasket", "quantity": 100, "unit_price": 8.5}
            ]
        }
        submit_response = client.post("/api/restocking/orders", json=payload)
        new_order_id = submit_response.json()["order"]["id"]

        orders_response = client.get("/api/orders")
        all_orders = orders_response.json()

        matching = [o for o in all_orders if o["id"] == new_order_id]
        assert len(matching) == 1
        assert matching[0]["status"] == "Submitted"

    def test_submit_empty_items_returns_400(self, client):
        """Test that submitting with no items is rejected."""
        response = client.post("/api/restocking/orders", json={"items": []})
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
