"""Tests for the Restocking feature: budget-based recommendations and submitted restock orders."""
from datetime import date, timedelta

import pytest

from mock_data import restock_orders


@pytest.fixture(autouse=True)
def clear_restock_orders():
    """Keep tests independent: submitted orders live in a module-level list."""
    restock_orders.clear()
    yield
    restock_orders.clear()


class TestRestockRecommendations:
    """GET /api/restocking/recommendations"""

    def test_recommendations_fit_budget(self, client):
        for budget in (0, 500, 1500, 5000, 100000):
            response = client.get(f"/api/restocking/recommendations?budget={budget}")
            assert response.status_code == 200
            data = response.json()
            assert data["total_cost"] <= budget
            assert round(data["budget"] - data["total_cost"], 2) == data["remaining"]
            assert round(sum(i["line_total"] for i in data["items"]), 2) == data["total_cost"]

    def test_zero_budget_returns_no_items(self, client):
        data = client.get("/api/restocking/recommendations?budget=0").json()
        assert data["items"] == []
        assert data["total_cost"] == 0

    def test_negative_or_missing_budget_rejected(self, client):
        assert client.get("/api/restocking/recommendations?budget=-1").status_code == 422
        assert client.get("/api/restocking/recommendations").status_code == 422

    def test_only_growing_items_recommended(self, client):
        data = client.get("/api/restocking/recommendations?budget=1000000").json()
        assert data["items"], "a large budget should recommend items"
        for item in data["items"]:
            assert item["forecasted_demand"] > item["current_demand"]
            assert item["quantity"] == item["forecasted_demand"] - item["current_demand"]
        skus = {i["item_sku"] for i in data["items"]}
        assert "MTR-304" not in skus  # decreasing demand

    def test_priority_is_highest_growth_first(self, client):
        items = client.get("/api/restocking/recommendations?budget=1000000").json()["items"]
        growth = [(i["forecasted_demand"] - i["current_demand"]) / i["current_demand"] for i in items]
        assert growth == sorted(growth, reverse=True)

    def test_max_budget_covers_everything(self, client):
        data = client.get("/api/restocking/recommendations?budget=0").json()
        full = client.get(f"/api/restocking/recommendations?budget={data['max_budget']}").json()
        assert data["max_budget"] % 1000 == 0
        assert all(i["quantity"] == i["forecasted_demand"] - i["current_demand"] for i in full["items"])

    def test_small_budget_buys_partial_quantity(self, client):
        # 50 dollars cannot cover the top item's full growth, so a partial quantity is recommended
        items = client.get("/api/restocking/recommendations?budget=50").json()["items"]
        assert items
        assert items[0]["quantity"] < items[0]["forecasted_demand"] - items[0]["current_demand"]


class TestRestockOrders:
    """POST/GET /api/restocking/orders"""

    def test_create_and_list_order(self, client):
        rec = client.get("/api/restocking/recommendations?budget=2000").json()
        payload = {"budget": 2000, "items": [{"item_sku": i["item_sku"], "quantity": i["quantity"]} for i in rec["items"]]}
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 201
        order = response.json()
        assert order["id"].startswith("RST-")
        assert order["status"] == "Submitted"
        assert order["total_cost"] == rec["total_cost"]
        assert order["lead_time_days"] == max(i["lead_time_days"] for i in rec["items"])
        expected = date.fromisoformat(order["created_date"]) + timedelta(days=order["lead_time_days"])
        assert order["expected_delivery"] == expected.isoformat()

        listed = client.get("/api/restocking/orders").json()
        assert listed[0]["id"] == order["id"]  # newest first

    def test_empty_order_rejected(self, client):
        assert client.post("/api/restocking/orders", json={"budget": 100, "items": []}).status_code == 400

    def test_unknown_sku_rejected(self, client):
        payload = {"budget": 100, "items": [{"item_sku": "NOPE-000", "quantity": 1}]}
        assert client.post("/api/restocking/orders", json=payload).status_code == 400

    def test_over_budget_rejected(self, client):
        payload = {"budget": 10, "items": [{"item_sku": "WDG-001", "quantity": 100}]}
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 400
        assert "exceeds budget" in response.json()["detail"]

    def test_non_positive_quantity_rejected(self, client):
        payload = {"budget": 100, "items": [{"item_sku": "WDG-001", "quantity": 0}]}
        assert client.post("/api/restocking/orders", json=payload).status_code == 422


class TestDemandForecastFields:
    def test_demand_includes_cost_and_lead_time(self, client):
        for f in client.get("/api/demand").json():
            assert f["unit_cost"] > 0
            assert f["lead_time_days"] > 0
