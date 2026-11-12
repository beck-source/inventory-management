"""
Tests for Restocking API endpoints.
"""
import json
from datetime import datetime, timedelta

import pytest

import mock_data
from main import build_restock_recommendation, recommended_quantity


@pytest.fixture
def isolated_submitted_orders(tmp_path, monkeypatch):
    """Redirect order persistence to a temp file and start from an empty list,
    so tests never touch server/data/submitted_orders.json."""
    path = tmp_path / "submitted_orders.json"
    path.write_text("[]")
    monkeypatch.setattr(mock_data, "SUBMITTED_ORDERS_FILE", str(path))
    saved = list(mock_data.submitted_orders)
    mock_data.submitted_orders.clear()
    yield path
    # Restore in place: main.py references the same list object
    mock_data.submitted_orders.clear()
    mock_data.submitted_orders.extend(saved)


class TestRestockRecommendations:
    """Test suite for GET /api/restocking/recommendations."""

    def test_recommendation_structure(self, client):
        """Test response structure and item fields."""
        response = client.get("/api/restocking/recommendations?budget=3000")
        assert response.status_code == 200

        data = response.json()
        for key in ["budget", "items", "total_cost", "remaining_budget", "full_cost"]:
            assert key in data
        assert len(data["items"]) > 0
        for item in data["items"]:
            for key in ["sku", "name", "quantity", "unit_cost", "line_total", "lead_time_days", "trend"]:
                assert key in item
            assert isinstance(item["quantity"], int)
            assert item["quantity"] >= 1
            assert abs(item["line_total"] - item["quantity"] * item["unit_cost"]) < 0.01

    @pytest.mark.parametrize("budget", [100, 1234.56, 3000, 5000])
    def test_recommendation_respects_budget(self, client, budget):
        """Test that total cost never exceeds the budget."""
        data = client.get(f"/api/restocking/recommendations?budget={budget}").json()
        assert data["total_cost"] <= budget
        assert abs(data["remaining_budget"] - (budget - data["total_cost"])) < 0.01
        assert abs(sum(i["line_total"] for i in data["items"]) - data["total_cost"]) < 0.01

    def test_zero_budget_returns_no_items(self, client):
        """Test that a zero budget recommends nothing."""
        data = client.get("/api/restocking/recommendations?budget=0").json()
        assert data["items"] == []
        assert data["total_cost"] == 0

    def test_large_budget_covers_all_items_at_full_quantity(self, client):
        """Test that a budget above full_cost recommends every forecast item in full."""
        forecasts = client.get("/api/demand").json()
        data = client.get("/api/restocking/recommendations?budget=1000000").json()

        assert len(data["items"]) == len(forecasts)
        by_sku = {f["item_sku"]: f for f in forecasts}
        for item in data["items"]:
            assert item["quantity"] == recommended_quantity(by_sku[item["sku"]])
        assert abs(data["total_cost"] - data["full_cost"]) < 0.01

    def test_items_ordered_by_priority(self, client):
        """Test that items are ranked by trend, then growth ratio."""
        data = client.get("/api/restocking/recommendations?budget=1000000").json()
        rank = {"increasing": 0, "stable": 1, "decreasing": 2}
        trend_ranks = [rank[i["trend"]] for i in data["items"]]
        assert trend_ranks == sorted(trend_ranks)

    def test_highest_priority_item_filled_first(self, client):
        """Test that a small budget goes to the top-priority item first."""
        full = client.get("/api/restocking/recommendations?budget=1000000").json()
        top = full["items"][0]
        data = client.get(f"/api/restocking/recommendations?budget={top['line_total']}").json()
        assert data["items"][0]["sku"] == top["sku"]
        assert data["items"][0]["quantity"] == top["quantity"]

    def test_negative_budget_rejected(self, client):
        """Test that a negative budget returns a validation error."""
        response = client.get("/api/restocking/recommendations?budget=-1")
        assert response.status_code == 422

    def test_missing_budget_rejected(self, client):
        """Test that budget is required."""
        response = client.get("/api/restocking/recommendations")
        assert response.status_code == 422

    def test_partial_quantity_when_item_does_not_fit(self):
        """Test the greedy helper buys whole units of an item it cannot fully afford."""
        forecasts = [{
            "item_sku": "A", "item_name": "A", "current_demand": 100, "forecasted_demand": 200,
            "trend": "increasing", "unit_cost": 10.0, "lead_time_days": 5,
        }]
        result = build_restock_recommendation(255, forecasts)
        assert result["items"][0]["quantity"] == 25
        assert result["remaining_budget"] == 5


class TestSubmittedOrders:
    """Test suite for POST/GET /api/restocking/orders."""

    def test_submit_order(self, client, isolated_submitted_orders):
        """Test submitting an order computes totals and lead time server-side."""
        forecasts = {f["item_sku"]: f for f in client.get("/api/demand").json()}
        payload = {"items": [{"sku": "WDG-001", "quantity": 10}, {"sku": "GSK-203", "quantity": 5}]}

        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 201

        order = response.json()
        assert order["status"] == "Submitted"
        assert order["order_number"].startswith("RST-")
        expected_total = 10 * forecasts["WDG-001"]["unit_cost"] + 5 * forecasts["GSK-203"]["unit_cost"]
        assert abs(order["total_cost"] - expected_total) < 0.01

    def test_lead_time_is_max_of_items(self, client, isolated_submitted_orders):
        """Test order lead time equals the slowest item and expected delivery matches."""
        forecasts = {f["item_sku"]: f for f in client.get("/api/demand").json()}
        skus = ["WDG-001", "MTR-304", "FLT-405"]
        payload = {"items": [{"sku": s, "quantity": 1} for s in skus]}

        order = client.post("/api/restocking/orders", json=payload).json()
        expected_lead = max(forecasts[s]["lead_time_days"] for s in skus)
        assert order["lead_time_days"] == expected_lead

        submitted = datetime.fromisoformat(order["submitted_date"])
        delivery = datetime.fromisoformat(order["expected_delivery"])
        assert delivery - submitted == timedelta(days=expected_lead)

    def test_unknown_sku_rejected(self, client, isolated_submitted_orders):
        """Test that an unknown SKU returns 400 and nothing is saved."""
        response = client.post("/api/restocking/orders", json={"items": [{"sku": "NOPE-999", "quantity": 1}]})
        assert response.status_code == 400
        assert "detail" in response.json()
        assert client.get("/api/restocking/orders").json() == []

    @pytest.mark.parametrize("quantity", [0, -5])
    def test_non_positive_quantity_rejected(self, client, isolated_submitted_orders, quantity):
        """Test that zero or negative quantities fail validation."""
        response = client.post("/api/restocking/orders", json={"items": [{"sku": "WDG-001", "quantity": quantity}]})
        assert response.status_code == 422

    def test_empty_items_rejected(self, client, isolated_submitted_orders):
        """Test that an order with no items fails validation."""
        response = client.post("/api/restocking/orders", json={"items": []})
        assert response.status_code == 422

    def test_submitted_order_listed_and_persisted(self, client, isolated_submitted_orders):
        """Test the order appears in GET (newest first) and is written to disk."""
        first = client.post("/api/restocking/orders", json={"items": [{"sku": "WDG-001", "quantity": 1}]}).json()
        second = client.post("/api/restocking/orders", json={"items": [{"sku": "GSK-203", "quantity": 2}]}).json()

        listed = client.get("/api/restocking/orders").json()
        assert len(listed) == 2
        assert {o["id"] for o in listed} == {first["id"], second["id"]}
        assert listed[0]["submitted_date"] >= listed[1]["submitted_date"]

        on_disk = json.loads(isolated_submitted_orders.read_text())
        assert [o["id"] for o in on_disk] == [first["id"], second["id"]]


class TestRestockingGuards:
    """Input guards added after code review."""

    @pytest.mark.parametrize("budget", ["inf", "1e308"])
    def test_unbounded_budget_rejected(self, client, budget):
        """Test that infinite/huge budgets are rejected instead of overflowing (500)."""
        response = client.get(f"/api/restocking/recommendations?budget={budget}")
        assert response.status_code == 422

    def test_duplicate_skus_rejected(self, client, isolated_submitted_orders):
        """Test that repeating a SKU in one order returns 400."""
        payload = {"items": [{"sku": "WDG-001", "quantity": 1}, {"sku": "WDG-001", "quantity": 2}]}
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 400

    def test_excessive_quantity_rejected(self, client, isolated_submitted_orders):
        """Test that quantities above the cap fail validation."""
        response = client.post("/api/restocking/orders", json={"items": [{"sku": "WDG-001", "quantity": 100001}]})
        assert response.status_code == 422

    def test_order_ids_unique_and_newest_first(self, client, isolated_submitted_orders):
        """Test sequential ids and newest-first ordering even within the same second."""
        ids = [
            client.post("/api/restocking/orders", json={"items": [{"sku": "WDG-001", "quantity": 1}]}).json()["id"]
            for _ in range(3)
        ]
        assert len(set(ids)) == 3
        listed = [o["id"] for o in client.get("/api/restocking/orders").json()]
        assert listed == list(reversed(ids))
