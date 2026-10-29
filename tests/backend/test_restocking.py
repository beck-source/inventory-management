import pytest
from datetime import date, timedelta

from mock_data import restocking_orders, demand_forecasts


@pytest.fixture(autouse=True)
def clean_restocking_orders():
    # POST mutates shared in-memory state, so isolate every test from the others
    restocking_orders.clear()
    yield
    restocking_orders.clear()


class TestRestockingRecommendations:
    def test_zero_budget_recommends_nothing(self, client):
        response = client.get("/api/restocking/recommendations?budget=0")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total_cost"] == 0
        assert data["lead_time_days"] == 0

    def test_negative_budget_rejected(self, client):
        response = client.get("/api/restocking/recommendations?budget=-5")
        assert response.status_code == 422

    def test_missing_budget_rejected(self, client):
        response = client.get("/api/restocking/recommendations")
        assert response.status_code == 422

    def test_total_cost_never_exceeds_budget(self, client):
        for budget in [100, 1000, 5000, 20000]:
            data = client.get(f"/api/restocking/recommendations?budget={budget}").json()
            assert data["total_cost"] <= budget
            assert abs(data["remaining_budget"] - (budget - data["total_cost"])) < 0.01

    def test_large_budget_covers_every_shortfall(self, client):
        full_cost = client.get("/api/restocking/recommendations?budget=0").json()["full_restock_cost"]
        data = client.get(f"/api/restocking/recommendations?budget={full_cost + 1}").json()
        needed = [f for f in demand_forecasts if f["forecasted_demand"] > f["quantity_on_hand"]]
        assert len(data["items"]) == len(needed)
        assert abs(data["total_cost"] - full_cost) < 0.01
        for item in data["items"]:
            assert item["quantity"] == item["shortfall"]

    def test_increasing_trend_items_come_first(self, client):
        data = client.get("/api/restocking/recommendations?budget=100000").json()
        trends = [item["trend"] for item in data["items"]]
        increasing = [i for i, t in enumerate(trends) if t == "increasing"]
        others = [i for i, t in enumerate(trends) if t != "increasing"]
        assert increasing and others
        assert max(increasing) < min(others)

    def test_small_budget_buys_partial_quantity(self, client):
        data = client.get("/api/restocking/recommendations?budget=100").json()
        assert len(data["items"]) > 0
        for item in data["items"]:
            assert 0 < item["quantity"] <= item["shortfall"]

    def test_lead_time_is_longest_item(self, client):
        data = client.get("/api/restocking/recommendations?budget=100000").json()
        assert data["lead_time_days"] == max(i["lead_time_days"] for i in data["items"])

    def test_line_totals_match_quantity_times_cost(self, client):
        data = client.get("/api/restocking/recommendations?budget=5000").json()
        for item in data["items"]:
            assert abs(item["line_total"] - item["quantity"] * item["unit_cost"]) < 0.01


class TestRestockingOrders:
    def test_list_empty_initially(self, client):
        response = client.get("/api/restocking-orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_order_success(self, client):
        sku = demand_forecasts[0]["item_sku"]
        response = client.post("/api/restocking-orders", json={
            "items": [{"sku": sku, "quantity": 10}],
            "budget": 1000,
        })
        assert response.status_code == 201
        order = response.json()
        assert order["order_number"].startswith("RST-")
        assert order["status"] == "Submitted"
        assert order["items"][0]["sku"] == sku
        assert order["items"][0]["quantity"] == 10

    def test_lead_time_and_delivery_date(self, client):
        skus = [f["item_sku"] for f in demand_forecasts[:3]]
        order = client.post("/api/restocking-orders", json={
            "items": [{"sku": s, "quantity": 1} for s in skus],
            "budget": 100000,
        }).json()
        expected_lead = max(f["lead_time_days"] for f in demand_forecasts[:3])
        assert order["lead_time_days"] == expected_lead
        delivery = date.fromisoformat(order["expected_delivery"])
        assert delivery == date.fromisoformat(order["order_date"]) + timedelta(days=expected_lead)

    def test_client_cannot_set_price(self, client):
        forecast = demand_forecasts[0]
        order = client.post("/api/restocking-orders", json={
            "items": [{"sku": forecast["item_sku"], "quantity": 2, "unit_cost": 0.01}],
            "budget": 1000,
        }).json()
        assert order["items"][0]["unit_cost"] == forecast["unit_cost"]
        assert abs(order["total_cost"] - 2 * forecast["unit_cost"]) < 0.01

    def test_over_budget_rejected(self, client):
        response = client.post("/api/restocking-orders", json={
            "items": [{"sku": demand_forecasts[0]["item_sku"], "quantity": 1000}],
            "budget": 1,
        })
        assert response.status_code == 400
        assert "budget" in response.json()["detail"].lower()
        assert client.get("/api/restocking-orders").json() == []

    def test_unknown_sku_rejected(self, client):
        response = client.post("/api/restocking-orders", json={
            "items": [{"sku": "NOPE-999", "quantity": 1}],
            "budget": 1000,
        })
        assert response.status_code == 400
        assert "unknown sku" in response.json()["detail"].lower()

    def test_empty_items_rejected(self, client):
        response = client.post("/api/restocking-orders", json={"items": [], "budget": 1000})
        assert response.status_code == 422

    def test_non_positive_quantity_rejected(self, client):
        response = client.post("/api/restocking-orders", json={
            "items": [{"sku": demand_forecasts[0]["item_sku"], "quantity": 0}],
            "budget": 1000,
        })
        assert response.status_code == 422

    def test_orders_listed_newest_first(self, client):
        sku = demand_forecasts[0]["item_sku"]
        first = client.post("/api/restocking-orders", json={"items": [{"sku": sku, "quantity": 1}], "budget": 1000}).json()
        second = client.post("/api/restocking-orders", json={"items": [{"sku": sku, "quantity": 2}], "budget": 1000}).json()
        listed = client.get("/api/restocking-orders").json()
        assert [o["id"] for o in listed] == [second["id"], first["id"]]
        assert first["order_number"] != second["order_number"]
