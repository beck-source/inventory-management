"""
Tests for restocking API endpoints.
"""
import pytest


class TestRestockingRecommendations:
    """Test suite for GET /api/restocking/recommendations."""

    def test_get_recommendations_default_budget(self, client):
        """Test getting recommendations with the default budget."""
        response = client.get("/api/restocking/recommendations")
        assert response.status_code == 200

        data = response.json()
        assert "budget" in data
        assert "recommendations" in data
        assert "total_recommended_cost" in data
        assert "unmatched_forecast_count" in data
        assert isinstance(data["recommendations"], list)

    def test_recommendation_structure(self, client):
        """Test that each recommendation has the expected fields and types."""
        response = client.get("/api/restocking/recommendations?budget=10000")
        assert response.status_code == 200

        data = response.json()
        assert len(data["recommendations"]) > 0

        item = data["recommendations"][0]
        for field in [
            "sku", "item_name", "category", "current_demand", "forecasted_demand",
            "demand_gap", "recommended_quantity", "unit_cost", "subtotal",
            "lead_time_days", "fits_budget"
        ]:
            assert field in item

        assert isinstance(item["demand_gap"], int)
        assert item["demand_gap"] > 0
        assert item["demand_gap"] == item["forecasted_demand"] - item["current_demand"]
        assert isinstance(item["fits_budget"], bool)

    def test_only_positive_demand_gap_items_recommended(self, client):
        """Test that recommendations only include items with a positive demand gap."""
        response = client.get("/api/restocking/recommendations?budget=100000")
        data = response.json()

        for item in data["recommendations"]:
            assert item["forecasted_demand"] > item["current_demand"]

    def test_zero_budget_returns_no_fitting_items(self, client):
        """Test that a budget of 0 marks every candidate as not fitting."""
        response = client.get("/api/restocking/recommendations?budget=0")
        assert response.status_code == 200

        data = response.json()
        assert data["total_recommended_cost"] == 0
        for item in data["recommendations"]:
            assert item["fits_budget"] is False

    def test_recommendations_sorted_by_demand_gap_descending(self, client):
        """Test that recommendations are sorted by demand gap, largest first."""
        response = client.get("/api/restocking/recommendations?budget=100000")
        data = response.json()

        gaps = [item["demand_gap"] for item in data["recommendations"]]
        assert gaps == sorted(gaps, reverse=True)

    def test_unmatched_forecast_count_present(self, client):
        """Test that forecasts with no matching inventory sku are counted, not dropped silently."""
        response = client.get("/api/restocking/recommendations?budget=10000")
        data = response.json()

        assert isinstance(data["unmatched_forecast_count"], int)
        assert data["unmatched_forecast_count"] >= 0


class TestCreateRestockingOrder:
    """Test suite for POST /api/restocking/order."""

    def test_create_order_happy_path(self, client):
        """Test submitting a valid restocking order."""
        response = client.post(
            "/api/restocking/order",
            json={"items": [{"sku": "PSU-501", "quantity": 5}], "budget": 5000},
        )
        assert response.status_code == 201

        order = response.json()
        assert order["order_number"].startswith("RST-")
        assert len(order["items"]) == 1
        assert order["items"][0]["sku"] == "PSU-501"
        assert order["items"][0]["quantity"] == 5
        assert order["total_cost"] == round(5 * order["items"][0]["unit_cost"], 2)
        assert order["lead_time_days"] > 0
        assert order["status"] == "Pending"
        assert "created_date" in order
        assert "expected_delivery" in order

    def test_create_order_empty_items_returns_400(self, client):
        """Test that submitting an order with no items is rejected."""
        response = client.post("/api/restocking/order", json={"items": []})
        assert response.status_code == 400

    def test_create_order_unknown_sku_returns_404(self, client):
        """Test that an unknown sku is rejected."""
        response = client.post(
            "/api/restocking/order",
            json={"items": [{"sku": "NOT-A-REAL-SKU", "quantity": 1}]},
        )
        assert response.status_code == 404

    def test_create_order_non_positive_quantity_returns_400(self, client):
        """Test that a zero/negative quantity is rejected."""
        response = client.post(
            "/api/restocking/order",
            json={"items": [{"sku": "PSU-501", "quantity": 0}]},
        )
        assert response.status_code == 400

    def test_created_order_lead_time_is_max_across_categories(self, client):
        """Test that a multi-category order's lead time is the max across its items."""
        response = client.post(
            "/api/restocking/order",
            json={
                "items": [
                    {"sku": "PSU-501", "quantity": 1},   # Power Supplies -> 18 days
                    {"sku": "TMP-201", "quantity": 1},   # Sensors -> 10 days
                ]
            },
        )
        assert response.status_code == 201
        order = response.json()
        assert order["lead_time_days"] == 18


class TestGetRestockingOrders:
    """Test suite for GET /api/restocking/orders."""

    def test_submitted_order_appears_in_list(self, client):
        """Test that a submitted order shows up in the list endpoint."""
        create_response = client.post(
            "/api/restocking/order",
            json={"items": [{"sku": "PSU-501", "quantity": 3}]},
        )
        assert create_response.status_code == 201
        created_order = create_response.json()

        list_response = client.get("/api/restocking/orders")
        assert list_response.status_code == 200

        orders = list_response.json()
        assert any(o["id"] == created_order["id"] for o in orders)
