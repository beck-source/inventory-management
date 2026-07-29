"""
Tests for restocking API endpoints.
"""
import pytest


class TestRestockRecommendationsEndpoint:
    """Test suite for GET /api/restocking/recommendations."""

    def test_get_recommendations_zero_budget(self, client):
        """Test that a zero budget recommends nothing."""
        response = client.get("/api/restocking/recommendations?budget=0")
        assert response.status_code == 200

        data = response.json()
        assert data["budget"] == 0.0
        assert data["recommendations"] == []
        assert data["total_estimated_cost"] == 0.0
        assert data["remaining_budget"] == 0.0

    def test_get_recommendations_negative_budget_returns_400(self, client):
        """Test that a negative budget is rejected."""
        response = client.get("/api/restocking/recommendations?budget=-100")
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data

    def test_get_recommendations_worked_example(self, client):
        """Test the documented budget=5000 worked example produces exact expected output."""
        response = client.get("/api/restocking/recommendations?budget=5000")
        assert response.status_code == 200

        data = response.json()
        skus = [r["item_sku"] for r in data["recommendations"]]
        assert skus == ["WDG-001", "FLT-405"]
        assert data["total_estimated_cost"] == 4986.0
        assert data["remaining_budget"] == 14.0

        for rec in data["recommendations"]:
            assert rec["recommended_quantity"] == rec["demand_gap"]
            assert abs(rec["estimated_cost"] - rec["unit_cost"] * rec["recommended_quantity"]) < 0.01

    def test_get_recommendations_excludes_declining_items(self, client):
        """Test that items with forecasted_demand <= current_demand are never recommended."""
        response = client.get("/api/restocking/recommendations?budget=1000000")
        assert response.status_code == 200

        data = response.json()
        skus = [r["item_sku"] for r in data["recommendations"]]
        assert "MTR-304" not in skus

    def test_get_recommendations_ranked_by_demand_gap_descending(self, client):
        """Test that recommendations are ordered by descending demand gap."""
        response = client.get("/api/restocking/recommendations?budget=1000000")
        assert response.status_code == 200

        data = response.json()
        gaps = [r["demand_gap"] for r in data["recommendations"]]
        assert gaps == sorted(gaps, reverse=True)

    def test_get_recommendations_never_exceeds_budget(self, client):
        """Test that total estimated cost never exceeds the given budget."""
        response = client.get("/api/restocking/recommendations?budget=2000")
        assert response.status_code == 200

        data = response.json()
        assert data["total_estimated_cost"] <= 2000
        assert data["remaining_budget"] == round(2000 - data["total_estimated_cost"], 2)


class TestRestockOrdersEndpoint:
    """Test suite for POST/GET /api/restocking/orders."""

    def test_create_restock_order_success(self, client):
        """Test submitting a restock order returns the computed totals and lead time."""
        payload = {
            "budget": 5000,
            "items": [
                {"item_sku": "WDG-001", "item_name": "Industrial Widget Type A", "quantity": 150, "unit_cost": 24.99},
                {"item_sku": "FLT-405", "item_name": "Oil Filter Cartridge", "quantity": 150, "unit_cost": 8.25}
            ]
        }
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 201

        data = response.json()
        assert data["order_number"].startswith("RSO-")
        assert data["total_cost"] == 4986.0
        assert data["total_quantity"] == 300
        assert data["lead_time_days"] == 11
        assert data["status"] == "Submitted"

    def test_create_restock_order_empty_items_returns_400(self, client):
        """Test that submitting an order with no items is rejected."""
        response = client.post("/api/restocking/orders", json={"budget": 1000, "items": []})
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data

    def test_get_restock_orders_includes_submitted_order(self, client):
        """Test that a submitted order appears in the restocking orders list."""
        payload = {
            "budget": 1000,
            "items": [
                {"item_sku": "GSK-203", "item_name": "High-Temperature Gasket", "quantity": 10, "unit_cost": 12.75}
            ]
        }
        created = client.post("/api/restocking/orders", json=payload).json()

        response = client.get("/api/restocking/orders")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        order_numbers = [o["order_number"] for o in data]
        assert created["order_number"] in order_numbers

    def test_restock_orders_are_separate_from_regular_orders(self, client):
        """Test that submitting a restock order does not affect /api/orders."""
        before = client.get("/api/orders").json()

        payload = {
            "budget": 500,
            "items": [
                {"item_sku": "VLV-506", "item_name": "Pressure Relief Valve", "quantity": 1, "unit_cost": 156.00}
            ]
        }
        client.post("/api/restocking/orders", json=payload)

        after = client.get("/api/orders").json()
        assert len(after) == len(before)


class TestDemandForecastUnitCostRegression:
    """Regression checks on the demand forecast unit_cost backfill."""

    def test_demand_forecasts_have_unit_cost(self, client):
        """Test that every demand forecast item has a positive unit_cost after the backfill."""
        response = client.get("/api/demand")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0
        for item in data:
            assert "unit_cost" in item
            assert isinstance(item["unit_cost"], (int, float))
            assert item["unit_cost"] > 0
