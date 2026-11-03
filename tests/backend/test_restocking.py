"""
Tests for restocking API endpoints (recommendations + submitted orders).
"""
from datetime import datetime, timedelta

import pytest

import mock_data


@pytest.fixture(autouse=True)
def reset_restock_orders():
    """
    Submitted orders live in a module-level list shared by every test.
    Snapshot and restore it IN PLACE: main.py bound the same list object at import,
    so rebinding mock_data.restock_orders would not affect the app.
    """
    snapshot = list(mock_data.restock_orders)
    yield
    mock_data.restock_orders[:] = snapshot


TREND_WEIGHTS = {"increasing": 1.5, "stable": 1.0, "decreasing": 0.5}


def _forecasts(client):
    return client.get("/api/demand").json()


def _shortfall(f):
    return max(0, f["forecasted_demand"] - f["quantity_on_hand"])


def _full_budget(client):
    return client.get("/api/restocking/recommendations?budget=0").json()["max_budget"]


class TestRestockingEndpoints:
    """Test suite for restocking-related endpoints."""

    # --- Recommendations -------------------------------------------------

    def test_recommendations_structure(self, client):
        """Test the recommendations response shape and field types."""
        response = client.get("/api/restocking/recommendations?budget=10000")
        assert response.status_code == 200

        data = response.json()
        for key in ("budget", "max_budget", "items", "total_cost", "remaining"):
            assert key in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) > 0

        for item in data["items"]:
            for key in ("sku", "name", "trend", "shortfall", "quantity",
                        "unit_cost", "line_cost", "lead_time_days"):
                assert key in item
            assert isinstance(item["quantity"], int)
            assert isinstance(item["unit_cost"], (int, float))

    def test_recommendations_zero_budget(self, client):
        """Test that a zero budget recommends nothing but still reports max_budget."""
        response = client.get("/api/restocking/recommendations?budget=0")
        assert response.status_code == 200

        data = response.json()
        assert data["items"] == []
        assert data["total_cost"] == 0
        assert data["remaining"] == 0
        assert data["max_budget"] > 0

    def test_recommendations_default_budget(self, client):
        """Test that budget defaults to zero when omitted."""
        response = client.get("/api/restocking/recommendations")
        assert response.status_code == 200
        assert response.json()["items"] == []

    def test_recommendations_negative_budget_rejected(self, client):
        """Test that a negative budget fails validation."""
        response = client.get("/api/restocking/recommendations?budget=-5")
        assert response.status_code == 422

    @pytest.mark.parametrize("budget", [500, 2500, 9999.99, 20000, 36000])
    def test_recommendations_never_exceed_budget(self, client, budget):
        """Test that the recommended total stays within the budget and adds up."""
        data = client.get(f"/api/restocking/recommendations?budget={budget}").json()

        assert data["total_cost"] <= budget + 0.01
        assert abs(data["total_cost"] + data["remaining"] - budget) < 0.01
        assert abs(sum(i["line_cost"] for i in data["items"]) - data["total_cost"]) < 0.01

        for item in data["items"]:
            assert 0 < item["quantity"] <= item["shortfall"]
            assert abs(item["line_cost"] - item["quantity"] * item["unit_cost"]) < 0.01

    def test_recommendations_full_budget_covers_all_shortfalls(self, client):
        """Test that max_budget buys every shortfall in full."""
        max_budget = _full_budget(client)
        data = client.get(f"/api/restocking/recommendations?budget={max_budget}").json()

        for item in data["items"]:
            assert item["quantity"] == item["shortfall"]

        expected_skus = {f["item_sku"] for f in _forecasts(client) if _shortfall(f) > 0}
        assert {i["sku"] for i in data["items"]} == expected_skus
        assert abs(data["total_cost"] - max_budget) < 0.01

    def test_recommendations_max_budget_calculation(self, client):
        """Test that max_budget matches shortfall x unit_cost summed over forecasts."""
        expected = sum(_shortfall(f) * f["unit_cost"] for f in _forecasts(client))
        assert abs(_full_budget(client) - expected) < 0.01

    def test_recommendations_skip_items_without_shortfall(self, client):
        """Test that items already covered by stock are never recommended."""
        covered = {f["item_sku"] for f in _forecasts(client) if _shortfall(f) == 0}
        assert len(covered) > 0  # the demo data must include some covered items

        data = client.get(f"/api/restocking/recommendations?budget={_full_budget(client)}").json()
        assert covered.isdisjoint({i["sku"] for i in data["items"]})

    def test_recommendations_ranked_by_weighted_shortfall(self, client):
        """Test that, with a full budget, items are ordered by shortfall x trend weight."""
        data = client.get(f"/api/restocking/recommendations?budget={_full_budget(client)}").json()

        scores = [i["shortfall"] * TREND_WEIGHTS[i["trend"]] for i in data["items"]]
        assert scores == sorted(scores, reverse=True)

    def test_recommendations_partial_fill_when_budget_is_tight(self, client):
        """Test that the budget is spent down to less than one more unit of any item left over."""
        data = client.get("/api/restocking/recommendations?budget=1000").json()
        partial = [i for i in data["items"] if i["quantity"] < i["shortfall"]]
        assert len(partial) > 0  # 1000 cannot cover the top-ranked item in full

        # An item is only cut short when the budget could not afford another unit of it.
        # Later purchases can only reduce what is left, so the final remainder is
        # smaller than the unit cost of every partially-filled item.
        for item in partial:
            assert data["remaining"] < item["unit_cost"]

    # --- Placing orders --------------------------------------------------

    def _place_order(self, client, budget=10000, lines=None):
        if lines is None:
            rec = client.get(f"/api/restocking/recommendations?budget={budget}").json()
            lines = [{"sku": i["sku"], "quantity": i["quantity"]} for i in rec["items"]]
        return client.post("/api/restocking/orders", json={"budget": budget, "items": lines})

    def test_create_restock_order(self, client):
        """Test submitting a recommended order."""
        budget = 10000
        rec = client.get(f"/api/restocking/recommendations?budget={budget}").json()
        response = self._place_order(client, budget)
        assert response.status_code == 201

        order = response.json()
        for key in ("id", "order_number", "items", "total_value", "budget",
                    "status", "order_date", "lead_time_days", "expected_delivery"):
            assert key in order
        assert order["order_number"].startswith("RST-")
        assert order["status"] == "Submitted"
        assert order["budget"] == budget
        assert abs(order["total_value"] - rec["total_cost"]) < 0.01
        assert len(order["items"]) == len(rec["items"])

    def test_restock_order_lead_time_is_longest_item(self, client):
        """Test that order lead time is the max item lead time and drives expected delivery."""
        order = self._place_order(client, 20000).json()

        assert order["lead_time_days"] == max(i["lead_time_days"] for i in order["items"])

        placed = datetime.fromisoformat(order["order_date"])
        expected = datetime.fromisoformat(order["expected_delivery"])
        assert expected - placed == timedelta(days=order["lead_time_days"])
        assert "T" in order["expected_delivery"]  # same ISO format as /api/orders

    def test_restock_order_uses_server_side_prices(self, client):
        """Test that line costs come from forecast data, not from the request body."""
        forecast = next(f for f in _forecasts(client) if _shortfall(f) > 0)
        # Extra, client-supplied price fields must be ignored.
        response = client.post("/api/restocking/orders", json={
            "budget": 100000,
            "items": [{"sku": forecast["item_sku"], "quantity": 2, "unit_cost": 0.01}],
        })
        assert response.status_code == 201

        item = response.json()["items"][0]
        assert item["unit_cost"] == forecast["unit_cost"]
        assert abs(item["line_cost"] - 2 * forecast["unit_cost"]) < 0.01

    def test_order_ids_increment(self, client):
        """Test that successive orders get distinct, sequential ids and order numbers."""
        first = self._place_order(client, 5000).json()
        second = self._place_order(client, 5000).json()

        assert first["id"] != second["id"]
        assert first["order_number"] == "RST-0001"
        assert second["order_number"] == "RST-0002"

    def test_create_order_unknown_sku(self, client):
        """Test that an unknown SKU is rejected."""
        response = client.post("/api/restocking/orders", json={
            "budget": 1000, "items": [{"sku": "NOPE-999", "quantity": 1}],
        })
        assert response.status_code == 400
        assert "not available" in response.json()["detail"].lower()

    def test_create_order_duplicate_sku(self, client):
        """Test that the same SKU twice in one order is rejected."""
        sku = next(f["item_sku"] for f in _forecasts(client) if _shortfall(f) > 0)
        response = client.post("/api/restocking/orders", json={
            "budget": 100000,
            "items": [{"sku": sku, "quantity": 1}, {"sku": sku, "quantity": 1}],
        })
        assert response.status_code == 400
        assert "duplicate" in response.json()["detail"].lower()

    def test_create_order_over_budget(self, client):
        """Test that an order whose total exceeds the budget is rejected and not stored."""
        forecast = next(f for f in _forecasts(client) if _shortfall(f) > 0)
        response = client.post("/api/restocking/orders", json={
            "budget": 1, "items": [{"sku": forecast["item_sku"], "quantity": 10}],
        })
        assert response.status_code == 400
        assert "exceeds budget" in response.json()["detail"].lower()
        assert client.get("/api/restocking/orders").json() == []

    @pytest.mark.parametrize("payload", [
        {"budget": 1000, "items": []},
        {"budget": 1000, "items": [{"sku": "WDG-001", "quantity": 0}]},
        {"budget": 1000, "items": [{"sku": "WDG-001", "quantity": -3}]},
        {"budget": -1, "items": [{"sku": "WDG-001", "quantity": 1}]},
        {"items": [{"sku": "WDG-001", "quantity": 1}]},
    ])
    def test_create_order_validation_errors(self, client, payload):
        """Test that malformed requests fail Pydantic validation."""
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 422

    # --- Listing orders --------------------------------------------------

    def test_get_restock_orders_empty(self, client):
        """Test that no orders exist before anything is submitted."""
        response = client.get("/api/restocking/orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_restock_orders_newest_first(self, client):
        """Test that submitted orders are listed newest first."""
        first = self._place_order(client, 5000).json()
        second = self._place_order(client, 5000).json()

        response = client.get("/api/restocking/orders")
        assert response.status_code == 200
        numbers = [o["order_number"] for o in response.json()]
        assert numbers == [second["order_number"], first["order_number"]]

    # --- Isolation from existing order data ------------------------------

    def test_restock_orders_do_not_affect_existing_orders(self, client):
        """Test that submitting an order leaves /api/orders and the dashboard untouched."""
        orders_before = client.get("/api/orders").json()
        summary_before = client.get("/api/dashboard/summary").json()
        reports_before = client.get("/api/reports/monthly-trends").json()

        assert self._place_order(client, 10000).status_code == 201

        assert client.get("/api/orders").json() == orders_before
        assert client.get("/api/dashboard/summary").json() == summary_before
        assert client.get("/api/reports/monthly-trends").json() == reports_before

    # --- Forecast data used by restocking --------------------------------

    def test_demand_forecasts_include_restock_fields(self, client):
        """Test that every forecast carries the cost, stock and lead-time fields."""
        for f in _forecasts(client):
            assert isinstance(f["unit_cost"], (int, float)) and f["unit_cost"] > 0
            assert isinstance(f["quantity_on_hand"], int) and f["quantity_on_hand"] >= 0
            assert isinstance(f["lead_time_days"], int) and f["lead_time_days"] > 0
