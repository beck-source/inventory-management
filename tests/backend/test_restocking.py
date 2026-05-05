"""
Tests for Restocking API endpoints.

Covers:
- GET /api/restocking/recommendations  (greedy budget fill)
- POST /api/restocking/orders          (submit a restocking order)
- GET /api/restocking/orders           (list submitted orders, newest first)
"""
from datetime import datetime, timedelta

import pytest

import main


@pytest.fixture(autouse=True)
def reset_restock_state():
    """Reset in-memory restocking state before each test.

    submitted_restock_orders and _next_restock_seq are module globals so they
    survive between tests in the same session; without a reset, later tests
    see orders created by earlier ones.
    """
    main.submitted_restock_orders.clear()
    main._next_restock_seq = 1
    yield
    main.submitted_restock_orders.clear()
    main._next_restock_seq = 1


def _shortage_items():
    """Return demand-forecast items that have a positive shortage."""
    return [
        f for f in main.demand_forecasts
        if f["forecasted_demand"] - f["current_demand"] > 0
    ]


class TestRestockRecommendations:
    """Test suite for GET /api/restocking/recommendations."""

    def test_zero_budget_includes_nothing(self, client):
        """With budget=0 every shortage line should be excluded."""
        response = client.get("/api/restocking/recommendations?budget=0")
        assert response.status_code == 200

        data = response.json()
        assert data["budget"] == 0
        assert data["total_cost"] == 0
        assert data["items_covered"] == 0
        assert data["items_total"] == len(_shortage_items())
        assert all(item["included"] is False for item in data["items"])

    def test_huge_budget_includes_everything(self, client):
        """With a very large budget every shortage line should be included."""
        response = client.get("/api/restocking/recommendations?budget=999999")
        assert response.status_code == 200

        data = response.json()
        assert data["items_covered"] == data["items_total"]
        assert all(item["included"] is True for item in data["items"])
        # total_cost should equal the sum of all line costs
        expected_total = sum(item["line_cost"] for item in data["items"])
        assert abs(data["total_cost"] - expected_total) < 0.01

    def test_items_sorted_by_shortage_desc(self, client):
        """Items must be returned largest shortage first (cost as tiebreak)."""
        response = client.get("/api/restocking/recommendations?budget=10000")
        data = response.json()

        shortages = [item["shortage"] for item in data["items"]]
        assert shortages == sorted(shortages, reverse=True)

    def test_only_positive_shortages_returned(self, client):
        """Items where forecast <= current demand should not appear."""
        response = client.get("/api/restocking/recommendations?budget=10000")
        data = response.json()

        for item in data["items"]:
            assert item["shortage"] > 0

        # MTR-304 is 'decreasing' (forecast < current) so it must never appear.
        skus = {item["sku"] for item in data["items"]}
        assert "MTR-304" not in skus

    def test_greedy_total_never_exceeds_budget(self, client):
        """The sum of included line costs must stay within budget."""
        for budget in [1000, 5000, 15000, 20000, 25000]:
            response = client.get(f"/api/restocking/recommendations?budget={budget}")
            data = response.json()

            included_total = sum(i["line_cost"] for i in data["items"] if i["included"])
            assert included_total <= budget
            assert abs(data["total_cost"] - included_total) < 0.01
            assert data["items_covered"] == sum(1 for i in data["items"] if i["included"])

    def test_skip_and_continue_greedy(self, client):
        """A line that doesn't fit must not block cheaper lines further down.

        At a budget where the largest line is too expensive, the algorithm
        should skip it and still include cheaper items below it.
        """
        # Find the most expensive line cost across all shortages.
        full = client.get("/api/restocking/recommendations?budget=999999").json()
        max_line = max(i["line_cost"] for i in full["items"])

        # Pick a budget just below that line — it can't afford the biggest item
        # but should afford some cheaper ones.
        budget = max_line - 1
        data = client.get(f"/api/restocking/recommendations?budget={budget}").json()
        assert data["items_covered"] > 0, "skip-greedy should still cover cheap items"

    def test_recommendation_structure(self, client):
        """Each recommendation row must have the full set of fields."""
        response = client.get("/api/restocking/recommendations?budget=15000")
        data = response.json()

        required = {
            "sku", "name", "trend", "shortage",
            "unit_cost", "line_cost", "lead_time_days", "included",
        }
        for item in data["items"]:
            assert required.issubset(item.keys())
            assert isinstance(item["shortage"], int)
            assert isinstance(item["unit_cost"], (int, float))
            assert isinstance(item["lead_time_days"], int)
            assert item["lead_time_days"] > 0
            # line_cost should be shortage * unit_cost
            assert abs(item["line_cost"] - item["shortage"] * item["unit_cost"]) < 0.01

    def test_negative_budget_rejected(self, client):
        """Budget must be >= 0 — query validation should return 422."""
        response = client.get("/api/restocking/recommendations?budget=-5")
        assert response.status_code == 422

    def test_missing_budget_rejected(self, client):
        """Budget is a required query param."""
        response = client.get("/api/restocking/recommendations")
        assert response.status_code == 422


class TestSubmitRestockOrder:
    """Test suite for POST /api/restocking/orders."""

    def _valid_payload(self):
        return {
            "budget": 20000,
            "items": [
                {"sku": "WDG-001", "quantity": 150, "unit_cost": 95.0},
                {"sku": "FLT-405", "quantity": 150, "unit_cost": 22.75},
            ],
        }

    def test_create_order_returns_201(self, client):
        """A valid POST should return 201 with the created order."""
        response = client.post("/api/restocking/orders", json=self._valid_payload())
        assert response.status_code == 201

        order = response.json()
        assert order["order_number"].startswith("RST-")
        assert order["status"] == "Submitted"
        assert len(order["items"]) == 2

    def test_order_number_increments(self, client):
        """Each new order should get a sequential RST-YYYY-NNNN number."""
        r1 = client.post("/api/restocking/orders", json=self._valid_payload()).json()
        r2 = client.post("/api/restocking/orders", json=self._valid_payload()).json()

        year = datetime.now().year
        assert r1["order_number"] == f"RST-{year}-0001"
        assert r2["order_number"] == f"RST-{year}-0002"

    def test_total_value_calculation(self, client):
        """total_value must equal sum(quantity * unit_cost) across items."""
        payload = self._valid_payload()
        response = client.post("/api/restocking/orders", json=payload)
        order = response.json()

        expected = sum(i["quantity"] * i["unit_cost"] for i in payload["items"])
        assert abs(order["total_value"] - expected) < 0.01

    def test_expected_delivery_uses_lead_time(self, client):
        """Each line's expected_delivery must be submitted_at + lead_time_days."""
        response = client.post("/api/restocking/orders", json=self._valid_payload())
        order = response.json()

        submitted = datetime.fromisoformat(order["submitted_at"])
        # Lead times come from demand_forecasts.json: WDG-001=21d, FLT-405=5d.
        leads_by_sku = {f["item_sku"]: f["lead_time_days"] for f in main.demand_forecasts}
        for item in order["items"]:
            expected = submitted + timedelta(days=leads_by_sku[item["sku"]])
            actual = datetime.fromisoformat(item["expected_delivery"])
            assert abs((actual - expected).total_seconds()) < 1
            assert item["lead_time_days"] == leads_by_sku[item["sku"]]

    def test_unknown_sku_rejected(self, client):
        """A SKU not present in demand_forecasts should return 400."""
        payload = {
            "budget": 1000,
            "items": [{"sku": "NOPE-000", "quantity": 1, "unit_cost": 1.0}],
        }
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 400
        assert "Unknown SKU" in response.json()["detail"]

    def test_empty_items_rejected(self, client):
        """An order with no items should fail Pydantic validation (422)."""
        response = client.post(
            "/api/restocking/orders",
            json={"budget": 1000, "items": []},
        )
        assert response.status_code == 422

    def test_invalid_quantity_rejected(self, client):
        """quantity must be > 0."""
        response = client.post(
            "/api/restocking/orders",
            json={"budget": 1000, "items": [{"sku": "WDG-001", "quantity": 0, "unit_cost": 1.0}]},
        )
        assert response.status_code == 422


class TestListSubmittedOrders:
    """Test suite for GET /api/restocking/orders."""

    def test_empty_when_nothing_submitted(self, client):
        """With no orders submitted, the list should be empty."""
        response = client.get("/api/restocking/orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_submitted_orders_newest_first(self, client):
        """Orders should come back in reverse chronological order."""
        for sku in ["WDG-001", "GSK-203", "FLT-405"]:
            client.post(
                "/api/restocking/orders",
                json={"budget": 5000, "items": [{"sku": sku, "quantity": 1, "unit_cost": 1.0}]},
            )

        response = client.get("/api/restocking/orders")
        orders = response.json()
        assert len(orders) == 3

        year = datetime.now().year
        # Newest (highest sequence) first.
        assert orders[0]["order_number"] == f"RST-{year}-0003"
        assert orders[1]["order_number"] == f"RST-{year}-0002"
        assert orders[2]["order_number"] == f"RST-{year}-0001"


class TestDemandForecastSchema:
    """Verify the demand forecast model carries the new restocking fields."""

    def test_demand_forecasts_have_unit_cost_and_lead_time(self, client):
        """All demand forecast rows must include unit_cost and lead_time_days."""
        response = client.get("/api/demand")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0
        for forecast in data:
            assert "unit_cost" in forecast
            assert "lead_time_days" in forecast
            assert isinstance(forecast["unit_cost"], (int, float))
            assert forecast["unit_cost"] > 0
            assert isinstance(forecast["lead_time_days"], int)
            assert forecast["lead_time_days"] > 0
