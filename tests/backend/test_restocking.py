"""
Tests for restocking API endpoints.

Note: `restocking_orders` in server/main.py is a module-level list with no
per-test reset (unlike the read-only JSON-backed lists), since it's runtime-
created state shared across the whole test session. Tests that create orders
assert monotonic increase in order numbers rather than a hardcoded literal.
"""
import pytest


class TestRestockingEndpoints:
    """Test suite for restocking-related endpoints."""

    def test_get_recommendations_happy_path(self, client):
        """Test getting recommendations for a reasonable budget."""
        response = client.get("/api/restocking/recommendations?budget=5000")
        assert response.status_code == 200

        data = response.json()
        assert data["budget"] == 5000
        assert isinstance(data["items"], list)
        assert data["allocated_cost"] <= data["budget"]
        assert round(data["allocated_cost"] + data["remaining_budget"], 2) == data["budget"]

        for item in data["items"]:
            assert "sku" in item
            assert "item_name" in item
            assert "target_quantity" in item
            assert "recommended_quantity" in item
            assert "line_cost" in item
            assert "fully_funded" in item
            assert "urgency_score" in item
            assert item["recommended_quantity"] <= item["target_quantity"]
            assert item["recommended_quantity"] >= 1

    def test_recommendations_sorted_by_urgency(self, client):
        """Test that low-stock items (urgency_score <= 0) come before adequate-stock items."""
        response = client.get("/api/restocking/recommendations?budget=999999999")
        data = response.json()

        urgency_scores = [item["urgency_score"] for item in data["items"]]
        assert urgency_scores == sorted(urgency_scores)

        # Items below/at reorder point (score <= 0) should all appear before
        # items in the adequate band (score > 0)
        below_reorder = [s for s in urgency_scores if s <= 0]
        above_reorder = [s for s in urgency_scores if s > 0]
        if below_reorder and above_reorder:
            last_below_index = max(i for i, s in enumerate(urgency_scores) if s <= 0)
            first_above_index = min(i for i, s in enumerate(urgency_scores) if s > 0)
            assert last_below_index < first_above_index

    def test_zero_budget_returns_no_items(self, client):
        """Test that a zero budget yields no recommendations."""
        response = client.get("/api/restocking/recommendations?budget=0")
        assert response.status_code == 200

        data = response.json()
        assert data["items"] == []
        assert data["allocated_cost"] == 0
        assert data["remaining_budget"] == 0

    def test_negative_budget_rejected(self, client):
        """Test that a negative budget returns 400."""
        response = client.get("/api/restocking/recommendations?budget=-100")
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_tiny_budget_partial_fill(self, client):
        """Test that a budget too small for the top item's full deficit still
        recommends a partially-funded quantity of it."""
        full_response = client.get("/api/restocking/recommendations?budget=999999999")
        full_items = full_response.json()["items"]
        assert len(full_items) > 0

        top_item = full_items[0]
        unit_cost = top_item["unit_cost"]
        # Budget for a few units, but fewer than the full target quantity
        tiny_budget = unit_cost * 2

        response = client.get(f"/api/restocking/recommendations?budget={tiny_budget}")
        assert response.status_code == 200
        data = response.json()

        assert len(data["items"]) == 1
        item = data["items"][0]
        assert item["sku"] == top_item["sku"]
        assert item["fully_funded"] is False
        assert item["recommended_quantity"] == int(tiny_budget // unit_cost)
        assert item["recommended_quantity"] < item["target_quantity"]

    def test_huge_budget_fully_funds_everything(self, client):
        """Test that with an effectively unlimited budget, every item is fully
        funded and already-adequate-stock items never appear."""
        response = client.get("/api/restocking/recommendations?budget=999999999")
        data = response.json()

        assert len(data["items"]) > 0
        for item in data["items"]:
            assert item["fully_funded"] is True
            # target_level = ceil(reorder_point * 1.5); items at/above that are excluded
            assert item["quantity_on_hand"] < item["reorder_point"] * 1.5

    def test_filter_by_warehouse(self, client):
        """Test that warehouse filtering narrows recommendations correctly."""
        response = client.get("/api/restocking/recommendations?budget=999999999&warehouse=Tokyo")
        assert response.status_code == 200

        data = response.json()
        for item in data["items"]:
            assert item["warehouse"] == "Tokyo"

    def test_filter_with_no_matches_returns_empty(self, client):
        """Test that filtering to a warehouse/category with no candidates returns
        an empty list without erroring."""
        response = client.get(
            "/api/restocking/recommendations?budget=999999999&warehouse=Nonexistent Warehouse"
        )
        assert response.status_code == 200
        assert response.json()["items"] == []

    def test_create_order_happy_path(self, client):
        """Test placing a restocking order."""
        response = client.get("/api/restocking/recommendations?budget=5000")
        assert len(response.json()["items"]) > 0

        response = client.post("/api/restocking/orders", json={"budget": 5000})
        assert response.status_code == 201

        order = response.json()
        assert order["id"]
        assert order["order_number"].startswith("RO-")
        assert len(order["order_number"]) == len("RO-0001")
        assert 5 <= order["lead_time_days"] <= 14
        assert order["status"] == "Ordered"
        assert len(order["items"]) > 0

        order_date = order["order_date"]
        expected_delivery = order["expected_delivery"]
        from datetime import datetime
        delta_days = (
            datetime.fromisoformat(expected_delivery) - datetime.fromisoformat(order_date)
        ).days
        assert delta_days == order["lead_time_days"]

        calculated_total = sum(item["line_cost"] for item in order["items"])
        assert abs(order["total_cost"] - calculated_total) < 0.01

    def test_create_order_zero_budget_rejected(self, client):
        """Test that placing an order with zero budget returns 400."""
        response = client.post("/api/restocking/orders", json={"budget": 0})
        assert response.status_code == 400

    def test_create_order_insufficient_budget_rejected(self, client):
        """Test that a budget too small to afford even one unit of anything returns 400."""
        response = client.post("/api/restocking/orders", json={"budget": 0.01})
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_orders_persist_and_list(self, client):
        """Test that created orders are persisted and retrievable, with
        monotonically increasing order numbers."""
        before = client.get("/api/restocking/orders").json()
        before_count = len(before)

        r1 = client.post("/api/restocking/orders", json={"budget": 2000})
        r2 = client.post("/api/restocking/orders", json={"budget": 2000})
        assert r1.status_code == 201
        assert r2.status_code == 201

        after = client.get("/api/restocking/orders").json()
        assert len(after) == before_count + 2

        num1 = int(r1.json()["order_number"].split("-")[1])
        num2 = int(r2.json()["order_number"].split("-")[1])
        assert num2 == num1 + 1

    def test_does_not_touch_purchase_orders(self, client):
        """Test that restocking orders are independent of the (unrelated,
        pre-existing) purchase-order data — creating a restocking order must
        not affect /api/backlog's has_purchase_order flags."""
        before = client.get("/api/backlog").json()
        client.post("/api/restocking/orders", json={"budget": 2000})
        after = client.get("/api/backlog").json()

        before_flags = [item["has_purchase_order"] for item in before]
        after_flags = [item["has_purchase_order"] for item in after]
        assert before_flags == after_flags

    def test_lead_time_is_randomized(self, client):
        """Test that lead time isn't hardcoded to a single value."""
        lead_times = set()
        for _ in range(6):
            response = client.post("/api/restocking/orders", json={"budget": 2000})
            assert response.status_code == 201
            lead_times.add(response.json()["lead_time_days"])

        assert len(lead_times) > 1
