"""
Tests for restocking API endpoints.
"""
from datetime import datetime, timedelta

import pytest

RECOMMENDATION_FIELDS = [
    "sku", "name", "category", "warehouse", "quantity_on_hand", "reorder_point",
    "forecasted_demand", "shortfall", "recommended_quantity", "unit_cost",
    "line_total", "lead_time_days",
]
HUGE_BUDGET = 10_000_000


def recommend(client, budget):
    response = client.get(f"/api/restocking/recommendations?budget={budget}")
    assert response.status_code == 200
    return response.json()


def order_payload(client, budget=100000):
    """Build a valid order payload from the current recommendations."""
    recs = recommend(client, budget)
    return {
        "budget": budget,
        "items": [
            {"sku": r["sku"], "quantity": r["recommended_quantity"]}
            for r in recs["items"]
        ],
    }


class TestRestockingRecommendations:
    """Test suite for the recommendations endpoint."""

    def test_zero_budget_recommends_nothing(self, client):
        """Test that a zero budget yields no items."""
        data = recommend(client, 0)
        assert data["items"] == []
        assert data["total_cost"] == 0
        assert data["remaining_budget"] == 0

    def test_budget_defaults_to_zero(self, client):
        """Test that omitting the budget behaves like a zero budget."""
        response = client.get("/api/restocking/recommendations")
        assert response.status_code == 200
        assert response.json()["items"] == []

    def test_negative_budget_rejected(self, client):
        """Test that a negative budget is a validation error."""
        response = client.get("/api/restocking/recommendations?budget=-1")
        assert response.status_code == 422

    def test_recommendation_structure_and_types(self, client):
        """Test the response structure and field types."""
        data = recommend(client, 100000)
        assert len(data["items"]) > 0
        for key in ["budget", "total_cost", "remaining_budget", "items"]:
            assert key in data

        for item in data["items"]:
            for field in RECOMMENDATION_FIELDS:
                assert field in item
            assert isinstance(item["recommended_quantity"], int)
            assert isinstance(item["lead_time_days"], int)
            assert isinstance(item["unit_cost"], (int, float))

    @pytest.mark.parametrize("budget", [1000, 25000, 100000, 250000, 500000])
    def test_total_never_exceeds_budget(self, client, budget):
        """Test that recommended spend stays within the budget."""
        data = recommend(client, budget)
        assert data["total_cost"] <= budget
        assert abs(data["remaining_budget"] - (budget - data["total_cost"])) < 0.01

        line_sum = sum(item["line_total"] for item in data["items"])
        assert abs(line_sum - data["total_cost"]) < 0.01

    def test_line_totals_match_quantity_times_unit_cost(self, client):
        """Test that each line total is quantity times unit cost."""
        for item in recommend(client, 100000)["items"]:
            assert abs(item["line_total"] - item["recommended_quantity"] * item["unit_cost"]) < 0.01

    def test_quantity_never_exceeds_shortfall(self, client):
        """Test that no item is recommended beyond its shortfall."""
        for item in recommend(client, 100000)["items"]:
            assert 0 < item["recommended_quantity"] <= item["shortfall"]

    def test_large_budget_covers_every_shortfall(self, client):
        """Test that an unconstrained budget fills each shortfall completely."""
        data = recommend(client, HUGE_BUDGET)
        assert len(data["items"]) > 0
        for item in data["items"]:
            assert item["recommended_quantity"] == item["shortfall"]

    def test_only_forecasted_skus_are_recommended(self, client):
        """Test that recommendations come from the demand forecast."""
        forecast_skus = {f["item_sku"] for f in client.get("/api/demand").json()}
        for item in recommend(client, HUGE_BUDGET)["items"]:
            assert item["sku"] in forecast_skus

    def test_skus_are_unique(self, client):
        """Test that each SKU is recommended at most once."""
        skus = [item["sku"] for item in recommend(client, HUGE_BUDGET)["items"]]
        assert len(skus) == len(set(skus))

    def test_items_at_or_below_reorder_point_come_first(self, client):
        """Test urgency ordering: below-reorder-point items precede the rest."""
        items = recommend(client, HUGE_BUDGET)["items"]
        urgent = [i["quantity_on_hand"] <= i["reorder_point"] for i in items]
        # Once a non-urgent item appears, no urgent item may follow
        assert urgent == sorted(urgent, reverse=True)
        assert any(urgent)

    def test_urgent_items_ordered_by_shortfall(self, client):
        """Test that urgent items are ordered by largest shortfall first."""
        items = recommend(client, HUGE_BUDGET)["items"]
        urgent_shortfalls = [
            i["shortfall"] for i in items if i["quantity_on_hand"] <= i["reorder_point"]
        ]
        assert urgent_shortfalls == sorted(urgent_shortfalls, reverse=True)

    def test_lead_time_matches_category(self, client):
        """Test that lead times are derived from the category table."""
        lead_by_category = {}
        for item in recommend(client, HUGE_BUDGET)["items"]:
            assert item["lead_time_days"] > 0
            lead_by_category.setdefault(item["category"], set()).add(item["lead_time_days"])
        for category, leads in lead_by_category.items():
            assert len(leads) == 1, f"{category} has inconsistent lead times"

    def test_partial_fill_when_budget_is_tight(self, client):
        """Test that a small budget partially fills the top-ranked item."""
        full = recommend(client, HUGE_BUDGET)["items"][0]
        budget = full["unit_cost"] * 3 + 1
        data = recommend(client, budget)
        assert len(data["items"]) >= 1
        assert data["items"][0]["sku"] == full["sku"]
        assert data["items"][0]["recommended_quantity"] == 3


class TestRestockingOrders:
    """Test suite for submitting and listing restocking orders."""

    def test_list_starts_empty(self, client):
        """Test that no orders exist before any are submitted."""
        response = client.get("/api/restocking-orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_order(self, client):
        """Test submitting a valid order."""
        payload = order_payload(client)
        response = client.post("/api/restocking-orders", json=payload)
        assert response.status_code == 201

        order = response.json()
        for field in [
            "id", "order_number", "items", "total_cost", "budget", "status",
            "order_date", "lead_time_days", "expected_delivery",
        ]:
            assert field in order
        assert order["order_number"].startswith("RST-")
        assert order["status"] == "Submitted"
        assert order["budget"] == payload["budget"]
        assert len(order["items"]) == len(payload["items"])
        assert order["total_cost"] <= payload["budget"]

    def test_order_total_matches_lines(self, client):
        """Test that the total equals the sum of line totals."""
        order = client.post("/api/restocking-orders", json=order_payload(client)).json()
        for item in order["items"]:
            assert abs(item["line_total"] - item["quantity"] * item["unit_cost"]) < 0.01
        assert abs(order["total_cost"] - sum(i["line_total"] for i in order["items"])) < 0.01

    def test_order_lead_time_is_longest_item_lead_time(self, client):
        """Test that the order lead time is the maximum across items."""
        order = client.post("/api/restocking-orders", json=order_payload(client)).json()
        assert order["lead_time_days"] == max(i["lead_time_days"] for i in order["items"])

    def test_expected_delivery_is_lead_time_after_order_date(self, client):
        """Test the delivery date arithmetic."""
        order = client.post("/api/restocking-orders", json=order_payload(client)).json()
        ordered = datetime.fromisoformat(order["order_date"])
        expected = datetime.fromisoformat(order["expected_delivery"])
        assert expected - ordered == timedelta(days=order["lead_time_days"])

    def test_prices_come_from_inventory_not_client(self, client):
        """Test that client-supplied prices cannot change the cost."""
        payload = order_payload(client)
        payload["items"][0]["unit_cost"] = 0.01
        order = client.post("/api/restocking-orders", json=payload).json()

        inventory = {i["sku"]: i for i in client.get("/api/inventory").json()}
        for item in order["items"]:
            assert item["unit_cost"] == inventory[item["sku"]]["unit_cost"]

    def test_created_order_appears_in_list(self, client):
        """Test that a submitted order is returned by the list endpoint."""
        created = client.post("/api/restocking-orders", json=order_payload(client)).json()
        orders = client.get("/api/restocking-orders").json()
        assert len(orders) == 1
        assert orders[0]["id"] == created["id"]

    def test_orders_listed_newest_first(self, client):
        """Test list ordering and unique numbering."""
        first = client.post("/api/restocking-orders", json=order_payload(client)).json()
        second = client.post("/api/restocking-orders", json=order_payload(client)).json()
        assert first["order_number"] != second["order_number"]

        orders = client.get("/api/restocking-orders").json()
        assert [o["id"] for o in orders] == [second["id"], first["id"]]

    def test_over_budget_rejected(self, client):
        """Test that an order costing more than its budget is rejected."""
        payload = order_payload(client)
        payload["budget"] = 1
        response = client.post("/api/restocking-orders", json=payload)
        assert response.status_code == 400
        assert "budget" in response.json()["detail"].lower()
        assert client.get("/api/restocking-orders").json() == []

    def test_empty_items_rejected(self, client):
        """Test that an order with no items is rejected."""
        response = client.post("/api/restocking-orders", json={"budget": 1000, "items": []})
        assert response.status_code == 400

    def test_unknown_sku_rejected(self, client):
        """Test that an unknown SKU returns 404."""
        payload = {"budget": 1000, "items": [{"sku": "NOPE-999", "quantity": 1}]}
        response = client.post("/api/restocking-orders", json=payload)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_duplicate_skus_rejected(self, client):
        """Test that repeating a SKU is rejected."""
        sku = recommend(client, 100000)["items"][0]["sku"]
        payload = {
            "budget": 100000,
            "items": [{"sku": sku, "quantity": 1}, {"sku": sku, "quantity": 2}],
        }
        response = client.post("/api/restocking-orders", json=payload)
        assert response.status_code == 400

    @pytest.mark.parametrize("quantity", [0, -5])
    def test_non_positive_quantity_rejected(self, client, quantity):
        """Test that zero or negative quantities fail validation."""
        sku = recommend(client, 100000)["items"][0]["sku"]
        payload = {"budget": 100000, "items": [{"sku": sku, "quantity": quantity}]}
        response = client.post("/api/restocking-orders", json=payload)
        assert response.status_code == 422

    def test_negative_budget_rejected(self, client):
        """Test that a negative budget fails validation."""
        payload = order_payload(client)
        payload["budget"] = -1
        response = client.post("/api/restocking-orders", json=payload)
        assert response.status_code == 422

    def test_submitting_order_does_not_affect_existing_data(self, client):
        """Test that customer orders, inventory and dashboard KPIs are unchanged."""
        orders_before = client.get("/api/orders").json()
        inventory_before = client.get("/api/inventory").json()
        summary_before = client.get("/api/dashboard/summary").json()

        client.post("/api/restocking-orders", json=order_payload(client))

        assert client.get("/api/orders").json() == orders_before
        assert client.get("/api/inventory").json() == inventory_before
        assert client.get("/api/dashboard/summary").json() == summary_before
