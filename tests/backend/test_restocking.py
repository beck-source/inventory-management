"""
Tests for the restocking recommendation and order-submission endpoints.
"""
from datetime import datetime


class TestRestockRecommendations:
    """Test suite for GET /api/restocking/recommendations."""

    def test_zero_budget_returns_no_items(self, client):
        response = client.get("/api/restocking/recommendations?budget=0")
        assert response.status_code == 200

        data = response.json()
        assert data["items"] == []
        assert data["total_cost"] == 0
        assert data["remaining_budget"] == 0

    def test_negative_budget_rejected(self, client):
        response = client.get("/api/restocking/recommendations?budget=-100")
        assert response.status_code == 400

    def test_recommendations_stay_within_budget(self, client):
        response = client.get("/api/restocking/recommendations?budget=5000")
        assert response.status_code == 200

        data = response.json()
        assert data["total_cost"] <= 5000
        assert data["remaining_budget"] == round(5000 - data["total_cost"], 2)

    def test_recommendations_exclude_decreasing_trend(self, client):
        response = client.get("/api/restocking/recommendations?budget=100000")
        data = response.json()

        for item in data["items"]:
            assert item["trend"] != "decreasing"

    def test_recommendations_ranked_by_trend_then_percent_increase(self, client):
        response = client.get("/api/restocking/recommendations?budget=100000")
        data = response.json()
        items = data["items"]

        assert len(items) > 0, "Expected at least one recommended item for a large budget"

        trend_rank = {"increasing": 0, "stable": 1}
        ranks = [trend_rank.get(item["trend"], 2) for item in items]
        assert ranks == sorted(ranks), "Increasing-trend items should be ranked before stable items"

        increasing_items = [item for item in items if item["trend"] == "increasing"]
        percent_increases = [item["percent_increase"] for item in increasing_items]
        assert percent_increases == sorted(percent_increases, reverse=True), \
            "Increasing items should be sorted by descending percent_increase"

    def test_recommended_line_totals_are_consistent(self, client):
        response = client.get("/api/restocking/recommendations?budget=2000")
        data = response.json()

        for item in data["items"]:
            expected_total = round(item["recommended_qty"] * item["unit_cost"], 2)
            assert item["line_total"] == expected_total


class TestCreateRestockOrder:
    """Test suite for POST /api/restocking/order."""

    def _sample_items(self):
        return [
            {"sku": "TMP-201", "name": "Temperature Sensor Module", "quantity": 25, "unit_cost": 89.5},
            {"sku": "HMD-202", "name": "Humidity Sensor Module", "quantity": 10, "unit_cost": 125.0},
        ]

    def test_create_restock_order_success(self, client):
        payload = {"budget": 5000, "items": self._sample_items()}
        response = client.post("/api/restocking/order", json=payload)
        assert response.status_code == 201

        order = response.json()
        assert order["status"] == "Submitted"
        assert order["lead_time_days"] == 7
        assert order["order_number"].startswith("RESTOCK-")
        assert order["customer"] == "Internal Restocking"

        order_date = datetime.fromisoformat(order["order_date"])
        expected_delivery = datetime.fromisoformat(order["expected_delivery"])
        assert (expected_delivery - order_date).days == 7

    def test_create_restock_order_total_value_calculation(self, client):
        items = self._sample_items()
        payload = {"budget": 5000, "items": items}
        response = client.post("/api/restocking/order", json=payload)
        order = response.json()

        expected_total = round(sum(i["quantity"] * i["unit_cost"] for i in items), 2)
        assert order["total_value"] == expected_total

    def test_create_restock_order_empty_items_rejected(self, client):
        payload = {"budget": 5000, "items": []}
        response = client.post("/api/restocking/order", json=payload)
        assert response.status_code == 400

    def test_create_restock_order_appears_in_orders_list(self, client):
        payload = {"budget": 5000, "items": self._sample_items()}
        create_response = client.post("/api/restocking/order", json=payload)
        created_order = create_response.json()

        orders_response = client.get("/api/orders", params={"status": "Submitted"})
        assert orders_response.status_code == 200

        submitted_orders = orders_response.json()
        order_ids = [o["id"] for o in submitted_orders]
        assert created_order["id"] in order_ids
