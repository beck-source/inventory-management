"""
Tests for restocking endpoints.
"""
import pytest


class TestRestockingEndpoints:
    """Test suite for restocking recommendation and order submission."""

    def test_get_restocking_recommendations(self, client):
        """Test getting restocking recommendations with budget."""
        response = client.get("/api/restocking/recommendations?budget=100000")
        assert response.status_code == 200

        data = response.json()
        assert "recommendations" in data
        assert "total_cost" in data
        assert "available_budget" in data
        assert "remaining_budget" in data
        assert "items_count" in data

        assert data["available_budget"] == 100000
        assert data["total_cost"] <= 100000

    def test_recommendations_with_filters(self, client):
        """Test recommendations with warehouse and category filters."""
        response = client.get(
            "/api/restocking/recommendations?budget=50000&warehouse=San+Francisco&category=Sensors"
        )
        assert response.status_code == 200
        data = response.json()

        # All recommendations should match filters
        for rec in data["recommendations"]:
            assert rec["warehouse"] == "San Francisco"
            assert rec["category"] == "Sensors"

    def test_recommendations_sorted_by_priority(self, client):
        """Test that recommendations are sorted by priority score."""
        response = client.get("/api/restocking/recommendations?budget=200000")
        data = response.json()

        recommendations = data["recommendations"]
        if len(recommendations) > 1:
            # Check descending order
            for i in range(len(recommendations) - 1):
                assert recommendations[i]["priority_score"] >= recommendations[i + 1]["priority_score"]

    def test_recommendations_within_budget(self, client):
        """Test that recommendations stay within budget."""
        budget = 50000
        response = client.get(f"/api/restocking/recommendations?budget={budget}")
        data = response.json()

        assert data["total_cost"] <= budget
        assert data["remaining_budget"] >= 0

    def test_submit_restocking_order(self, client):
        """Test submitting a restocking order."""
        order_data = {
            "budget": 100000,
            "recommendations": [
                {
                    "item_sku": "PCB-001",
                    "item_name": "Single Layer PCB Assembly",
                    "category": "Circuit Boards",
                    "warehouse": "San Francisco",
                    "quantity": 100,
                    "unit_cost": 24.99
                }
            ]
        }

        response = client.post("/api/restocking/submit", json=order_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["orders_created"] == 1
        assert len(data["order_ids"]) == 1
        assert data["total_cost"] == 2499.0

    def test_get_purchase_orders(self, client):
        """Test getting all purchase orders."""
        response = client.get("/api/purchase-orders")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_recommendation_structure(self, client):
        """Test that recommendation objects have correct structure."""
        response = client.get("/api/restocking/recommendations?budget=100000")
        data = response.json()

        if data["recommendations"]:
            rec = data["recommendations"][0]
            required_fields = [
                "item_sku", "item_name", "category", "warehouse",
                "current_stock", "reorder_point", "forecasted_demand",
                "current_demand", "recommended_quantity", "unit_cost",
                "total_cost", "priority_score", "lead_time_days"
            ]
            for field in required_fields:
                assert field in rec

    def test_recommendations_low_budget(self, client):
        """Test recommendations with very low budget."""
        response = client.get("/api/restocking/recommendations?budget=100")
        data = response.json()

        # Should return empty or very few recommendations
        assert data["total_cost"] <= 100
        assert data["remaining_budget"] >= 0

    def test_recommendations_high_budget(self, client):
        """Test recommendations with high budget."""
        response = client.get("/api/restocking/recommendations?budget=1000000")
        data = response.json()

        # Should return many recommendations
        assert data["available_budget"] == 1000000
        assert data["items_count"] >= 0

    def test_submit_multiple_items(self, client):
        """Test submitting multiple items in one order."""
        order_data = {
            "budget": 200000,
            "recommendations": [
                {
                    "item_sku": "PCB-001",
                    "item_name": "Single Layer PCB Assembly",
                    "category": "Circuit Boards",
                    "warehouse": "San Francisco",
                    "quantity": 100,
                    "unit_cost": 24.99
                },
                {
                    "item_sku": "SNS-201",
                    "item_name": "Temperature Sensor Module",
                    "category": "Sensors",
                    "warehouse": "Tokyo",
                    "quantity": 50,
                    "unit_cost": 15.50
                }
            ]
        }

        response = client.post("/api/restocking/submit", json=order_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["orders_created"] == 2
        assert len(data["order_ids"]) == 2

        # Verify each order has correct fields
        for order in data["orders"]:
            assert "id" in order
            assert "item_sku" in order
            assert "supplier_name" in order
            assert "expected_delivery_date" in order
            assert order["status"] == "Pending"

    def test_category_lead_times(self, client):
        """Test that different categories have different lead times."""
        response = client.get("/api/restocking/recommendations?budget=500000")
        data = response.json()

        # Collect unique lead times by category
        lead_times_by_category = {}
        for rec in data["recommendations"]:
            category = rec["category"]
            lead_time = rec["lead_time_days"]
            if category not in lead_times_by_category:
                lead_times_by_category[category] = lead_time

        # Verify expected lead times match CATEGORY_LEAD_TIMES
        expected = {
            'Circuit Boards': 7,
            'Sensors': 10,
            'Actuators': 14,
            'Controllers': 12,
            'Power Supplies': 5
        }

        for category, lead_time in lead_times_by_category.items():
            if category in expected:
                assert lead_time == expected[category]
