"""
Tests for restocking API endpoints.
"""
import pytest

import main


@pytest.fixture(autouse=True)
def clear_submitted_orders():
    """Reset submitted restocking orders so each test starts from a clean slate.

    The endpoint stores orders in a module-level list, so without this the order
    numbering and counts would depend on which tests ran before.
    """
    main.submitted_restock_orders.clear()
    yield
    main.submitted_restock_orders.clear()


@pytest.fixture
def plan(client):
    """A restocking plan with a budget large enough to fund several items."""
    response = client.get("/api/restock/recommendations?budget=5000")
    assert response.status_code == 200
    return response.json()


def to_order_lines(recommendations):
    """Convert plan recommendations into the request shape POST expects."""
    return [
        {
            "item_sku": rec["item_sku"],
            "item_name": rec["item_name"],
            "supplier": rec["supplier"],
            "quantity": rec["recommended_quantity"],
            "unit_cost": rec["unit_cost"],
            "line_total": rec["line_total"],
            "lead_time_days": rec["lead_time_days"]
        }
        for rec in recommendations
    ]


class TestRestockRecommendations:
    """Test suite for the restocking recommendation endpoint."""

    def test_get_recommendations(self, client):
        """Test getting a restocking plan for a budget."""
        response = client.get("/api/restock/recommendations?budget=5000")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)

        for field in [
            "budget", "recommendations", "skipped", "total_cost",
            "remaining_budget", "total_need", "items_recommended",
            "items_skipped", "total_units", "max_lead_time_days"
        ]:
            assert field in data

        assert data["budget"] == 5000
        assert isinstance(data["recommendations"], list)
        assert len(data["recommendations"]) > 0

    def test_recommendation_structure(self, plan):
        """Test that each recommendation exposes the full item contract."""
        for rec in plan["recommendations"]:
            assert "item_sku" in rec
            assert "item_name" in rec
            assert "supplier" in rec
            assert "trend" in rec
            assert "demand_gap" in rec
            assert "recommended_quantity" in rec
            assert "unit_cost" in rec
            assert "line_total" in rec
            assert "lead_time_days" in rec
            assert "priority_score" in rec

    def test_recommendation_types(self, plan):
        """Test that numeric recommendation fields have proper types and ranges."""
        for rec in plan["recommendations"]:
            assert isinstance(rec["demand_gap"], int)
            assert isinstance(rec["recommended_quantity"], int)
            assert isinstance(rec["lead_time_days"], int)
            assert isinstance(rec["unit_cost"], (int, float))
            assert isinstance(rec["line_total"], (int, float))
            assert isinstance(rec["priority_score"], (int, float))

            assert rec["demand_gap"] > 0
            assert rec["recommended_quantity"] > 0
            assert rec["unit_cost"] > 0
            assert rec["lead_time_days"] > 0

    def test_line_total_calculation(self, plan):
        """Test that each line total is quantity multiplied by unit cost."""
        for rec in plan["recommendations"]:
            expected = rec["recommended_quantity"] * rec["unit_cost"]
            assert abs(rec["line_total"] - expected) < 0.01

    def test_total_cost_matches_line_totals(self, plan):
        """Test that the plan total is the sum of its recommended lines."""
        expected = sum(rec["line_total"] for rec in plan["recommendations"])
        assert abs(plan["total_cost"] - expected) < 0.01

    def test_total_cost_within_budget(self, client):
        """Test that allocated cost never exceeds the budget, at any budget."""
        for budget in [0, 500, 1500, 5000, 9702, 20000]:
            response = client.get(f"/api/restock/recommendations?budget={budget}")
            assert response.status_code == 200

            data = response.json()
            assert data["total_cost"] <= budget + 0.01
            assert abs(data["remaining_budget"] - (budget - data["total_cost"])) < 0.01

    def test_recommendations_ordered_by_priority(self, plan):
        """Test that recommendations come back in descending priority order."""
        scores = [rec["priority_score"] for rec in plan["recommendations"]]
        assert scores == sorted(scores, reverse=True)

    def test_priority_score_applies_trend_weight(self, plan):
        """Test that priority score is the demand gap weighted by trend."""
        weights = {"increasing": 1.5, "stable": 1.0, "decreasing": 0.5}

        for rec in plan["recommendations"] + plan["skipped"]:
            expected = rec["demand_gap"] * weights[rec["trend"]]
            assert abs(rec["priority_score"] - expected) < 0.05

    def test_decreasing_demand_excluded(self, client):
        """Test that items with no positive demand gap are never recommended."""
        # MTR-304 forecasts 35 against current demand of 50, so it has no gap.
        response = client.get("/api/restock/recommendations?budget=100000")
        data = response.json()

        all_skus = [
            rec["item_sku"] for rec in data["recommendations"] + data["skipped"]
        ]
        assert "MTR-304" not in all_skus

    def test_zero_budget_recommends_nothing(self, client):
        """Test that a zero budget funds no items."""
        response = client.get("/api/restock/recommendations?budget=0")
        assert response.status_code == 200

        data = response.json()
        assert data["items_recommended"] == 0
        assert data["recommendations"] == []
        assert data["total_cost"] == 0
        assert data["max_lead_time_days"] == 0
        assert data["items_skipped"] > 0

    def test_large_budget_funds_everything(self, client):
        """Test that a budget above total need leaves nothing skipped."""
        response = client.get("/api/restock/recommendations?budget=100000")
        assert response.status_code == 200

        data = response.json()
        assert data["items_skipped"] == 0
        assert data["skipped"] == []
        assert abs(data["total_cost"] - data["total_need"]) < 0.01

    def test_negative_budget_rejected(self, client):
        """Test that a negative budget is a validation error."""
        response = client.get("/api/restock/recommendations?budget=-100")
        assert response.status_code == 422

    def test_counts_match_lists(self, plan):
        """Test that the reported counts match the returned lists."""
        assert plan["items_recommended"] == len(plan["recommendations"])
        assert plan["items_skipped"] == len(plan["skipped"])
        assert plan["total_units"] == sum(
            rec["recommended_quantity"] for rec in plan["recommendations"]
        )

    def test_max_lead_time_is_slowest_line(self, plan):
        """Test that max lead time is the longest lead time among funded items."""
        expected = max(rec["lead_time_days"] for rec in plan["recommendations"])
        assert plan["max_lead_time_days"] == expected

    def test_recommendations_are_deterministic(self, client):
        """Test that the same budget always produces the same plan."""
        first = client.get("/api/restock/recommendations?budget=4200").json()
        second = client.get("/api/restock/recommendations?budget=4200").json()
        assert first == second


class TestRestockOrderSubmission:
    """Test suite for submitting and retrieving restocking orders."""

    def test_submit_order(self, client, plan):
        """Test submitting a restocking order."""
        response = client.post("/api/restock-orders", json={
            "budget": plan["budget"],
            "items": to_order_lines(plan["recommendations"])
        })
        assert response.status_code == 201

        order = response.json()
        assert order["order_number"] == "RO-1001"
        assert order["status"] == "Submitted"
        assert order["item_count"] == plan["items_recommended"]
        assert order["total_units"] == plan["total_units"]
        assert abs(order["total_cost"] - plan["total_cost"]) < 0.01
        assert order["max_lead_time_days"] == plan["max_lead_time_days"]

    def test_submitted_order_structure(self, client, plan):
        """Test that a submitted order exposes the full contract."""
        response = client.post("/api/restock-orders", json={
            "budget": plan["budget"],
            "items": to_order_lines(plan["recommendations"])
        })
        order = response.json()

        for field in [
            "id", "order_number", "status", "submitted_date",
            "expected_delivery", "max_lead_time_days", "budget",
            "total_cost", "item_count", "total_units", "items"
        ]:
            assert field in order

        assert isinstance(order["items"], list)
        assert len(order["items"]) == order["item_count"]

    def test_expected_delivery_uses_max_lead_time(self, client, plan):
        """Test that expected delivery is submitted date plus the longest lead time."""
        from datetime import date, timedelta

        response = client.post("/api/restock-orders", json={
            "budget": plan["budget"],
            "items": to_order_lines(plan["recommendations"])
        })
        order = response.json()

        submitted = date.fromisoformat(order["submitted_date"])
        expected = submitted + timedelta(days=order["max_lead_time_days"])
        assert order["expected_delivery"] == expected.isoformat()

    def test_order_dates_are_iso_format(self, client, plan):
        """Test that submitted and delivery dates are ISO dates."""
        from datetime import date

        response = client.post("/api/restock-orders", json={
            "budget": plan["budget"],
            "items": to_order_lines(plan["recommendations"])
        })
        order = response.json()

        # Raises ValueError if the format is not YYYY-MM-DD.
        date.fromisoformat(order["submitted_date"])
        date.fromisoformat(order["expected_delivery"])

    def test_submit_empty_order_rejected(self, client):
        """Test that an order with no items is rejected."""
        response = client.post("/api/restock-orders", json={
            "budget": 5000,
            "items": []
        })
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert "at least one item" in data["detail"].lower()

    def test_submit_malformed_order_rejected(self, client):
        """Test that an item missing required fields is a validation error."""
        response = client.post("/api/restock-orders", json={
            "budget": 5000,
            "items": [{"item_sku": "WDG-001"}]
        })
        assert response.status_code == 422

    def test_get_orders_empty_initially(self, client):
        """Test that no restocking orders exist before any are submitted."""
        response = client.get("/api/restock-orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_orders_after_submission(self, client, plan):
        """Test that a submitted order is retrievable."""
        created = client.post("/api/restock-orders", json={
            "budget": plan["budget"],
            "items": to_order_lines(plan["recommendations"])
        }).json()

        response = client.get("/api/restock-orders")
        assert response.status_code == 200

        orders = response.json()
        assert len(orders) == 1
        assert orders[0]["order_number"] == created["order_number"]

    def test_order_numbers_increment(self, client, plan):
        """Test that each submitted order gets the next sequential number."""
        payload = {
            "budget": plan["budget"],
            "items": to_order_lines(plan["recommendations"])
        }

        numbers = [
            client.post("/api/restock-orders", json=payload).json()["order_number"]
            for _ in range(3)
        ]
        assert numbers == ["RO-1001", "RO-1002", "RO-1003"]

    def test_orders_returned_newest_first(self, client, plan):
        """Test that the order list is ordered newest to oldest."""
        payload = {
            "budget": plan["budget"],
            "items": to_order_lines(plan["recommendations"])
        }
        for _ in range(3):
            client.post("/api/restock-orders", json=payload)

        orders = client.get("/api/restock-orders").json()
        assert [o["order_number"] for o in orders] == [
            "RO-1003", "RO-1002", "RO-1001"
        ]

    def test_submitted_items_preserve_plan_lines(self, client, plan):
        """Test that submitted line items round-trip unchanged."""
        lines = to_order_lines(plan["recommendations"])

        order = client.post("/api/restock-orders", json={
            "budget": plan["budget"],
            "items": lines
        }).json()

        assert order["items"] == lines


class TestDemandForecastRestockFields:
    """Test suite for the restocking fields added to demand forecasts."""

    def test_forecasts_expose_restock_fields(self, client):
        """Test that every forecast carries cost, lead time and supplier."""
        response = client.get("/api/demand")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0

        for forecast in data:
            assert "unit_cost" in forecast
            assert "lead_time_days" in forecast
            assert "supplier" in forecast

            assert isinstance(forecast["unit_cost"], (int, float))
            assert isinstance(forecast["lead_time_days"], int)
            assert isinstance(forecast["supplier"], str)

            assert forecast["unit_cost"] > 0
            assert forecast["lead_time_days"] > 0
            assert forecast["supplier"] != ""

    def test_recommendations_match_forecast_data(self, client):
        """Test that plan lines carry the same cost and lead time as the forecast."""
        forecasts = {f["item_sku"]: f for f in client.get("/api/demand").json()}
        data = client.get("/api/restock/recommendations?budget=100000").json()

        for rec in data["recommendations"]:
            forecast = forecasts[rec["item_sku"]]
            assert rec["unit_cost"] == forecast["unit_cost"]
            assert rec["lead_time_days"] == forecast["lead_time_days"]
            assert rec["supplier"] == forecast["supplier"]
            assert rec["demand_gap"] == (
                forecast["forecasted_demand"] - forecast["current_demand"]
            )
