"""
Tests for restocking API endpoints.
"""
from datetime import datetime

import pytest

from mock_data import CATEGORY_LEAD_TIME_DAYS, DEFAULT_LEAD_TIME_DAYS, restock_orders


@pytest.fixture(autouse=True)
def clear_restock_orders():
    """Submitted orders live in a module global, so isolate every test from the last."""
    restock_orders.clear()
    yield
    restock_orders.clear()


class TestRestockingRecommendations:
    """Test suite for the restocking recommendation endpoint."""

    def test_get_recommendations_default_budget(self, client):
        """Test that a zero budget still reports the candidate pool."""
        response = client.get("/api/restocking/recommendations")
        assert response.status_code == 200

        data = response.json()
        assert data["items"] == []
        assert data["total_cost"] == 0
        assert data["candidate_count"] > 0
        assert data["max_useful_cost"] > 0
        assert data["min_unit_cost"] > 0

    def test_recommendation_structure(self, client):
        """Test that recommendation items have proper structure."""
        response = client.get("/api/restocking/recommendations?budget=130000")
        assert response.status_code == 200

        data = response.json()
        assert len(data["items"]) > 0

        for item in data["items"]:
            assert "sku" in item
            assert "name" in item
            assert "category" in item
            assert "warehouse" in item
            assert isinstance(item["unit_cost"], (int, float))
            assert isinstance(item["quantity_on_hand"], int)
            assert isinstance(item["reorder_point"], int)
            assert isinstance(item["below_reorder_point"], bool)
            assert isinstance(item["shortfall"], int)
            assert item["shortfall"] > 0
            assert item["shortfall_source"] in ["forecast", "reorder_point"]
            assert isinstance(item["recommended_quantity"], int)
            assert item["recommended_quantity"] >= 1
            assert isinstance(item["fully_covered"], bool)
            assert isinstance(item["lead_time_days"], int)

    def test_low_stock_items_ranked_first(self, client):
        """Test that items at or below reorder point outrank everything else."""
        response = client.get("/api/restocking/recommendations?budget=130000")
        items = response.json()["items"]

        flags = [item["below_reorder_point"] for item in items]
        # Once a non-low-stock item appears, no low-stock item may follow it
        assert flags == sorted(flags, reverse=True)

    def test_ranking_breaks_shortfall_ties_by_unit_cost(self, client):
        """Test that equal shortfalls are ordered by unit cost, not dict order."""
        items = client.get("/api/restocking/recommendations?budget=130000").json()["items"]

        for earlier, later in zip(items, items[1:]):
            if earlier["below_reorder_point"] != later["below_reorder_point"]:
                continue
            if earlier["shortfall"] == later["shortfall"]:
                assert earlier["unit_cost"] <= later["unit_cost"]

    def test_greedy_fill_respects_budget(self, client):
        """Test that the allocated total never exceeds the requested budget."""
        for budget in [500, 5000, 65000, 130000]:
            data = client.get(f"/api/restocking/recommendations?budget={budget}").json()

            assert data["total_cost"] <= budget
            assert abs(data["remaining_budget"] - (budget - data["total_cost"])) < 0.01

            calculated = sum(item["line_cost"] for item in data["items"])
            assert abs(data["total_cost"] - calculated) < 0.01

    def test_line_cost_matches_quantity_times_unit_cost(self, client):
        """Test that each line is priced from its own quantity and unit cost."""
        items = client.get("/api/restocking/recommendations?budget=65000").json()["items"]

        for item in items:
            expected = item["recommended_quantity"] * item["unit_cost"]
            assert abs(item["line_cost"] - expected) < 0.01

    def test_partial_lines_are_flagged(self, client):
        """Test that a line the budget could not fully cover reports fully_covered False."""
        items = client.get("/api/restocking/recommendations?budget=65000").json()["items"]

        for item in items:
            assert item["fully_covered"] == (item["recommended_quantity"] == item["shortfall"])

        # A mid-range budget must run out somewhere, otherwise this test proves nothing
        assert any(not item["fully_covered"] for item in items)

    def test_full_coverage_at_max_useful_cost(self, client):
        """Test that a budget of exactly max_useful_cost covers every candidate."""
        bounds = client.get("/api/restocking/recommendations?budget=0").json()
        max_useful = bounds["max_useful_cost"]

        data = client.get(f"/api/restocking/recommendations?budget={max_useful}").json()

        assert len(data["items"]) == bounds["candidate_count"]
        assert all(item["fully_covered"] for item in data["items"])
        assert abs(data["total_cost"] - max_useful) < 0.01

    def test_budget_below_cheapest_item(self, client):
        """Test that a budget under the cheapest unit buys nothing but still reports bounds."""
        bounds = client.get("/api/restocking/recommendations?budget=0").json()
        too_small = bounds["min_unit_cost"] - 1

        data = client.get(f"/api/restocking/recommendations?budget={too_small}").json()

        assert data["items"] == []
        assert data["total_cost"] == 0
        assert data["candidate_count"] == bounds["candidate_count"]

    def test_get_recommendations_by_warehouse(self, client):
        """Test filtering recommendations by warehouse."""
        response = client.get("/api/restocking/recommendations?budget=130000&warehouse=Tokyo")
        assert response.status_code == 200

        data = response.json()
        assert len(data["items"]) > 0
        for item in data["items"]:
            assert item["warehouse"] == "Tokyo"

    def test_get_recommendations_by_lowercase_category(self, client):
        """Test that FilterBar's lowercase category values match."""
        response = client.get("/api/restocking/recommendations?budget=130000&category=sensors")
        assert response.status_code == 200

        data = response.json()
        assert len(data["items"]) > 0
        for item in data["items"]:
            assert item["category"].lower() == "sensors"

    def test_get_recommendations_multiple_filters(self, client):
        """Test filtering recommendations by warehouse and category together."""
        response = client.get(
            "/api/restocking/recommendations?budget=130000&warehouse=London&category=actuators"
        )
        assert response.status_code == 200

        data = response.json()
        for item in data["items"]:
            assert item["warehouse"] == "London"
            assert item["category"].lower() == "actuators"

    def test_filters_leaving_no_candidates(self, client):
        """Test that an empty candidate pool reports zeroed bounds rather than erroring."""
        response = client.get(
            "/api/restocking/recommendations?budget=130000"
            "&warehouse=San Francisco&category=circuit boards"
        )
        assert response.status_code == 200

        data = response.json()
        assert data["items"] == []
        assert data["candidate_count"] == 0
        assert data["max_useful_cost"] == 0
        assert data["min_unit_cost"] is None

    def test_well_stocked_items_are_excluded(self, client):
        """Test that items already at or above target never appear."""
        inventory = {item["sku"]: item for item in client.get("/api/inventory").json()}
        items = client.get("/api/restocking/recommendations?budget=130000").json()["items"]

        recommended = {item["sku"] for item in items}
        for sku, item in inventory.items():
            if item["quantity_on_hand"] >= item["reorder_point"] * 2:
                # Only a forecast could pull a well-stocked item back in
                if sku in recommended:
                    assert next(i for i in items if i["sku"] == sku)["shortfall_source"] == "forecast"

    def test_forecast_sourced_items_carry_a_trend(self, client):
        """Test that a forecast-driven shortfall also surfaces the forecast trend."""
        items = client.get("/api/restocking/recommendations?budget=130000").json()["items"]

        for item in items:
            if item["shortfall_source"] == "forecast":
                assert item["forecast_trend"] in ["increasing", "stable", "decreasing"]
                assert isinstance(item["forecasted_demand"], int)

    def test_negative_budget_rejected(self, client):
        """Test that a negative budget is rejected."""
        response = client.get("/api/restocking/recommendations?budget=-1")
        assert response.status_code == 422


class TestLeadTimes:
    """Test suite for lead times derived from order history."""

    def test_lead_times_derived_from_order_history(self, client):
        """Test that lead times match the gaps actually present in the orders data."""
        orders = client.get("/api/orders").json()

        gaps = {}
        for order in orders:
            ordered = datetime.fromisoformat(order["order_date"])
            expected = datetime.fromisoformat(order["expected_delivery"])
            gaps.setdefault(order["category"], []).append((expected - ordered).days)

        for category, category_gaps in gaps.items():
            mean_days = int(sum(category_gaps) / len(category_gaps) + 0.5)
            assert CATEGORY_LEAD_TIME_DAYS[category] == mean_days

    def test_unknown_category_falls_back_to_default(self, client):
        """Test that every recommendation carries a plausible lead time."""
        items = client.get("/api/restocking/recommendations?budget=130000").json()["items"]

        assert DEFAULT_LEAD_TIME_DAYS > 0
        for item in items:
            assert item["lead_time_days"] == CATEGORY_LEAD_TIME_DAYS.get(
                item["category"], DEFAULT_LEAD_TIME_DAYS
            )


class TestRestockingOrders:
    """Test suite for submitting and listing restocking orders."""

    def test_create_restock_order(self, client):
        """Test submitting a restocking order."""
        response = client.post(
            "/api/restocking/orders",
            json={"budget": 3000, "items": [{"sku": "TMP-201", "quantity": 25}]},
        )
        assert response.status_code == 201

        order = response.json()
        assert order["order_number"].startswith("RST-")
        assert order["status"] == "Submitted"
        assert order["total_cost"] == 2237.5
        assert order["lead_time_days"] > 0
        assert "T" in order["created_date"]
        assert "T" in order["expected_delivery"]
        assert len(order["items"]) == 1

    def test_create_order_prices_from_inventory(self, client):
        """Test that a client-supplied cost is ignored in favour of the catalogue."""
        inventory = client.get("/api/inventory").json()
        real_cost = next(item["unit_cost"] for item in inventory if item["sku"] == "TMP-201")

        response = client.post(
            "/api/restocking/orders",
            json={
                "budget": 3000,
                "items": [{"sku": "TMP-201", "quantity": 25, "unit_cost": 0.01}],
            },
        )
        assert response.status_code == 201

        line = response.json()["items"][0]
        assert line["unit_cost"] == real_cost
        assert line["line_cost"] == round(25 * real_cost, 2)

    def test_order_lead_time_is_max_across_lines(self, client):
        """Test that the order lead time is set by its slowest line."""
        response = client.post(
            "/api/restocking/orders",
            json={
                "budget": 200000,
                "items": [
                    {"sku": "TMP-201", "quantity": 10},
                    {"sku": "PCB-001", "quantity": 10},
                ],
            },
        )
        assert response.status_code == 201

        order = response.json()
        assert order["lead_time_days"] == max(line["lead_time_days"] for line in order["items"])
        assert order["lead_time_days"] == CATEGORY_LEAD_TIME_DAYS["Circuit Boards"]

    def test_expected_delivery_matches_lead_time(self, client):
        """Test that expected delivery is the creation date plus the lead time."""
        response = client.post(
            "/api/restocking/orders",
            json={"budget": 3000, "items": [{"sku": "TMP-201", "quantity": 25}]},
        )
        order = response.json()

        created = datetime.fromisoformat(order["created_date"])
        expected = datetime.fromisoformat(order["expected_delivery"])
        assert (expected - created).days == order["lead_time_days"]

    def test_create_order_with_unknown_sku(self, client):
        """Test submitting an order for a SKU that doesn't exist."""
        response = client.post(
            "/api/restocking/orders",
            json={"budget": 1000, "items": [{"sku": "NOPE-999", "quantity": 1}]},
        )
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_create_order_with_no_items(self, client):
        """Test that an order must contain at least one line."""
        response = client.post("/api/restocking/orders", json={"budget": 1000, "items": []})
        assert response.status_code == 422

    def test_create_order_with_zero_quantity(self, client):
        """Test that a line quantity must be positive."""
        response = client.post(
            "/api/restocking/orders",
            json={"budget": 1000, "items": [{"sku": "TMP-201", "quantity": 0}]},
        )
        assert response.status_code == 422

    def test_create_order_exceeding_budget(self, client):
        """Test that an order costing more than its budget is rejected."""
        response = client.post(
            "/api/restocking/orders",
            json={"budget": 100, "items": [{"sku": "TMP-201", "quantity": 25}]},
        )
        assert response.status_code == 400

        data = response.json()
        assert "budget" in data["detail"].lower()

    def test_get_restock_orders_empty_initially(self, client):
        """Test that no submitted orders exist before any are placed."""
        response = client.get("/api/restocking/orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_submitted_order_appears_in_list(self, client):
        """Test that a submitted order is returned by the list endpoint."""
        created = client.post(
            "/api/restocking/orders",
            json={"budget": 3000, "items": [{"sku": "TMP-201", "quantity": 25}]},
        ).json()

        response = client.get("/api/restocking/orders")
        assert response.status_code == 200

        orders = response.json()
        assert len(orders) == 1
        assert orders[0]["order_number"] == created["order_number"]

    def test_get_restock_orders_by_warehouse(self, client):
        """Test filtering submitted orders by warehouse at line level."""
        # TMP-201 is a London item
        client.post(
            "/api/restocking/orders",
            json={"budget": 3000, "items": [{"sku": "TMP-201", "quantity": 25}]},
        )

        assert client.get("/api/restocking/orders?warehouse=London").json() != []
        assert client.get("/api/restocking/orders?warehouse=Tokyo").json() == []

    def test_get_restock_orders_ignores_status_and_month(self, client):
        """Test that status and month filters never hide a submitted order."""
        client.post(
            "/api/restocking/orders",
            json={"budget": 3000, "items": [{"sku": "TMP-201", "quantity": 25}]},
        )

        response = client.get("/api/restocking/orders?status=delivered&month=2025-01")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_order_numbers_are_sequential(self, client):
        """Test that successive orders get distinct, increasing numbers."""
        numbers = []
        for _ in range(3):
            response = client.post(
                "/api/restocking/orders",
                json={"budget": 3000, "items": [{"sku": "TMP-201", "quantity": 1}]},
            )
            numbers.append(response.json()["order_number"])

        assert len(set(numbers)) == 3
        assert numbers == sorted(numbers)
