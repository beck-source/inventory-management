"""
Tests for the restocking API endpoints.
"""
import pytest

import main


@pytest.fixture
def controlled_data(monkeypatch):
    """Replace inventory_items/demand_forecasts with a small, known dataset
    so recommendation/urgency-fill tests don't depend on the real sample
    data (which currently produces zero real candidates - the one matching
    SKU, PSU-501, is already well-stocked)."""
    inventory = [
        {
            "id": "t1", "sku": "TEST-URGENT", "name": "Urgent Widget",
            "category": "Sensors", "warehouse": "Tokyo",
            "quantity_on_hand": 10, "reorder_point": 50, "unit_cost": 10.0,
            "location": "T-1", "last_updated": "2025-09-01T00:00:00"
        },
        {
            "id": "t2", "sku": "TEST-MILD", "name": "Mild Widget",
            "category": "Actuators", "warehouse": "Tokyo",
            "quantity_on_hand": 80, "reorder_point": 50, "unit_cost": 5.0,
            "location": "T-2", "last_updated": "2025-09-01T00:00:00"
        },
        {
            "id": "t3", "sku": "TEST-STOCKED", "name": "Stocked Widget",
            "category": "Controllers", "warehouse": "Tokyo",
            "quantity_on_hand": 500, "reorder_point": 50, "unit_cost": 20.0,
            "location": "T-3", "last_updated": "2025-09-01T00:00:00"
        },
    ]
    demand_forecasts = [
        # gap = 300 - 10 = 290 (most urgent)
        {
            "id": "d1", "item_sku": "TEST-URGENT", "item_name": "Urgent Widget",
            "current_demand": 250, "forecasted_demand": 300,
            "trend": "increasing", "period": "Next 30 days"
        },
        # gap = 100 - 80 = 20 (mildly urgent)
        {
            "id": "d2", "item_sku": "TEST-MILD", "item_name": "Mild Widget",
            "current_demand": 90, "forecasted_demand": 100,
            "trend": "stable", "period": "Next 30 days"
        },
        # gap = 100 - 500 = -400 (already well-stocked, not a candidate)
        {
            "id": "d3", "item_sku": "TEST-STOCKED", "item_name": "Stocked Widget",
            "current_demand": 90, "forecasted_demand": 100,
            "trend": "stable", "period": "Next 30 days"
        },
        # no matching inventory item, must be dropped
        {
            "id": "d4", "item_sku": "TEST-UNKNOWN", "item_name": "Unknown Widget",
            "current_demand": 10, "forecasted_demand": 999,
            "trend": "increasing", "period": "Next 30 days"
        },
    ]

    monkeypatch.setattr(main, "inventory_items", inventory)
    monkeypatch.setattr(main, "demand_forecasts", demand_forecasts)
    return inventory, demand_forecasts


class TestRestockRecommendationsEndpoint:
    """Test suite for GET /api/restocking/recommendations."""

    def test_bootstrap_with_no_budget_returns_full_gap_cost(self, client, controlled_data):
        """With no budget param, max_budget equals the cost of restocking
        every candidate's full gap, and budget_used matches max_budget since
        nothing is held back."""
        response = client.get("/api/restocking/recommendations")
        assert response.status_code == 200

        data = response.json()
        # TEST-URGENT: 290 * 10.0 = 2900, TEST-MILD: 20 * 5.0 = 100
        assert data["max_budget"] == pytest.approx(3000.0)
        assert data["budget_used"] == pytest.approx(3000.0)
        assert len(data["recommendations"]) == 2

    def test_excludes_unmatched_and_well_stocked_items(self, client, controlled_data):
        """SKUs with no inventory match or a non-positive gap are dropped."""
        response = client.get("/api/restocking/recommendations")
        data = response.json()

        skus = {rec["sku"] for rec in data["recommendations"]}
        assert skus == {"TEST-URGENT", "TEST-MILD"}

    def test_recommendations_ranked_by_urgency(self, client, controlled_data):
        """Largest gap (most urgent) is recommended first."""
        response = client.get("/api/restocking/recommendations")
        data = response.json()

        recs = data["recommendations"]
        assert recs[0]["sku"] == "TEST-URGENT"
        assert recs[0]["gap"] == 290
        assert recs[1]["sku"] == "TEST-MILD"
        assert recs[1]["gap"] == 20

    def test_budget_greedily_fills_most_urgent_first(self, client, controlled_data):
        """A budget that can only afford part of the most urgent item's gap
        should spend entirely on that item, never exceeding the budget."""
        response = client.get("/api/restocking/recommendations?budget=250")
        assert response.status_code == 200

        data = response.json()
        assert data["budget_used"] <= 250
        assert len(data["recommendations"]) == 1

        rec = data["recommendations"][0]
        assert rec["sku"] == "TEST-URGENT"
        # floor(250 / 10.0) = 25 units, capped by affordability not the full gap
        assert rec["recommended_quantity"] == 25
        assert rec["line_cost"] == pytest.approx(250.0)

    def test_budget_covering_urgent_item_spills_to_next(self, client, controlled_data):
        """Once the most urgent item's full gap is affordable, remaining
        budget is spent on the next-most-urgent item."""
        # Full urgent gap costs 2900; leave room for 10 units of TEST-MILD (50)
        response = client.get("/api/restocking/recommendations?budget=2950")
        data = response.json()

        recs = {rec["sku"]: rec for rec in data["recommendations"]}
        assert recs["TEST-URGENT"]["recommended_quantity"] == 290
        assert recs["TEST-MILD"]["recommended_quantity"] == 10
        assert data["budget_used"] <= 2950

    def test_zero_budget_returns_no_recommendations(self, client, controlled_data):
        """A budget of 0 can't afford anything."""
        response = client.get("/api/restocking/recommendations?budget=0")
        assert response.status_code == 200

        data = response.json()
        assert data["recommendations"] == []
        assert data["budget_used"] == 0

    def test_budget_fill_not_undercounted_by_float_precision(self, client, monkeypatch):
        """A budget that divides evenly into a realistic (2-decimal) unit
        cost should not be shorted a unit by float division error
        (e.g. 149.95 // 29.99 == 4.0 in raw floor division, one short of the
        exact 5 units 29.99 * 5 == 149.95 affords)."""
        inventory = [{
            "id": "p1", "sku": "TEST-PENNY", "name": "Penny-Priced Widget",
            "category": "Sensors", "warehouse": "Tokyo",
            "quantity_on_hand": 0, "reorder_point": 50, "unit_cost": 29.99,
            "location": "T-1", "last_updated": "2025-09-01T00:00:00"
        }]
        demand_forecasts = [{
            "id": "d1", "item_sku": "TEST-PENNY", "item_name": "Penny-Priced Widget",
            "current_demand": 0, "forecasted_demand": 50,
            "trend": "increasing", "period": "Next 30 days"
        }]
        monkeypatch.setattr(main, "inventory_items", inventory)
        monkeypatch.setattr(main, "demand_forecasts", demand_forecasts)

        response = client.get("/api/restocking/recommendations?budget=149.95")
        data = response.json()

        assert len(data["recommendations"]) == 1
        assert data["recommendations"][0]["recommended_quantity"] == 5
        assert data["recommendations"][0]["line_cost"] == pytest.approx(149.95)

    def test_recommendation_includes_lead_time(self, client, controlled_data):
        """Each recommendation carries a lead time derived from its category."""
        response = client.get("/api/restocking/recommendations")
        data = response.json()

        for rec in data["recommendations"]:
            assert isinstance(rec["lead_time_days"], int)
            assert rec["lead_time_days"] > 0


class TestSubmitRestockingOrderEndpoint:
    """Test suite for POST /api/restocking/orders."""

    def test_submit_valid_order(self, client):
        """Submitting a valid order returns 201 with computed fields."""
        response = client.post("/api/restocking/orders", json={
            "budget": 500,
            "items": [
                {"sku": "PCB-001", "name": "Single Layer PCB Assembly", "quantity": 10, "unit_price": 24.99}
            ]
        })
        assert response.status_code == 201

        data = response.json()
        assert data["order_number"].startswith("RSO-")
        assert data["status"] == "Processing"
        assert data["total_value"] == pytest.approx(249.9)
        assert data["lead_time_days"] > 0
        assert "T" in data["order_date"]
        assert "T" in data["expected_delivery"]

    def test_submit_order_uses_category_lead_time(self, client):
        """Circuit Boards items should use the Circuit Boards lead time (14 days)."""
        response = client.post("/api/restocking/orders", json={
            "budget": 500,
            "items": [
                {"sku": "PCB-001", "name": "Single Layer PCB Assembly", "quantity": 1, "unit_price": 24.99}
            ]
        })
        data = response.json()
        assert data["lead_time_days"] == main.LEAD_TIME_BY_CATEGORY["Circuit Boards"]

    def test_submit_order_unknown_sku_returns_404(self, client):
        """An item referencing a SKU not in inventory is rejected."""
        response = client.post("/api/restocking/orders", json={
            "budget": 100,
            "items": [
                {"sku": "NOT-A-REAL-SKU", "name": "Nonexistent", "quantity": 1, "unit_price": 1.0}
            ]
        })
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_submit_order_appears_in_get_list(self, client):
        """A submitted order shows up in GET /api/restocking/orders."""
        submit_response = client.post("/api/restocking/orders", json={
            "budget": 500,
            "items": [
                {"sku": "PCB-002", "name": "Dual Layer PCB Assembly", "quantity": 5, "unit_price": 29.99}
            ]
        })
        assert submit_response.status_code == 201
        submitted_id = submit_response.json()["id"]

        list_response = client.get("/api/restocking/orders")
        assert list_response.status_code == 200

        order_ids = [order["id"] for order in list_response.json()]
        assert submitted_id in order_ids
