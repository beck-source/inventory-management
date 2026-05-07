"""
Tests for the restocking API endpoints.
"""
import pytest

import main as server_main


@pytest.fixture(autouse=True)
def reset_submitted_orders():
    """Reset in-memory submission state before each test.

    The restocking POST endpoint mutates module-level state in main.py
    (submitted_orders list and _submitted_seq counter). Tests share the
    same app instance, so we wipe both before every test to keep order
    counts and IDs predictable.
    """
    server_main.submitted_orders.clear()
    server_main._submitted_seq = 0
    yield
    server_main.submitted_orders.clear()
    server_main._submitted_seq = 0


class TestRestockingRecommendations:
    """Test suite for GET /api/restocking/recommendations."""

    def test_recommendations_default_budget(self, client):
        """Default budget returns a non-empty recommendation list."""
        response = client.get("/api/restocking/recommendations")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        first = data[0]
        for field in [
            "sku", "name", "warehouse", "category", "unit_cost",
            "quantity_on_hand", "reorder_point", "forecasted_demand",
            "tier", "shortfall", "urgency", "recommended_quantity", "line_total",
        ]:
            assert field in first, f"Missing field: {field}"

    def test_recommendations_respect_budget(self, client):
        """Sum of line_totals never exceeds the requested budget."""
        for budget in [5_000, 25_000, 100_000, 500_000]:
            response = client.get(f"/api/restocking/recommendations?budget={budget}")
            assert response.status_code == 200
            data = response.json()
            total = sum(item["line_total"] for item in data)
            assert total <= budget + 0.01, f"Total {total} exceeds budget {budget}"

    def test_recommendations_zero_budget_returns_empty(self, client):
        """A zero budget produces no recommendations."""
        response = client.get("/api/restocking/recommendations?budget=0")
        assert response.status_code == 200
        assert response.json() == []

    def test_recommendations_negative_budget_rejected(self, client):
        """Negative budget returns 400."""
        response = client.get("/api/restocking/recommendations?budget=-100")
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_recommendations_exclude_decreasing_trend(self, client):
        """Items with decreasing demand should never be recommended."""
        response = client.get("/api/restocking/recommendations?budget=500000")
        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert item["trend"] != "decreasing"

    def test_recommendations_urgency_values(self, client):
        """Every recommendation has one of the three valid urgency values."""
        response = client.get("/api/restocking/recommendations?budget=500000")
        data = response.json()
        valid = {"urgent", "rising", "stable"}
        for item in data:
            assert item["urgency"] in valid
            # Tier and urgency must agree
            assert (item["tier"], item["urgency"]) in {
                (1, "urgent"), (2, "rising"), (3, "stable")
            }

    def test_recommendations_tier_ordering(self, client):
        """Tier 1 items must come before tier 2, tier 2 before tier 3."""
        response = client.get("/api/restocking/recommendations?budget=500000")
        data = response.json()
        tiers = [item["tier"] for item in data]
        assert tiers == sorted(tiers)

    def test_recommendations_recommended_quantity_positive(self, client):
        """Every recommended quantity must be at least 1."""
        response = client.get("/api/restocking/recommendations?budget=500000")
        data = response.json()
        for item in data:
            assert item["recommended_quantity"] >= 1
            # Line total math sanity check
            expected = round(item["recommended_quantity"] * item["unit_cost"], 2)
            assert abs(item["line_total"] - expected) < 0.01


class TestSubmitRestockingOrder:
    """Test suite for POST /api/restocking/orders."""

    def test_submit_creates_one_order_per_warehouse(self, client):
        """A cart spanning N warehouses creates N submitted orders."""
        # Pull the recommendation list so we know real SKUs that span warehouses
        recs = client.get("/api/restocking/recommendations?budget=500000").json()
        assert len(recs) >= 2

        warehouses_seen = {r["warehouse"] for r in recs}
        # Pick the first SKU from each distinct warehouse to ensure a multi-warehouse cart
        cart = []
        chosen_warehouses = set()
        for r in recs:
            if r["warehouse"] not in chosen_warehouses:
                cart.append({"sku": r["sku"], "quantity": r["recommended_quantity"]})
                chosen_warehouses.add(r["warehouse"])

        response = client.post(
            "/api/restocking/orders",
            json={"items": cart, "budget": 500000},
        )
        assert response.status_code == 200
        new_orders = response.json()
        assert isinstance(new_orders, list)
        assert len(new_orders) == len(chosen_warehouses)
        assert {o["warehouse"] for o in new_orders} == chosen_warehouses

    def test_submit_assigns_sequential_ids(self, client):
        """SUB-XXX IDs increment monotonically across submissions."""
        recs = client.get("/api/restocking/recommendations?budget=500000").json()
        assert len(recs) > 0
        first_sku = recs[0]["sku"]

        # Two single-item submissions to the same warehouse
        for _ in range(2):
            client.post(
                "/api/restocking/orders",
                json={"items": [{"sku": first_sku, "quantity": 1}], "budget": 500000},
            )

        response = client.get("/api/restocking/orders")
        all_orders = response.json()
        ids = [o["id"] for o in all_orders]
        assert ids == ["SUB-001", "SUB-002"]

    def test_submit_lead_time_matches_warehouse(self, client):
        """Each submitted order's lead_time_days matches the LEAD_TIMES table."""
        expected_lead = {"San Francisco": 7, "London": 14, "Tokyo": 21}
        recs = client.get("/api/restocking/recommendations?budget=500000").json()

        # Find one rec per warehouse so we exercise all three lead times
        per_warehouse = {}
        for r in recs:
            per_warehouse.setdefault(r["warehouse"], r)
        cart = [
            {"sku": r["sku"], "quantity": 1}
            for r in per_warehouse.values()
        ]
        response = client.post(
            "/api/restocking/orders",
            json={"items": cart, "budget": 500000},
        )
        new_orders = response.json()
        for order in new_orders:
            assert order["lead_time_days"] == expected_lead[order["warehouse"]]

    def test_submit_total_value_matches_line_totals(self, client):
        """total_value equals the sum of line_total for every line."""
        recs = client.get("/api/restocking/recommendations?budget=500000").json()
        cart = [{"sku": r["sku"], "quantity": 2} for r in recs[:3]]
        response = client.post(
            "/api/restocking/orders",
            json={"items": cart, "budget": 500000},
        )
        new_orders = response.json()
        for order in new_orders:
            line_sum = sum(line["line_total"] for line in order["items"])
            assert abs(order["total_value"] - line_sum) < 0.01

    def test_submit_status_is_submitted(self, client):
        """Every new order has status='Submitted'."""
        recs = client.get("/api/restocking/recommendations?budget=500000").json()
        response = client.post(
            "/api/restocking/orders",
            json={"items": [{"sku": recs[0]["sku"], "quantity": 1}], "budget": 500000},
        )
        for order in response.json():
            assert order["status"] == "Submitted"

    def test_submit_empty_cart_rejected(self, client):
        """An empty cart returns 400."""
        response = client.post(
            "/api/restocking/orders",
            json={"items": [], "budget": 100000},
        )
        assert response.status_code == 400

    def test_submit_unknown_sku_rejected(self, client):
        """An unknown SKU returns 400 with a helpful detail."""
        response = client.post(
            "/api/restocking/orders",
            json={"items": [{"sku": "BOGUS-999", "quantity": 1}], "budget": 100000},
        )
        assert response.status_code == 400
        assert "BOGUS-999" in response.json()["detail"]

    def test_submit_zero_quantity_rejected(self, client):
        """Quantity < 1 returns 400."""
        recs = client.get("/api/restocking/recommendations?budget=500000").json()
        response = client.post(
            "/api/restocking/orders",
            json={"items": [{"sku": recs[0]["sku"], "quantity": 0}], "budget": 100000},
        )
        assert response.status_code == 400


class TestSubmittedOrdersList:
    """Test suite for GET /api/restocking/orders."""

    def test_list_starts_empty(self, client):
        """Fresh state means no submitted orders."""
        response = client.get("/api/restocking/orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_includes_submitted_orders(self, client):
        """Submitted orders appear in subsequent GETs."""
        recs = client.get("/api/restocking/recommendations?budget=500000").json()
        client.post(
            "/api/restocking/orders",
            json={"items": [{"sku": recs[0]["sku"], "quantity": 3}], "budget": 500000},
        )
        response = client.get("/api/restocking/orders")
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "SUB-001"
        assert len(data[0]["items"]) == 1
        assert data[0]["items"][0]["sku"] == recs[0]["sku"]
        assert data[0]["items"][0]["quantity"] == 3
