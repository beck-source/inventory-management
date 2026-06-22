"""
Tests for restocking recommendation and order endpoints.
"""
import pytest


class TestRestockingRecommendations:
    """GET /api/restocking/recommendations"""

    def test_zero_budget_returns_no_items(self, client):
        response = client.get("/api/restocking/recommendations?budget=0")
        assert response.status_code == 200
        data = response.json()
        assert data["budget"] == 0
        assert data["spent"] == 0
        assert data["remaining"] == 0
        assert data["items"] == []

    def test_negative_budget_rejected(self, client):
        response = client.get("/api/restocking/recommendations?budget=-100")
        assert response.status_code == 400

    def test_large_budget_covers_all_positive_gaps(self, client):
        response = client.get("/api/restocking/recommendations?budget=1000000")
        assert response.status_code == 200
        data = response.json()

        assert data["spent"] <= data["budget"]
        assert data["spent"] > 0
        assert len(data["items"]) > 0

        # Every line should be priced consistently
        for item in data["items"]:
            assert item["quantity"] > 0
            assert item["unit_cost"] > 0
            assert item["lead_time_days"] > 0
            assert round(item["quantity"] * item["unit_cost"], 2) == item["line_total"]

        # MTR-304 has forecasted < current (negative gap) — must never be recommended
        skus = {item["item_sku"] for item in data["items"]}
        assert "MTR-304" not in skus

    def test_priority_ordering_increasing_trend_first(self, client):
        """The first recommended item at a mid budget should be one of the
        highest-priority increasing-trend SKUs (FLT-405 or WDG-001 — both
        have gap=150 and trend=increasing, so they tie on score)."""
        response = client.get("/api/restocking/recommendations?budget=5000")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) > 0
        assert data["items"][0]["trend"] == "increasing"
        assert data["items"][0]["item_sku"] in {"FLT-405", "WDG-001"}

    def test_recommendation_is_deterministic(self, client):
        """Same budget must always produce the same result, since POST
        re-derives the order server-side and must match the GET preview."""
        a = client.get("/api/restocking/recommendations?budget=4000").json()
        b = client.get("/api/restocking/recommendations?budget=4000").json()
        assert a == b


class TestRestockingOrders:
    """POST + GET /api/restocking/orders"""

    def test_create_and_list_roundtrip(self, client):
        before = client.get("/api/restocking/orders").json()

        create = client.post("/api/restocking/orders", json={"budget": 5000})
        assert create.status_code == 201
        order = create.json()

        assert order["order_number"].startswith("RST-")
        assert order["status"] == "Submitted"
        assert order["total_value"] <= 5000
        assert order["total_value"] > 0
        assert order["expected_delivery"] >= order["order_date"]
        assert len(order["items"]) > 0

        after = client.get("/api/restocking/orders").json()
        assert len(after) == len(before) + 1
        assert any(o["id"] == order["id"] for o in after)

    def test_zero_budget_rejected(self, client):
        response = client.post("/api/restocking/orders", json={"budget": 0})
        assert response.status_code == 400

    def test_negative_budget_rejected(self, client):
        response = client.post("/api/restocking/orders", json={"budget": -1})
        assert response.status_code == 400

    def test_extra_client_fields_ignored(self, client):
        """Client-supplied items/prices must not influence the stored order —
        the server recomputes everything from `budget` alone."""
        baseline = client.get("/api/restocking/recommendations?budget=3000").json()

        response = client.post("/api/restocking/orders", json={
            "budget": 3000,
            "items": [{"item_sku": "FAKE-999", "unit_cost": 0.01, "quantity": 999999}],
            "total_value": 0.01,
        })
        assert response.status_code == 201
        order = response.json()

        # Order must match the server-computed recommendation, not the injected payload
        assert order["total_value"] == baseline["spent"]
        order_skus = {i["item_sku"] for i in order["items"]}
        assert "FAKE-999" not in order_skus


class TestDemandForecastFields:
    """GET /api/demand should now expose unit_cost and lead_time_days."""

    def test_demand_items_include_pricing_fields(self, client):
        response = client.get("/api/demand")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        for item in data:
            assert "unit_cost" in item
            assert "lead_time_days" in item
            assert item["unit_cost"] > 0
            assert item["lead_time_days"] > 0
