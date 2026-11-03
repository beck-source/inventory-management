"""
Tests for the restocking endpoints.
"""
import pytest

from mock_data import submitted_orders


@pytest.fixture(autouse=True)
def clear_submitted_orders():
    # The store is a module-level list shared across tests, so reset it around each test
    submitted_orders.clear()
    yield
    submitted_orders.clear()


class TestRestockRecommendations:
    """Tests for GET /api/restocking/recommendations"""

    def test_zero_budget_recommends_nothing(self, client):
        data = client.get("/api/restocking/recommendations?budget=0").json()
        assert data["items"] == []
        assert data["total_cost"] == 0
        assert data["max_budget"] > 0

    def test_negative_budget_rejected(self, client):
        assert client.get("/api/restocking/recommendations?budget=-1").status_code == 422

    def test_spend_never_exceeds_budget(self, client):
        for budget in (100, 1000, 5000, 20000):
            data = client.get(f"/api/restocking/recommendations?budget={budget}").json()
            assert data["total_cost"] <= budget
            assert data["total_cost"] + data["remaining"] == pytest.approx(budget)
            assert data["total_cost"] == pytest.approx(sum(i["line_cost"] for i in data["items"]))

    def test_increasing_trend_items_come_first(self, client):
        data = client.get("/api/restocking/recommendations?budget=100000").json()
        trends = [i["trend"] for i in data["items"]]
        assert trends[0] == "increasing"
        # Items are ordered increasing -> stable, never interleaved
        rank = {"increasing": 0, "stable": 1}
        assert trends == sorted(trends, key=rank.get)

    def test_decreasing_items_never_recommended(self, client):
        data = client.get("/api/restocking/recommendations?budget=100000").json()
        assert all(i["trend"] != "decreasing" for i in data["items"])

    def test_max_budget_funds_every_need(self, client):
        max_budget = client.get("/api/restocking/recommendations?budget=0").json()["max_budget"]
        data = client.get(f"/api/restocking/recommendations?budget={max_budget}").json()
        assert data["remaining"] == pytest.approx(0, abs=0.01)


class TestRestockOrders:
    """Tests for POST/GET /api/restocking/orders"""

    def test_place_order_uses_longest_lead_time(self, client):
        response = client.post("/api/restocking/orders", json={"budget": 100000})
        assert response.status_code == 200
        order = response.json()
        assert order["id"] == "RST-0001"
        assert order["status"] == "Submitted"
        assert order["lead_time_days"] == max(l["lead_time_days"] for l in order["lines"])

    def test_empty_recommendation_returns_400(self, client):
        assert client.post("/api/restocking/orders", json={"budget": 0}).status_code == 400

    def test_negative_budget_returns_422(self, client):
        assert client.post("/api/restocking/orders", json={"budget": -5}).status_code == 422

    def test_list_returns_newest_first(self, client):
        client.post("/api/restocking/orders", json={"budget": 100000})
        client.post("/api/restocking/orders", json={"budget": 50000})
        ids = [o["id"] for o in client.get("/api/restocking/orders").json()]
        assert ids == ["RST-0002", "RST-0001"]

    def test_orders_do_not_leak_into_main_orders(self, client):
        before = len(client.get("/api/orders").json())
        client.post("/api/restocking/orders", json={"budget": 100000})
        assert len(client.get("/api/orders").json()) == before
