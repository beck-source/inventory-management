"""
Tests for restocking API endpoints.
"""
from datetime import datetime

import pytest


class TestRestockingRecommendations:
    """Test suite for GET /api/restocking/recommendations."""

    def test_get_recommendations_structure(self, client):
        """Test that recommendations return the expected top-level fields."""
        response = client.get("/api/restocking/recommendations?warehouse=London&budget=100000")
        assert response.status_code == 200

        data = response.json()
        for field in ["warehouse", "budget", "lead_time_days", "items", "total_cost", "remaining_budget"]:
            assert field in data
        assert data["warehouse"] == "London"
        assert data["lead_time_days"] == 21

    def test_recommendations_item_structure(self, client):
        """Test that each recommended item has the expected fields."""
        response = client.get("/api/restocking/recommendations?warehouse=London&budget=100000")
        data = response.json()
        assert len(data["items"]) > 0

        for item in data["items"]:
            for field in ["sku", "name", "forecasted_demand", "current_stock", "shortfall",
                          "unit_cost", "recommended_quantity", "line_total"]:
                assert field in item
            assert 0 < item["recommended_quantity"] <= item["shortfall"]

    def test_recommendations_respect_budget(self, client):
        """Test that total cost never exceeds the budget."""
        budget = 2500
        response = client.get(f"/api/restocking/recommendations?warehouse=Tokyo&budget={budget}")
        data = response.json()

        assert data["total_cost"] <= budget
        assert data["remaining_budget"] == pytest.approx(budget - data["total_cost"], abs=0.01)

    def test_recommendations_line_totals_match_costs(self, client):
        """Test that line totals equal quantity times unit cost."""
        response = client.get("/api/restocking/recommendations?warehouse=San Francisco&budget=50000")
        data = response.json()

        for item in data["items"]:
            assert abs(item["line_total"] - item["recommended_quantity"] * item["unit_cost"]) < 0.01

        assert abs(data["total_cost"] - sum(i["line_total"] for i in data["items"])) < 0.01

    def test_recommendations_ranked_by_shortfall(self, client):
        """Test that items are ordered by shortfall, largest first."""
        response = client.get("/api/restocking/recommendations?warehouse=London&budget=1000000")
        shortfalls = [item["shortfall"] for item in response.json()["items"]]
        assert shortfalls == sorted(shortfalls, reverse=True)

    def test_zero_budget_recommends_nothing(self, client):
        """Test that a zero budget yields no recommendations."""
        response = client.get("/api/restocking/recommendations?warehouse=Tokyo&budget=0")
        data = response.json()
        assert data["items"] == []
        assert data["total_cost"] == 0

    def test_negative_budget_rejected(self, client):
        """Test that a negative budget returns 400."""
        response = client.get("/api/restocking/recommendations?warehouse=Tokyo&budget=-1")
        assert response.status_code == 400

    def test_unknown_warehouse_rejected(self, client):
        """Test that an unknown warehouse returns 400."""
        response = client.get("/api/restocking/recommendations?warehouse=Mars&budget=1000")
        assert response.status_code == 400
        assert "detail" in response.json()


class TestRestockingOrders:
    """Test suite for POST /api/restocking/orders."""

    def _sample_payload(self):
        return {
            "warehouse": "Tokyo",
            "items": [
                {"sku": "PSU-501", "name": "Power Supply Unit", "quantity": 10, "unit_price": 18.99},
                {"sku": "CTL-330", "name": "Controller", "quantity": 2, "unit_price": 128.00},
            ],
        }

    def test_submit_restocking_order(self, client):
        """Test that a valid order is created with status 201."""
        response = client.post("/api/restocking/orders", json=self._sample_payload())
        assert response.status_code == 201

        order = response.json()
        assert order["source"] == "restocking"
        assert order["status"] == "Processing"
        assert order["warehouse"] == "Tokyo"
        assert order["order_number"].startswith("RST-")

    def test_submitted_order_total_value(self, client):
        """Test that the server computes the order total from its items."""
        response = client.post("/api/restocking/orders", json=self._sample_payload())
        order = response.json()
        expected = round(10 * 18.99 + 2 * 128.00, 2)
        assert order["total_value"] == pytest.approx(expected, abs=0.01)

    def test_submitted_order_lead_time(self, client):
        """Test that expected delivery is the warehouse lead time after the order date."""
        response = client.post("/api/restocking/orders", json=self._sample_payload())
        order = response.json()

        ordered = datetime.fromisoformat(order["order_date"])
        expected = datetime.fromisoformat(order["expected_delivery"])
        assert (expected - ordered).days == 18  # Tokyo lead time

    def test_submitted_order_appears_in_orders(self, client):
        """Test that a submitted order is visible through GET /api/orders."""
        created = client.post("/api/restocking/orders", json=self._sample_payload()).json()

        response = client.get("/api/orders?warehouse=Tokyo")
        ids = [o["id"] for o in response.json()]
        assert created["id"] in ids

        restocking = [o for o in response.json() if o.get("source") == "restocking"]
        assert len(restocking) > 0

    def test_empty_order_rejected(self, client):
        """Test that an order without items returns 400."""
        response = client.post("/api/restocking/orders", json={"warehouse": "Tokyo", "items": []})
        assert response.status_code == 400

    def test_non_positive_quantity_rejected(self, client):
        """Test that a zero quantity returns 400."""
        payload = self._sample_payload()
        payload["items"][0]["quantity"] = 0
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 400

    def test_unknown_warehouse_order_rejected(self, client):
        """Test that an order for an unknown warehouse returns 400."""
        payload = self._sample_payload()
        payload["warehouse"] = "Mars"
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 400
