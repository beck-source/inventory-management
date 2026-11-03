"""
Tests for the restocking endpoints.
"""
import pytest

import mock_data


@pytest.fixture(autouse=True)
def clear_submitted_orders():
    """Reset in-memory submitted orders around each test."""
    mock_data.submitted_orders.clear()
    yield
    mock_data.submitted_orders.clear()


class TestRestockRecommendations:
    """Tests for GET /api/restock/recommendations"""

    def test_zero_budget_returns_nothing(self, client):
        response = client.get("/api/restock/recommendations?budget=0")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total_cost"] == 0

    def test_negative_budget_rejected(self, client):
        response = client.get("/api/restock/recommendations?budget=-5")
        assert response.status_code == 400

    @pytest.mark.parametrize("budget", [500, 5000, 20000, 100000])
    def test_total_within_budget(self, client, budget):
        data = client.get(f"/api/restock/recommendations?budget={budget}").json()
        assert data["total_cost"] <= budget
        assert data["total_cost"] == pytest.approx(sum(i["line_cost"] for i in data["items"]))

    def test_quantity_never_exceeds_shortfall(self, client):
        data = client.get("/api/restock/recommendations?budget=100000").json()
        assert data["items"]
        for item in data["items"]:
            assert 0 < item["quantity"] <= item["shortfall"]
            assert item["line_cost"] == pytest.approx(item["quantity"] * item["unit_cost"])

    def test_increasing_trend_first(self, client):
        items = client.get("/api/restock/recommendations?budget=100000").json()["items"]
        trends = [i["trend"] for i in items]
        assert trends[0] == "increasing"
        order = {"increasing": 0, "stable": 1, "decreasing": 2}
        assert [order[t] for t in trends] == sorted(order[t] for t in trends)

    def test_larger_budget_never_recommends_less(self, client):
        small = client.get("/api/restock/recommendations?budget=2000").json()["total_cost"]
        large = client.get("/api/restock/recommendations?budget=50000").json()["total_cost"]
        assert large >= small


class TestRestockRecommendationDetails:
    """Exact-value and edge-case tests for recommendations"""

    def test_quantity_is_min_of_shortfall_and_affordable(self, client):
        # FLT-405 ranks first (shortfall 550) at 14.25 -> 15 units affordable with 220
        data = client.get("/api/restock/recommendations?budget=220").json()
        assert [(i["sku"], i["quantity"]) for i in data["items"]] == [("FLT-405", 15)]
        assert data["total_cost"] == pytest.approx(213.75)

    def test_ranked_by_shortfall_within_trend(self, client):
        items = client.get("/api/restock/recommendations?budget=1000000").json()["items"]
        increasing = [i["shortfall"] for i in items if i["trend"] == "increasing"]
        assert increasing == sorted(increasing, reverse=True)

    def test_no_item_without_shortfall(self, client):
        items = client.get("/api/restock/recommendations?budget=1000000").json()["items"]
        assert all(i["shortfall"] > 0 for i in items)
        assert "MTR-304" not in {i["sku"] for i in items}

    @pytest.mark.parametrize("budget", ["nan", "inf", "-inf"])
    def test_non_finite_budget_rejected(self, client, budget):
        assert client.get(f"/api/restock/recommendations?budget={budget}").status_code in (400, 422)

    def test_non_numeric_budget_rejected(self, client):
        assert client.get("/api/restock/recommendations?budget=abc").status_code == 422


class TestRestockOrders:
    """Tests for POST/GET /api/restock/orders"""

    def test_place_order_success(self, client):
        payload = {"budget": 10000, "items": [{"sku": "WDG-001", "quantity": 10}]}
        response = client.post("/api/restock/orders", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Submitted"
        assert data["order_number"].startswith("RST-")
        assert data["total_cost"] == pytest.approx(10 * 42.50)
        assert data["lead_time_days"] == 21
        assert data["expected_delivery"]

    def test_lead_time_is_longest_category(self, client):
        payload = {"budget": 100000, "items": [
            {"sku": "GSK-203", "quantity": 5},   # Sensors, 10 days
            {"sku": "WDG-001", "quantity": 5},   # Actuators, 21 days
        ]}
        data = client.post("/api/restock/orders", json=payload).json()
        assert data["lead_time_days"] == 21

    def test_over_budget_rejected(self, client):
        payload = {"budget": 100, "items": [{"sku": "WDG-001", "quantity": 10}]}
        assert client.post("/api/restock/orders", json=payload).status_code == 400

    def test_empty_items_rejected(self, client):
        assert client.post("/api/restock/orders", json={"budget": 100, "items": []}).status_code == 400

    def test_unknown_sku_rejected(self, client):
        payload = {"budget": 100, "items": [{"sku": "NOPE-999", "quantity": 1}]}
        assert client.post("/api/restock/orders", json=payload).status_code == 400

    @pytest.mark.parametrize("quantity", [0, -3])
    def test_non_positive_quantity_rejected(self, client, quantity):
        payload = {"budget": 1000, "items": [{"sku": "WDG-001", "quantity": quantity}]}
        assert client.post("/api/restock/orders", json=payload).status_code == 400

    def test_non_positive_budget_rejected(self, client):
        payload = {"budget": 0, "items": [{"sku": "WDG-001", "quantity": 1}]}
        assert client.post("/api/restock/orders", json=payload).status_code == 400

    def test_placed_orders_listed_newest_first(self, client):
        for qty in (1, 2):
            client.post("/api/restock/orders", json={"budget": 10000, "items": [{"sku": "WDG-001", "quantity": qty}]})
        orders = client.get("/api/restock/orders").json()
        assert [o["order_number"] for o in orders] == ["RST-0002", "RST-0001"]

    def test_no_orders_initially(self, client):
        assert client.get("/api/restock/orders").json() == []

    def test_duplicate_sku_rejected(self, client):
        payload = {"budget": 10000, "items": [{"sku": "WDG-001", "quantity": 1}, {"sku": "WDG-001", "quantity": 2}]}
        assert client.post("/api/restock/orders", json=payload).status_code == 400

    def test_quantity_above_shortfall_rejected(self, client):
        payload = {"budget": 1000000, "items": [{"sku": "WDG-001", "quantity": 271}]}
        response = client.post("/api/restock/orders", json=payload)
        assert response.status_code == 400
        assert "shortfall" in response.json()["detail"]

    def test_sku_without_shortfall_rejected(self, client):
        payload = {"budget": 100000, "items": [{"sku": "PCB-001", "quantity": 1}]}
        assert client.post("/api/restock/orders", json=payload).status_code == 400

    def test_exact_budget_accepted_and_one_cent_over_rejected(self, client):
        items = [{"sku": "WDG-001", "quantity": 10}]  # 425.00
        assert client.post("/api/restock/orders", json={"budget": 425.00, "items": items}).status_code == 200
        assert client.post("/api/restock/orders", json={"budget": 424.99, "items": items}).status_code == 400

    def test_expected_delivery_is_today_plus_lead_time(self, client):
        from datetime import date, timedelta
        data = client.post("/api/restock/orders", json={"budget": 10000, "items": [{"sku": "WDG-001", "quantity": 1}]}).json()
        assert data["expected_delivery"] == (date.today() + timedelta(days=data["lead_time_days"])).isoformat()

    def test_non_finite_budget_rejected(self, client):
        response = client.post("/api/restock/orders", content='{"budget": NaN, "items": [{"sku": "WDG-001", "quantity": 1}]}',
                               headers={"Content-Type": "application/json"})
        assert response.status_code in (400, 422)
