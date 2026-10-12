"""
Tests for restocking API endpoints.
"""
import pytest


class TestRestockingRecommendationsEndpoint:
    """Test suite for GET /api/restocking/recommendations."""

    def test_get_recommendations_basic(self, client):
        """Test getting recommendations for a reasonable budget."""
        response = client.get("/api/restocking/recommendations?budget=5000")
        assert response.status_code == 200

        data = response.json()
        assert data["budget"] == 5000
        assert isinstance(data["recommendations"], list)
        assert data["total_gap"] > 0
        assert len(data["recommendations"]) > 0

        first = data["recommendations"][0]
        assert "item_sku" in first
        assert "item_name" in first
        assert "gap" in first
        assert "unit_cost" in first
        assert "lead_time_days" in first
        assert "recommended_quantity" in first
        assert "estimated_cost" in first

    def test_recommendations_exclude_zero_gap_items(self, client):
        """Test that items with forecasted_demand <= current_demand are excluded."""
        response = client.get("/api/restocking/recommendations?budget=5000")
        data = response.json()

        # MTR-304 has forecasted_demand (35) < current_demand (50), gap == 0
        skus = [r["item_sku"] for r in data["recommendations"]]
        assert "MTR-304" not in skus

    def test_recommendations_proportional_to_gap(self, client):
        """Test that items with larger demand gaps receive proportionally larger budget allocations."""
        response = client.get("/api/restocking/recommendations?budget=5000")
        data = response.json()

        by_sku = {r["item_sku"]: r for r in data["recommendations"]}
        # WDG-001 gap=150, PSU-501 gap=2 -- WDG-001 should get a much larger allocated_budget
        assert by_sku["WDG-001"]["gap"] > by_sku["PSU-501"]["gap"]
        assert by_sku["WDG-001"]["allocated_budget"] > by_sku["PSU-501"]["allocated_budget"]

    def test_recommendations_quantity_within_allocated_budget(self, client):
        """Test that estimated_cost never exceeds the item's allocated_budget."""
        response = client.get("/api/restocking/recommendations?budget=5000")
        data = response.json()

        for rec in data["recommendations"]:
            assert rec["estimated_cost"] <= rec["allocated_budget"] + 0.01
            assert rec["recommended_quantity"] >= 1

    def test_recommendations_total_allocated_within_budget(self, client):
        """Test that total_allocated never exceeds the requested budget."""
        response = client.get("/api/restocking/recommendations?budget=5000")
        data = response.json()

        assert data["total_allocated"] <= data["budget"] + 0.01
        assert abs(data["remaining_budget"] - (data["budget"] - data["total_allocated"])) < 0.01

    def test_recommendations_small_budget_may_exclude_expensive_items(self, client):
        """Test that a very small budget yields fewer or no recommendations for expensive items."""
        response = client.get("/api/restocking/recommendations?budget=1")
        assert response.status_code == 200

        data = response.json()
        # A $1 budget split proportionally across many items can't afford a single unit of most items
        for rec in data["recommendations"]:
            assert rec["recommended_quantity"] >= 1

    def test_recommendations_zero_budget_rejected(self, client):
        """Test that a budget of 0 is rejected."""
        response = client.get("/api/restocking/recommendations?budget=0")
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_recommendations_negative_budget_rejected(self, client):
        """Test that a negative budget is rejected."""
        response = client.get("/api/restocking/recommendations?budget=-100")
        assert response.status_code == 400

    def test_recommendations_missing_budget_rejected(self, client):
        """Test that omitting the required budget param returns a validation error."""
        response = client.get("/api/restocking/recommendations")
        assert response.status_code == 422

    def test_recommendations_sorted_by_gap_descending(self, client):
        """Test that recommendations are sorted by gap, largest first."""
        response = client.get("/api/restocking/recommendations?budget=5000")
        data = response.json()

        gaps = [r["gap"] for r in data["recommendations"]]
        assert gaps == sorted(gaps, reverse=True)


class TestRestockingOrdersEndpoint:
    """Test suite for POST/GET /api/restocking/orders."""

    def test_submit_order_success(self, client):
        """Test submitting a restock order."""
        payload = {
            "budget": 1000,
            "items": [
                {
                    "item_sku": "WDG-001",
                    "item_name": "Industrial Widget Type A",
                    "quantity": 10,
                    "unit_cost": 12.5,
                    "lead_time_days": 7
                },
                {
                    "item_sku": "GSK-203",
                    "item_name": "High-Temperature Gasket",
                    "quantity": 20,
                    "unit_cost": 4.25,
                    "lead_time_days": 5
                }
            ]
        }
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 200

        order = response.json()
        assert order["status"] == "Submitted"
        assert order["order_number"].startswith("RSO-")
        assert order["budget"] == 1000
        assert order["max_lead_time_days"] == 7
        expected_total = 10 * 12.5 + 20 * 4.25
        assert abs(order["total_cost"] - expected_total) < 0.01

    def test_submit_order_empty_items_rejected(self, client):
        """Test that an order with no items is rejected."""
        response = client.post("/api/restocking/orders", json={"budget": 500, "items": []})
        assert response.status_code == 400

    def test_submitted_order_appears_in_get(self, client):
        """Test that a submitted order is retrievable via GET /api/restocking/orders."""
        payload = {
            "budget": 300,
            "items": [
                {
                    "item_sku": "FLT-405",
                    "item_name": "Oil Filter Cartridge",
                    "quantity": 15,
                    "unit_cost": 6.9,
                    "lead_time_days": 4
                }
            ]
        }
        post_response = client.post("/api/restocking/orders", json=payload)
        created_order = post_response.json()

        get_response = client.get("/api/restocking/orders")
        assert get_response.status_code == 200

        orders = get_response.json()
        assert isinstance(orders, list)
        order_numbers = [o["order_number"] for o in orders]
        assert created_order["order_number"] in order_numbers

    def test_max_lead_time_days_is_max_of_items(self, client):
        """Test that max_lead_time_days reflects the longest lead time among order items."""
        payload = {
            "budget": 500,
            "items": [
                {"item_sku": "GSK-203", "item_name": "High-Temperature Gasket", "quantity": 5, "unit_cost": 4.25, "lead_time_days": 5},
                {"item_sku": "PSU-501", "item_name": "5V 10A Switching Power Supply", "quantity": 5, "unit_cost": 18.4, "lead_time_days": 14},
                {"item_sku": "WDG-001", "item_name": "Industrial Widget Type A", "quantity": 5, "unit_cost": 12.5, "lead_time_days": 7}
            ]
        }
        response = client.post("/api/restocking/orders", json=payload)
        order = response.json()
        assert order["max_lead_time_days"] == 14
