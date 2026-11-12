"""
Tests for restocking API endpoints (recommendations and restock orders).
"""
from datetime import datetime, timedelta

import pytest

import main


@pytest.fixture(autouse=True)
def clear_restock_orders():
    """Restock orders are stored in module-level memory; reset between tests."""
    main.restock_orders.clear()
    yield
    main.restock_orders.clear()


def _get_recommendation(client, budget):
    response = client.get(f"/api/restock/recommendations?budget={budget}")
    assert response.status_code == 200
    return response.json()


def _forecasts_by_sku(client):
    return {f["item_sku"]: f for f in client.get("/api/demand").json()}


class TestRestockRecommendations:
    """Test suite for GET /api/restock/recommendations."""

    def test_recommendation_structure(self, client):
        """Test that the recommendation response has the expected shape."""
        data = _get_recommendation(client, 5000)

        for field in ["budget", "total_cost", "remaining_budget", "max_useful_budget", "items"]:
            assert field in data
        assert data["budget"] == 5000
        assert isinstance(data["items"], list)

        for item in data["items"]:
            for field in ["sku", "name", "quantity", "unit_cost", "line_total", "lead_time_days"]:
                assert field in item
            assert isinstance(item["quantity"], int)
            assert item["quantity"] > 0
            assert abs(item["line_total"] - item["quantity"] * item["unit_cost"]) < 0.01

    def test_zero_budget_returns_no_items(self, client):
        """Test that a zero budget recommends nothing."""
        data = _get_recommendation(client, 0)
        assert data["items"] == []
        assert data["total_cost"] == 0
        assert data["remaining_budget"] == 0

    def test_max_budget_fills_every_gap(self, client):
        """Test that max_useful_budget buys the full gap of every positive-gap item."""
        max_budget = _get_recommendation(client, 0)["max_useful_budget"]
        data = _get_recommendation(client, max_budget)

        forecasts = _forecasts_by_sku(client)
        expected = {
            sku: f["forecasted_demand"] - f["current_demand"]
            for sku, f in forecasts.items()
            if f["forecasted_demand"] - f["current_demand"] > 0
        }
        assert {i["sku"]: i["quantity"] for i in data["items"]} == expected
        assert abs(data["total_cost"] - max_budget) < 0.01

    def test_items_without_demand_gap_excluded(self, client):
        """Test that items with flat or falling demand are never recommended."""
        max_budget = _get_recommendation(client, 0)["max_useful_budget"]
        data = _get_recommendation(client, max_budget * 10)

        forecasts = _forecasts_by_sku(client)
        for item in data["items"]:
            f = forecasts[item["sku"]]
            assert f["forecasted_demand"] > f["current_demand"]
        assert "MTR-304" not in {i["sku"] for i in data["items"]}

    def test_increasing_trends_prioritized(self, client):
        """Test that increasing-trend items are ordered before stable ones."""
        max_budget = _get_recommendation(client, 0)["max_useful_budget"]
        data = _get_recommendation(client, max_budget)

        forecasts = _forecasts_by_sku(client)
        trends = [forecasts[i["sku"]]["trend"] for i in data["items"]]
        first_stable = trends.index("stable")
        assert all(t == "increasing" for t in trends[:first_stable])
        assert "increasing" not in trends[first_stable:]

    @pytest.mark.parametrize("budget", [1, 100, 2500, 6375.5, 9999])
    def test_total_never_exceeds_budget(self, client, budget):
        """Test that the recommended total stays within budget."""
        data = _get_recommendation(client, budget)
        assert data["total_cost"] <= budget
        assert abs(data["remaining_budget"] - (budget - data["total_cost"])) < 0.01

    def test_partial_fill_of_last_item(self, client):
        """Test that a budget short of the top item's full cost buys floor(budget / unit_cost) units."""
        full = _get_recommendation(client, _get_recommendation(client, 0)["max_useful_budget"])
        top = full["items"][0]
        budget = top["line_total"] - 1

        data = _get_recommendation(client, budget)
        assert len(data["items"]) == 1
        assert data["items"][0]["sku"] == top["sku"]
        assert data["items"][0]["quantity"] == int(budget // top["unit_cost"])

    def test_negative_budget_rejected(self, client):
        """Test that a negative budget fails validation."""
        response = client.get("/api/restock/recommendations?budget=-1")
        assert response.status_code == 422

    def test_missing_budget_rejected(self, client):
        """Test that budget is a required parameter."""
        response = client.get("/api/restock/recommendations")
        assert response.status_code == 422


class TestRestockOrders:
    """Test suite for POST/GET /api/restock-orders."""

    def test_get_restock_orders_empty(self, client):
        """Test that no orders exist before any are submitted."""
        response = client.get("/api/restock-orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_restock_order(self, client):
        """Test submitting a recommended order and its computed fields."""
        rec = _get_recommendation(client, 5000)
        payload = {
            "budget": 5000,
            "items": [{"sku": i["sku"], "quantity": i["quantity"]} for i in rec["items"]],
        }

        response = client.post("/api/restock-orders", json=payload)
        assert response.status_code == 201

        order = response.json()
        assert order["status"] == "Submitted"
        assert order["order_number"].startswith("RST-")
        assert abs(order["total_cost"] - rec["total_cost"]) < 0.01
        assert order["lead_time_days"] == max(i["lead_time_days"] for i in rec["items"])

        submitted = datetime.fromisoformat(order["submitted_date"])
        expected = datetime.fromisoformat(order["expected_delivery"])
        assert expected - submitted == timedelta(days=order["lead_time_days"])

    def test_created_order_listed_newest_first(self, client):
        """Test that submitted orders are returned newest first."""
        for sku in ["GSK-203", "FLT-405"]:
            response = client.post(
                "/api/restock-orders",
                json={"budget": 10000, "items": [{"sku": sku, "quantity": 1}]},
            )
            assert response.status_code == 201

        orders = client.get("/api/restock-orders").json()
        assert len(orders) == 2
        assert orders[0]["items"][0]["sku"] == "FLT-405"
        assert orders[1]["items"][0]["sku"] == "GSK-203"

    def test_prices_come_from_server(self, client):
        """Test that line prices are taken from forecast data, not the request."""
        forecasts = _forecasts_by_sku(client)
        response = client.post(
            "/api/restock-orders",
            json={"budget": 10000, "items": [{"sku": "WDG-001", "quantity": 10, "unit_cost": 0.01}]},
        )
        assert response.status_code == 201
        assert response.json()["items"][0]["unit_cost"] == forecasts["WDG-001"]["unit_cost"]

    def test_unknown_sku_returns_404(self, client):
        """Test that ordering an unknown SKU fails."""
        response = client.post(
            "/api/restock-orders",
            json={"budget": 1000, "items": [{"sku": "NOPE-999", "quantity": 1}]},
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_over_budget_returns_400(self, client):
        """Test that an order costing more than the budget is rejected and not stored."""
        response = client.post(
            "/api/restock-orders",
            json={"budget": 10, "items": [{"sku": "WDG-001", "quantity": 100}]},
        )
        assert response.status_code == 400
        assert "exceeds budget" in response.json()["detail"]
        assert client.get("/api/restock-orders").json() == []

    @pytest.mark.parametrize("payload", [
        {"budget": 1000, "items": [{"sku": "WDG-001", "quantity": 0}]},
        {"budget": 1000, "items": []},
        {"budget": -5, "items": [{"sku": "WDG-001", "quantity": 1}]},
    ])
    def test_invalid_payload_returns_422(self, client, payload):
        """Test that zero quantities, empty orders, and negative budgets fail validation."""
        response = client.post("/api/restock-orders", json=payload)
        assert response.status_code == 422

    def test_duplicate_skus_rejected(self, client):
        """Test that an order listing the same SKU twice is rejected."""
        response = client.post(
            "/api/restock-orders",
            json={"budget": 10000, "items": [{"sku": "GSK-203", "quantity": 1}, {"sku": "GSK-203", "quantity": 2}]},
        )
        assert response.status_code == 400
        assert "only once" in response.json()["detail"]

    def test_order_exactly_at_budget_accepted(self, client):
        """Test that an order costing exactly the budget passes the cent-precise check."""
        response = client.post(
            "/api/restock-orders",
            json={"budget": 18.99 * 7, "items": [{"sku": "PSU-501", "quantity": 7}]},
        )
        assert response.status_code == 201


class TestRestockCentPrecision:
    """Budget math must be exact at cent boundaries."""

    def test_exact_budget_buys_exact_units(self):
        """Test that a budget equal to N * unit_cost buys N units, not N - 1."""
        from main import build_restock_recommendation
        # WDG-001 is first priority at 42.50; 0.1-style float drift must not lose a unit.
        for qty in [1, 3, 7, 149]:
            rec = build_restock_recommendation(42.5 * qty)
            assert rec["items"][0]["sku"] == "WDG-001"
            assert rec["items"][0]["quantity"] == qty
