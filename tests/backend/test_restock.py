"""
Tests for restocking recommendation and order endpoints.
"""
import pytest


class TestRestockRecommendations:
    """Test suite for GET /api/restock/recommendations."""

    def test_get_recommendations(self, client):
        """Test getting recommendations with a generous budget."""
        response = client.get("/api/restock/recommendations?budget=100000")
        assert response.status_code == 200

        data = response.json()
        assert data["budget"] == 100000
        assert isinstance(data["recommendations"], list)
        assert len(data["recommendations"]) > 0

        rec = data["recommendations"][0]
        for field in ["item_sku", "item_name", "current_stock", "forecasted_demand",
                      "shortfall", "trend", "unit_cost", "recommended_quantity",
                      "estimated_cost"]:
            assert field in rec

    def test_recommendations_within_budget(self, client):
        """Test that total cost never exceeds the budget."""
        for budget in [500, 5000, 25000, 100000]:
            response = client.get(f"/api/restock/recommendations?budget={budget}")
            data = response.json()
            assert data["total_cost"] <= budget
            assert data["remaining_budget"] == pytest.approx(budget - data["total_cost"], abs=0.01)

    def test_recommendations_ranked_by_shortfall(self, client):
        """Test that recommendations are ordered by biggest shortfall first."""
        response = client.get("/api/restock/recommendations?budget=1000000")
        recs = response.json()["recommendations"]

        shortfalls = [r["shortfall"] for r in recs]
        assert shortfalls == sorted(shortfalls, reverse=True)

    def test_recommendation_quantities_capped_at_shortfall(self, client):
        """Test that recommended quantity never exceeds the shortfall."""
        response = client.get("/api/restock/recommendations?budget=1000000")
        for rec in response.json()["recommendations"]:
            assert 0 < rec["recommended_quantity"] <= rec["shortfall"]
            assert rec["estimated_cost"] == pytest.approx(
                rec["recommended_quantity"] * rec["unit_cost"], abs=0.01)

    def test_zero_budget_returns_no_recommendations(self, client):
        """Test that a zero budget yields an empty recommendation list."""
        response = client.get("/api/restock/recommendations?budget=0")
        assert response.status_code == 200
        data = response.json()
        assert data["recommendations"] == []
        assert data["total_cost"] == 0

    def test_negative_budget_rejected(self, client):
        """Test that a negative budget returns 400."""
        response = client.get("/api/restock/recommendations?budget=-100")
        assert response.status_code == 400

    def test_missing_budget_rejected(self, client):
        """Test that the budget query param is required."""
        response = client.get("/api/restock/recommendations")
        assert response.status_code == 422

    def test_current_stock_reflects_inventory(self, client):
        """Test that current stock comes from inventory (PSU-501 exists there)."""
        response = client.get("/api/restock/recommendations?budget=1000000")
        recs = {r["item_sku"]: r for r in response.json()["recommendations"]}

        # PSU-501 is in inventory with stock on hand, so its shortfall must be
        # smaller than its forecasted demand
        if "PSU-501" in recs:
            psu = recs["PSU-501"]
            assert psu["current_stock"] > 0
            assert psu["shortfall"] == psu["forecasted_demand"] - psu["current_stock"]


class TestRestockOrders:
    """Test suite for POST/GET /api/restock/orders."""

    def _sample_request(self):
        return {
            "budget": 10000,
            "items": [
                {"item_sku": "WDG-001", "item_name": "Industrial Widget Type A",
                 "quantity": 100, "unit_cost": 45.00},
                {"item_sku": "GSK-203", "item_name": "High-Temperature Gasket",
                 "quantity": 200, "unit_cost": 8.75}
            ]
        }

    def test_create_restock_order(self, client):
        """Test submitting a restocking order."""
        response = client.post("/api/restock/orders", json=self._sample_request())
        assert response.status_code == 201

        order = response.json()
        assert order["order_number"].startswith("RST-")
        assert order["status"] == "Submitted"
        assert order["lead_time_days"] == 10
        assert order["total_value"] == pytest.approx(100 * 45.00 + 200 * 8.75, abs=0.01)
        assert len(order["items"]) == 2

    def test_expected_delivery_matches_lead_time(self, client):
        """Test that expected delivery is order date plus lead time."""
        from datetime import date, timedelta

        response = client.post("/api/restock/orders", json=self._sample_request())
        order = response.json()

        order_date = date.fromisoformat(order["order_date"])
        expected = date.fromisoformat(order["expected_delivery"])
        assert expected - order_date == timedelta(days=order["lead_time_days"])

    def test_submitted_order_appears_in_list(self, client):
        """Test that a submitted order is returned by GET /api/restock/orders."""
        created = client.post("/api/restock/orders", json=self._sample_request()).json()

        response = client.get("/api/restock/orders")
        assert response.status_code == 200
        order_numbers = [o["order_number"] for o in response.json()]
        assert created["order_number"] in order_numbers

    def test_order_numbers_are_unique(self, client):
        """Test that consecutive orders get distinct order numbers."""
        first = client.post("/api/restock/orders", json=self._sample_request()).json()
        second = client.post("/api/restock/orders", json=self._sample_request()).json()
        assert first["order_number"] != second["order_number"]

    def test_empty_order_rejected(self, client):
        """Test that an order with no items returns 400."""
        response = client.post("/api/restock/orders", json={"budget": 1000, "items": []})
        assert response.status_code == 400

    def test_non_positive_quantity_rejected(self, client):
        """Test that zero/negative quantities return 400."""
        request = self._sample_request()
        request["items"][0]["quantity"] = 0
        response = client.post("/api/restock/orders", json=request)
        assert response.status_code == 400

    def test_order_exceeding_budget_rejected(self, client):
        """Test that an order costing more than the budget returns 400."""
        request = self._sample_request()
        request["budget"] = 10
        response = client.post("/api/restock/orders", json=request)
        assert response.status_code == 400
