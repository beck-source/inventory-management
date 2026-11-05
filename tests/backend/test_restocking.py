"""
Tests for restocking API endpoints (recommendations and submitted orders).
"""
import pytest

TREND_RANK = {"increasing": 0, "stable": 1, "decreasing": 2}


def recommend(client, budget):
    response = client.get("/api/restocking/recommendations", params={"budget": budget})
    assert response.status_code == 200
    return response.json()


def order_payload(items, budget=100000):
    return {"budget": budget, "items": items}


class TestRestockRecommendations:
    """Test suite for GET /api/restocking/recommendations."""

    def test_zero_budget_recommends_nothing(self, client):
        data = recommend(client, 0)
        assert data["items"] == []
        assert data["total_cost"] == 0
        assert data["remaining_budget"] == 0
        assert data["lead_time_days"] == 0

    def test_negative_budget_is_rejected(self, client):
        response = client.get("/api/restocking/recommendations", params={"budget": -1})
        assert response.status_code == 422

    def test_missing_budget_is_rejected(self, client):
        response = client.get("/api/restocking/recommendations")
        assert response.status_code == 422

    def test_total_never_exceeds_budget(self, client):
        for budget in (500, 3000, 12345, 20000):
            data = recommend(client, budget)
            assert data["total_cost"] <= budget
            assert data["remaining_budget"] == pytest.approx(budget - data["total_cost"])
            line_sum = sum(i["line_total"] for i in data["items"])
            assert data["total_cost"] == pytest.approx(line_sum)

    def test_growing_items_are_prioritised(self, client):
        data = recommend(client, 20000)
        ranks = [TREND_RANK[i["trend"]] for i in data["items"]]
        assert ranks == sorted(ranks)

    def test_large_budget_covers_every_shortfall(self, client):
        data = recommend(client, 1000000)
        assert len(data["items"]) > 0
        for item in data["items"]:
            assert item["quantity"] == item["shortfall"]
            assert item["shortfall"] == item["forecasted_demand"] - item["quantity_on_hand"]
        # Order lead time is the slowest item
        assert data["lead_time_days"] == max(i["lead_time_days"] for i in data["items"])

    def test_items_without_shortfall_are_excluded(self, client):
        skus = {i["sku"] for i in recommend(client, 1000000)["items"]}
        demand = client.get("/api/demand").json()
        for forecast in demand:
            if forecast["quantity_on_hand"] >= forecast["forecasted_demand"]:
                assert forecast["item_sku"] not in skus


class TestRestockOrders:
    """Test suite for POST/GET /api/restocking/orders."""

    def test_no_orders_initially(self, client):
        response = client.get("/api/restocking/orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_order_from_recommendation(self, client):
        rec = recommend(client, 20000)
        items = [{"sku": i["sku"], "name": i["name"], "quantity": i["quantity"],
                  "unit_cost": i["unit_cost"]} for i in rec["items"]]

        response = client.post("/api/restocking/orders", json=order_payload(items, 20000))
        assert response.status_code == 201

        order = response.json()
        assert order["status"] == "Submitted"
        assert order["order_number"].startswith("RST-")
        assert order["total_value"] == pytest.approx(rec["total_cost"])
        assert order["lead_time_days"] == rec["lead_time_days"]
        assert order["expected_delivery"] > order["order_date"]

    def test_created_order_appears_in_list_newest_first(self, client):
        item = [{"sku": "FLT-405", "name": "x", "quantity": 10, "unit_cost": 1}]
        first = client.post("/api/restocking/orders", json=order_payload(item)).json()
        second = client.post("/api/restocking/orders", json=order_payload(item)).json()

        listed = client.get("/api/restocking/orders").json()
        assert [o["id"] for o in listed] == [second["id"], first["id"]]
        assert first["order_number"] != second["order_number"]

    def test_server_ignores_client_supplied_price(self, client):
        # A tampered unit_cost must not let an order slip under the budget
        item = [{"sku": "FLT-405", "name": "x", "quantity": 100, "unit_cost": 0.01}]
        order = client.post("/api/restocking/orders", json=order_payload(item)).json()
        assert order["items"][0]["unit_cost"] != 0.01
        assert order["total_value"] == pytest.approx(100 * order["items"][0]["unit_cost"])

        response = client.post("/api/restocking/orders", json=order_payload(item, budget=10))
        assert response.status_code == 400

    def test_lead_time_is_longest_item(self, client):
        forecasts = {f["item_sku"]: f for f in client.get("/api/demand").json()}
        skus = ["FLT-405", "WDG-001"]
        items = [{"sku": s, "name": "x", "quantity": 1, "unit_cost": 1} for s in skus]
        order = client.post("/api/restocking/orders", json=order_payload(items)).json()
        assert order["lead_time_days"] == max(forecasts[s]["lead_time_days"] for s in skus)

    def test_empty_order_is_rejected(self, client):
        response = client.post("/api/restocking/orders", json=order_payload([]))
        assert response.status_code == 400

    def test_unknown_sku_is_rejected(self, client):
        item = [{"sku": "NOPE-000", "name": "x", "quantity": 1, "unit_cost": 1}]
        response = client.post("/api/restocking/orders", json=order_payload(item))
        assert response.status_code == 400

    def test_non_positive_quantity_is_rejected(self, client):
        item = [{"sku": "FLT-405", "name": "x", "quantity": 0, "unit_cost": 1}]
        response = client.post("/api/restocking/orders", json=order_payload(item))
        assert response.status_code == 422

    def test_negative_budget_is_rejected(self, client):
        item = [{"sku": "FLT-405", "name": "x", "quantity": 1, "unit_cost": 1}]
        response = client.post("/api/restocking/orders", json=order_payload(item, budget=-5))
        assert response.status_code == 422
