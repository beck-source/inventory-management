"""
Tests for restocking API endpoints.
"""
import pytest

import main


@pytest.fixture(autouse=True)
def reset_restock_orders():
    """Submitted restocking orders live in memory; isolate each test."""
    main.restock_orders.clear()
    yield
    main.restock_orders.clear()


class TestRestockingRecommendations:
    """Test suite for the restocking recommendations endpoint."""

    def test_get_recommendations(self, client):
        """Test getting recommendations for a budget."""
        response = client.get("/api/restocking/recommendations?budget=25000")
        assert response.status_code == 200

        data = response.json()
        for field in ["budget", "total_cost", "remaining_budget", "full_restock_cost", "items"]:
            assert field in data
        assert data["budget"] == 25000
        assert len(data["items"]) > 0

        for item in data["items"]:
            for field in ["item_sku", "item_name", "trend", "forecasted_demand", "quantity_on_hand", "quantity_on_order",
                          "shortfall", "recommended_quantity", "unit_cost", "line_total",
                          "lead_time_days", "partial"]:
                assert field in item
            assert isinstance(item["recommended_quantity"], int)
            assert 0 < item["recommended_quantity"] <= item["shortfall"]
            assert item["line_total"] == pytest.approx(item["recommended_quantity"] * item["unit_cost"])

    def test_recommendations_stay_within_budget(self, client):
        """Test that the recommended total never exceeds the budget."""
        for budget in [1000, 5000, 25000, 100000]:
            data = client.get(f"/api/restocking/recommendations?budget={budget}").json()
            assert data["total_cost"] <= budget
            assert data["remaining_budget"] == pytest.approx(budget - data["total_cost"])
            assert data["total_cost"] == pytest.approx(sum(i["line_total"] for i in data["items"]))

    def test_large_budget_covers_full_restock(self, client):
        """Test that a budget above the full restock cost covers every shortfall."""
        data = client.get("/api/restocking/recommendations?budget=10000000").json()
        assert data["total_cost"] == pytest.approx(data["full_restock_cost"])
        for item in data["items"]:
            assert item["recommended_quantity"] == item["shortfall"]
            assert item["partial"] is False

    def test_recommendations_exclude_stocked_items(self, client):
        """Test that items with enough stock on hand are not recommended."""
        # PSU-501 has 420 on hand against a forecast of 252
        data = client.get("/api/restocking/recommendations?budget=10000000").json()
        skus = [item["item_sku"] for item in data["items"]]
        assert "PSU-501" not in skus
        for item in data["items"]:
            assert item["shortfall"] == item["forecasted_demand"] - item["quantity_on_hand"] - item["quantity_on_order"]

    def test_recommendations_prioritize_increasing_trend(self, client):
        """Test that increasing-demand items are ranked before other trends."""
        data = client.get("/api/restocking/recommendations?budget=10000000").json()
        trends = [item["trend"] for item in data["items"]]
        priority = {"increasing": 0, "stable": 1, "decreasing": 2}
        assert trends == sorted(trends, key=priority.get)

    def test_small_budget_marks_partial(self, client):
        """Test that a budget smaller than the first shortfall yields a partial line."""
        data = client.get("/api/restocking/recommendations?budget=1000").json()
        assert len(data["items"]) > 0
        assert data["items"][0]["partial"] is True

    @pytest.mark.parametrize("budget", ["0", "-100", "abc", "inf", "nan", "1e308"])
    def test_invalid_budget(self, client, budget):
        """Test that non-positive, non-numeric, non-finite, or oversized budgets are rejected."""
        response = client.get(f"/api/restocking/recommendations?budget={budget}")
        assert response.status_code == 422

    def test_missing_budget(self, client):
        """Test that budget is required."""
        response = client.get("/api/restocking/recommendations")
        assert response.status_code == 422


class TestRestockingOrders:
    """Test suite for submitting and listing restocking orders."""

    def test_no_orders_initially(self, client):
        """Test that the submitted orders list starts empty."""
        response = client.get("/api/restocking/orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_place_recommended_order(self, client):
        """Test submitting the recommended items as an order."""
        recs = client.get("/api/restocking/recommendations?budget=25000").json()
        payload = {
            "budget": 25000,
            "items": [{"item_sku": i["item_sku"], "quantity": i["recommended_quantity"]} for i in recs["items"]],
        }
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 201

        order = response.json()
        assert order["status"] == "Submitted"
        assert order["order_number"].startswith("RST-")
        assert order["total_value"] == pytest.approx(recs["total_cost"])
        assert order["lead_time_days"] == max(i["lead_time_days"] for i in recs["items"])
        assert len(order["items"]) == len(recs["items"])

    def test_placed_order_reduces_recommendations(self, client):
        """Test that quantities on order count toward stock, so the same order is not recommended twice."""
        recs = client.get("/api/restocking/recommendations?budget=10000000").json()
        client.post("/api/restocking/orders", json={
            "budget": 10000000,
            "items": [{"item_sku": i["item_sku"], "quantity": i["recommended_quantity"]} for i in recs["items"]],
        })
        after = client.get("/api/restocking/recommendations?budget=10000000").json()
        assert after["items"] == []
        assert after["full_restock_cost"] == 0

    def test_partial_order_leaves_remaining_shortfall(self, client):
        """Test that ordering part of a shortfall leaves the rest recommended, with the on-order quantity shown."""
        before = {i["item_sku"]: i for i in client.get("/api/restocking/recommendations?budget=10000000").json()["items"]}
        client.post("/api/restocking/orders", json={"budget": 5000, "items": [{"item_sku": "TMP-201", "quantity": 10}]})
        after = {i["item_sku"]: i for i in client.get("/api/restocking/recommendations?budget=10000000").json()["items"]}
        assert after["TMP-201"]["quantity_on_order"] == 10
        assert after["TMP-201"]["shortfall"] == before["TMP-201"]["shortfall"] - 10

    def test_expected_delivery_uses_lead_time(self, client):
        """Test that expected delivery is submitted date plus the lead time."""
        from datetime import datetime, timedelta

        order = client.post("/api/restocking/orders", json={
            "budget": 5000, "items": [{"item_sku": "TMP-201", "quantity": 10}],
        }).json()
        submitted = datetime.fromisoformat(order["submitted_date"])
        expected = datetime.fromisoformat(order["expected_delivery"])
        assert expected - submitted == timedelta(days=order["lead_time_days"])

    def test_submitted_order_is_listed(self, client):
        """Test that submitted orders appear in the list, newest first."""
        first = client.post("/api/restocking/orders", json={
            "budget": 5000, "items": [{"item_sku": "TMP-201", "quantity": 10}],
        }).json()
        second = client.post("/api/restocking/orders", json={
            "budget": 5000, "items": [{"item_sku": "HMD-202", "quantity": 20}],
        }).json()

        orders = client.get("/api/restocking/orders").json()
        assert [o["id"] for o in orders] == [second["id"], first["id"]]

    def test_server_uses_catalog_prices(self, client):
        """Test that line totals come from the demand forecast unit cost."""
        demand = {d["item_sku"]: d for d in client.get("/api/demand").json()}
        order = client.post("/api/restocking/orders", json={
            "budget": 5000, "items": [{"item_sku": "TMP-201", "quantity": 10}],
        }).json()
        assert order["items"][0]["unit_cost"] == demand["TMP-201"]["unit_cost"]
        assert order["total_value"] == pytest.approx(10 * demand["TMP-201"]["unit_cost"])

    def test_order_over_budget_rejected(self, client):
        """Test that an order exceeding its budget is rejected and not stored."""
        response = client.post("/api/restocking/orders", json={
            "budget": 100, "items": [{"item_sku": "SRV-302", "quantity": 10}],
        })
        assert response.status_code == 400
        assert "exceeds budget" in response.json()["detail"]
        assert client.get("/api/restocking/orders").json() == []

    def test_unknown_sku_rejected(self, client):
        """Test that an unknown SKU is rejected."""
        response = client.post("/api/restocking/orders", json={
            "budget": 5000, "items": [{"item_sku": "NOPE-999", "quantity": 1}],
        })
        assert response.status_code == 400
        assert "NOPE-999" in response.json()["detail"]

    def test_duplicate_sku_rejected(self, client):
        """Test that the same SKU twice in one order is rejected."""
        response = client.post("/api/restocking/orders", json={
            "budget": 5000,
            "items": [{"item_sku": "TMP-201", "quantity": 1}, {"item_sku": "TMP-201", "quantity": 2}],
        })
        assert response.status_code == 400

    @pytest.mark.parametrize("payload", [
        {"budget": 5000, "items": []},
        {"budget": 5000, "items": [{"item_sku": "TMP-201", "quantity": 0}]},
        {"budget": 0, "items": [{"item_sku": "TMP-201", "quantity": 1}]},
        {"items": [{"item_sku": "TMP-201", "quantity": 1}]},
        {"budget": "inf", "items": [{"item_sku": "TMP-201", "quantity": 1000000000}]},
        {"budget": 5000, "items": [{"item_sku": "TMP-201", "quantity": 1000000000}]},
    ])
    def test_invalid_order_payload(self, client, payload):
        """Test that malformed order payloads are rejected."""
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 422
