"""
Tests for restocking API endpoints (recommendations and submitted orders).
"""
from datetime import datetime, timedelta

import pytest

import mock_data


@pytest.fixture(autouse=True)
def clear_restocking_orders():
    """Restocking orders live in a module-level list; reset it around each test."""
    mock_data.restocking_orders.clear()
    yield
    mock_data.restocking_orders.clear()


def get_recommendations(client, budget):
    response = client.get(f"/api/restocking/recommendations?budget={budget}")
    assert response.status_code == 200
    return response.json()


class TestRestockRecommendations:
    """Test suite for the budget-based recommendation endpoint."""

    def test_zero_budget_returns_no_items(self, client):
        """A zero budget recommends nothing but still reports max_budget."""
        data = get_recommendations(client, 0)
        assert data["items"] == []
        assert data["total_cost"] == 0
        assert data["max_budget"] > 0

    def test_full_budget_covers_every_positive_gap(self, client):
        """Budget >= max_budget restocks every growing item at its full gap."""
        forecasts = client.get("/api/demand").json()
        expected = {f["item_sku"]: f["forecasted_demand"] - f["current_demand"]
                    for f in forecasts if f["forecasted_demand"] > f["current_demand"]}

        max_budget = get_recommendations(client, 0)["max_budget"]
        data = get_recommendations(client, max_budget)

        assert {i["sku"]: i["quantity"] for i in data["items"]} == expected
        assert data["total_cost"] == pytest.approx(max_budget)

    @pytest.mark.parametrize("budget", [0, 50, 999.99, 5000, 12345, 10_000_000])
    def test_total_never_exceeds_budget(self, client, budget):
        """Planned spend stays within budget and line totals add up."""
        data = get_recommendations(client, budget)
        assert data["total_cost"] <= budget
        assert data["remaining_budget"] == pytest.approx(budget - data["total_cost"])
        assert data["total_cost"] == pytest.approx(sum(i["line_total"] for i in data["items"]))
        for item in data["items"]:
            assert 0 < item["quantity"] <= item["demand_gap"]
            assert item["line_total"] == pytest.approx(item["quantity"] * item["unit_cost"])

    def test_increasing_trend_items_come_first(self, client):
        """All increasing-trend items are ordered before any other trend."""
        data = get_recommendations(client, 10_000_000)
        trends = [i["trend"].lower() == "increasing" for i in data["items"]]
        assert trends == sorted(trends, reverse=True)
        assert trends[0] is True

    def test_decreasing_items_never_recommended(self, client):
        """Items with falling demand (e.g. MTR-304) have no gap to restock."""
        data = get_recommendations(client, 10_000_000)
        skus = [i["sku"] for i in data["items"]]
        assert "MTR-304" not in skus
        assert all(i["trend"].lower() != "decreasing" for i in data["items"])

    def test_partial_fill_when_budget_is_tight(self, client):
        """A budget below the top item's gap cost buys a partial quantity of it."""
        top = get_recommendations(client, 10_000_000)["items"][0]
        budget = top["line_total"] / 2
        data = get_recommendations(client, budget)

        first = data["items"][0]
        assert first["sku"] == top["sku"]
        assert first["quantity"] < top["quantity"]
        assert data["total_cost"] <= budget

    def test_missing_budget_rejected(self, client):
        response = client.get("/api/restocking/recommendations")
        assert response.status_code == 422

    def test_negative_budget_rejected(self, client):
        response = client.get("/api/restocking/recommendations?budget=-1")
        assert response.status_code == 422


class TestRestockOrders:
    """Test suite for submitting and listing restocking orders."""

    def test_no_orders_initially(self, client):
        response = client.get("/api/restocking/orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_order(self, client):
        """Submitting an order stores the server-computed recommendation."""
        budget = 5000
        expected = get_recommendations(client, budget)

        response = client.post("/api/restocking/orders", json={"budget": budget})
        assert response.status_code == 201
        order = response.json()

        assert order["order_number"].startswith("RST-")
        assert order["status"] == "Submitted"
        assert order["budget"] == budget
        assert order["total_cost"] == pytest.approx(expected["total_cost"])
        assert order["items"] == expected["items"]

    def test_expected_delivery_uses_max_lead_time(self, client):
        """Delivery date is creation time plus the slowest item's lead time."""
        order = client.post("/api/restocking/orders", json={"budget": 10_000_000}).json()

        max_lead = max(i["lead_time_days"] for i in order["items"])
        assert order["lead_time_days"] == max_lead

        created = datetime.fromisoformat(order["created_at"])
        delivery = datetime.fromisoformat(order["expected_delivery"])
        assert delivery - created == timedelta(days=max_lead)

    def test_orders_listed_newest_first(self, client):
        first = client.post("/api/restocking/orders", json={"budget": 1000}).json()
        second = client.post("/api/restocking/orders", json={"budget": 2000}).json()

        listed = client.get("/api/restocking/orders").json()
        assert [o["order_number"] for o in listed] == [second["order_number"], first["order_number"]]
        assert first["order_number"] != second["order_number"]

    def test_budget_too_small_returns_400(self, client):
        """A budget below the cheapest unit cost can't buy anything."""
        response = client.post("/api/restocking/orders", json={"budget": 0.01})
        assert response.status_code == 400
        assert "detail" in response.json()
        assert client.get("/api/restocking/orders").json() == []

    @pytest.mark.parametrize("payload", [{"budget": 0}, {"budget": -100}, {}, {"budget": "abc"}])
    def test_invalid_budget_rejected(self, client, payload):
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 422
