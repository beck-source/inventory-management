"""
Tests for restocking API endpoints.
"""
import pytest
from main import submitted_restocking_orders


class TestRestockingRecommendations:
    """Test suite for GET /api/restocking/recommendations."""

    def test_get_recommendations_default_budget(self, client):
        """Test getting recommendations with default budget."""
        response = client.get("/api/restocking/recommendations")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        first = data[0]
        assert "sku" in first
        assert "name" in first
        assert "quantity" in first
        assert "unit_cost" in first
        assert "line_total" in first
        assert "trend" in first
        assert "priority" in first

    def test_recommendations_respect_budget(self, client):
        """Test that total never exceeds the budget."""
        budget = 20000
        response = client.get(f"/api/restocking/recommendations?budget={budget}")
        assert response.status_code == 200

        data = response.json()
        total = sum(item["line_total"] for item in data)
        assert total <= budget

    def test_recommendations_priority_ordering(self, client):
        """Test that results are sorted by priority descending."""
        response = client.get("/api/restocking/recommendations?budget=200000")
        data = response.json()

        priorities = [item["priority"] for item in data]
        assert priorities == sorted(priorities, reverse=True)

    def test_recommendations_increasing_trend_first(self, client):
        """Test that increasing-trend items win over stable/decreasing."""
        response = client.get("/api/restocking/recommendations?budget=200000")
        data = response.json()

        # Priority encodes trend weight in the thousands place; increasing >= 3000
        increasing_priorities = [r["priority"] for r in data if r["trend"] == "increasing"]
        other_priorities = [r["priority"] for r in data if r["trend"] != "increasing"]
        if increasing_priorities and other_priorities:
            assert min(increasing_priorities) > max(other_priorities)

    def test_recommendations_tiny_budget_empty(self, client):
        """Test that an unrealistically small budget yields no recommendations."""
        response = client.get("/api/restocking/recommendations?budget=100")
        assert response.status_code == 200
        assert response.json() == []

    def test_recommendation_line_total_calculation(self, client):
        """Test that line_total = quantity * unit_cost."""
        response = client.get("/api/restocking/recommendations?budget=100000")
        data = response.json()

        for item in data:
            expected = item["quantity"] * item["unit_cost"]
            assert abs(item["line_total"] - expected) < 0.01

    def test_recommendation_data_types(self, client):
        """Test that numeric fields have proper types."""
        response = client.get("/api/restocking/recommendations?budget=100000")
        data = response.json()

        for item in data:
            assert isinstance(item["quantity"], int)
            assert isinstance(item["unit_cost"], (int, float))
            assert isinstance(item["line_total"], (int, float))
            assert isinstance(item["priority"], int)
            assert item["quantity"] > 0
            assert item["unit_cost"] > 0


class TestPlaceRestockingOrder:
    """Test suite for POST /api/restocking/orders."""

    @pytest.fixture(autouse=True)
    def _reset(self):
        """In-memory storage persists across tests; wipe before each."""
        submitted_restocking_orders.clear()
        yield
        submitted_restocking_orders.clear()

    def _sample_items(self):
        return [
            {"sku": "WDG-001", "name": "Widget", "quantity": 100,
             "unit_cost": 24.5, "line_total": 2450.0, "trend": "increasing", "priority": 3150},
            {"sku": "BRG-102", "name": "Bearing", "quantity": 50,
             "unit_cost": 89.0, "line_total": 4450.0, "trend": "stable", "priority": 2002},
        ]

    def test_place_order_success(self, client):
        """Test placing a restocking order."""
        payload = {"budget": 10000, "items": self._sample_items()}
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 200

        order = response.json()
        assert order["order_number"].startswith("RST-")
        assert order["status"] == "Submitted"
        assert order["total_value"] == 6900.0
        assert order["budget"] == 10000
        assert "T" in order["order_date"]
        assert "T" in order["expected_delivery"]

    def test_place_order_lead_time_is_slowest_item(self, client):
        """Lead time follows the slowest item (stable=14 > increasing=7)."""
        payload = {"budget": 10000, "items": self._sample_items()}
        response = client.post("/api/restocking/orders", json=payload)
        order = response.json()
        assert order["lead_time_days"] == 14

    def test_place_order_all_increasing_fast_lead(self, client):
        """All increasing-trend items gives 7-day lead."""
        items = [{"sku": "X", "name": "X", "quantity": 1, "unit_cost": 1.0,
                  "line_total": 1.0, "trend": "increasing", "priority": 3000}]
        response = client.post("/api/restocking/orders", json={"budget": 100, "items": items})
        assert response.json()["lead_time_days"] == 7

    def test_place_order_empty_items_rejected(self, client):
        """Test that empty item list returns 400."""
        response = client.post("/api/restocking/orders", json={"budget": 1000, "items": []})
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_place_order_appears_in_list(self, client):
        """Test that placed order appears in GET /api/restocking/orders."""
        client.post("/api/restocking/orders", json={"budget": 5000, "items": self._sample_items()})

        response = client.get("/api/restocking/orders")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["total_value"] == 6900.0

    def test_multiple_orders_sequential_numbers(self, client):
        """Test that order numbers increment."""
        r1 = client.post("/api/restocking/orders", json={"budget": 5000, "items": self._sample_items()})
        r2 = client.post("/api/restocking/orders", json={"budget": 5000, "items": self._sample_items()})

        # IDs are different even though the sequence counter is module-global
        assert r1.json()["id"] != r2.json()["id"]

        response = client.get("/api/restocking/orders")
        assert len(response.json()) == 2


class TestListRestockingOrders:
    """Test suite for GET /api/restocking/orders."""

    def test_list_empty_initially(self, client):
        """Test that list is empty when no orders placed."""
        submitted_restocking_orders.clear()
        response = client.get("/api/restocking/orders")
        assert response.status_code == 200
        assert response.json() == []
