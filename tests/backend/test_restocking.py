"""Tests for restocking API endpoints."""
import pytest

from mock_data import restock_orders


@pytest.fixture(autouse=True)
def isolate_restock_orders():
    """Restore submitted orders after each test.

    `restock_orders` is module-level state imported once per process, so an order
    created by one test would otherwise stay visible to every later test. Slice
    assignment restores the contents in place - rebinding the name here would
    leave main.py still pointing at the mutated list.
    """
    saved = list(restock_orders)
    yield
    restock_orders[:] = saved


class TestRestockRecommendations:
    """Test suite for restocking recommendation endpoints."""

    def test_get_recommendations_returns_plan(self, client):
        """Test that the recommendations endpoint returns a plan structure."""
        response = client.get("/api/restock/recommendations?budget=5000")
        assert response.status_code == 200

        data = response.json()
        for field in [
            "budget", "total_cost", "remaining_budget", "item_count",
            "total_units", "lead_time_days", "full_coverage_cost",
            "recommendations", "unpriced_skus"
        ]:
            assert field in data, f"Missing field: {field}"

        assert isinstance(data["recommendations"], list)

    def test_recommendations_stay_within_budget(self, client):
        """Test that recommended spend never exceeds the requested budget."""
        for budget in [0, 500, 1200, 5000, 12000, 99999]:
            data = client.get(f"/api/restock/recommendations?budget={budget}").json()

            line_sum = sum(r["line_total"] for r in data["recommendations"])
            assert abs(data["total_cost"] - line_sum) < 0.01
            assert data["total_cost"] <= budget + 0.01, \
                f"Budget {budget} exceeded by {data['total_cost']}"
            assert abs(data["remaining_budget"] - (budget - data["total_cost"])) < 0.01

    def test_zero_budget_recommends_nothing(self, client):
        """Test that a zero budget produces an empty recommendation list."""
        data = client.get("/api/restock/recommendations?budget=0").json()

        assert data["recommendations"] == []
        assert data["item_count"] == 0
        assert data["total_units"] == 0
        assert data["total_cost"] == 0
        assert data["lead_time_days"] == 0

    def test_negative_budget_is_rejected(self, client):
        """Test that a negative budget returns 400."""
        response = client.get("/api/restock/recommendations?budget=-1")
        assert response.status_code == 400

    def test_recommendations_ordered_by_demand_gap(self, client):
        """Test that recommendations are ranked by demand gap, largest first."""
        data = client.get("/api/restock/recommendations?budget=12000").json()
        gaps = [r["demand_gap"] for r in data["recommendations"]]

        assert gaps == sorted(gaps, reverse=True)

    def test_recommendations_only_cover_growing_demand(self, client):
        """Test that only items with a positive demand gap are recommended."""
        data = client.get("/api/restock/recommendations?budget=99999").json()

        for rec in data["recommendations"]:
            assert rec["demand_gap"] > 0
            assert rec["forecasted_demand"] > rec["current_demand"]
            assert 0 < rec["recommended_quantity"] <= rec["demand_gap"]

    def test_partial_line_is_the_last_line(self, client):
        """Test that a budget-truncated line is flagged and ends the list."""
        data = client.get("/api/restock/recommendations?budget=5000").json()
        recommendations = data["recommendations"]

        partial_indexes = [i for i, r in enumerate(recommendations) if r["is_partial"]]
        assert len(partial_indexes) <= 1

        if partial_indexes:
            assert partial_indexes[0] == len(recommendations) - 1
            partial = recommendations[-1]
            assert partial["recommended_quantity"] < partial["demand_gap"]

    def test_generous_budget_closes_every_gap(self, client):
        """Test that a budget above full coverage cost fills every shortfall."""
        data = client.get("/api/restock/recommendations?budget=999999").json()

        assert abs(data["total_cost"] - data["full_coverage_cost"]) < 0.01
        for rec in data["recommendations"]:
            assert rec["is_partial"] is False
            assert rec["recommended_quantity"] == rec["demand_gap"]

    def test_line_totals_match_unit_cost(self, client):
        """Test that each line total equals quantity times unit cost."""
        data = client.get("/api/restock/recommendations?budget=12000").json()

        for rec in data["recommendations"]:
            expected = rec["recommended_quantity"] * rec["unit_cost"]
            assert abs(rec["line_total"] - expected) < 0.01

    def test_recommendations_priced_from_inventory(self, client):
        """Test that recommended items are priced from the inventory catalog."""
        inventory = {item["sku"]: item for item in client.get("/api/inventory").json()}
        data = client.get("/api/restock/recommendations?budget=99999").json()

        for rec in data["recommendations"]:
            item = inventory.get(rec["item_sku"])
            assert item is not None, f"{rec['item_sku']} is not in inventory"
            assert abs(rec["unit_cost"] - item["unit_cost"]) < 0.01
            assert rec["category"] == item["category"]
            assert rec["warehouse"] == item["warehouse"]

    def test_unpriced_forecast_skus_are_reported(self, client):
        """Test that forecast SKUs missing from inventory are surfaced, not dropped."""
        inventory_skus = {item["sku"] for item in client.get("/api/inventory").json()}
        forecasts = client.get("/api/demand").json()
        data = client.get("/api/restock/recommendations?budget=99999").json()

        recommended_skus = {r["item_sku"] for r in data["recommendations"]}
        reported = set(data["unpriced_skus"])

        for forecast in forecasts:
            has_gap = forecast["forecasted_demand"] > forecast["current_demand"]
            if has_gap and forecast["item_sku"] not in inventory_skus:
                assert forecast["item_sku"] in reported, \
                    f"{forecast['item_sku']} was dropped without explanation"

        assert reported.isdisjoint(recommended_skus)

    def test_lead_time_is_the_slowest_line(self, client):
        """Test that plan lead time equals the longest line lead time."""
        data = client.get("/api/restock/recommendations?budget=12000").json()
        line_leads = [r["lead_time_days"] for r in data["recommendations"]]

        assert data["lead_time_days"] == max(line_leads)
        for lead in line_leads:
            assert lead > 0


class TestRestockOrders:
    """Test suite for submitted restocking orders."""

    def submit_plan(self, client, budget=5000):
        """Submit the recommended plan for a budget and return the response."""
        plan = client.get(f"/api/restock/recommendations?budget={budget}").json()
        payload = {
            "budget": budget,
            "lines": [
                {"item_sku": r["item_sku"], "quantity": r["recommended_quantity"]}
                for r in plan["recommendations"]
            ]
        }
        return client.post("/api/restock-orders", json=payload)

    def test_get_restock_orders_returns_list(self, client):
        """Test that the restocking orders endpoint returns a list."""
        response = client.get("/api/restock-orders")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_submit_order_returns_201(self, client):
        """Test that submitting a restocking order returns 201 with an order."""
        response = self.submit_plan(client)
        assert response.status_code == 201

        order = response.json()
        assert order["status"] == "Submitted"
        assert order["order_number"].startswith("RO-")
        assert order["item_count"] == len(order["lines"])
        assert order["total_units"] == sum(line["quantity"] for line in order["lines"])

    def test_submitted_order_appears_in_list(self, client):
        """Test that a submitted order is retrievable afterwards."""
        submitted = self.submit_plan(client).json()

        orders = client.get("/api/restock-orders").json()
        assert submitted["order_number"] in [o["order_number"] for o in orders]

    def test_orders_are_returned_newest_first(self, client):
        """Test that the most recently submitted order is listed first."""
        self.submit_plan(client, budget=1200)
        second = self.submit_plan(client, budget=5000).json()

        orders = client.get("/api/restock-orders").json()
        assert orders[0]["order_number"] == second["order_number"]

    def test_order_total_matches_lines(self, client):
        """Test that the order total equals the sum of its line totals."""
        order = self.submit_plan(client).json()

        line_sum = sum(line["line_total"] for line in order["lines"])
        assert abs(order["total_value"] - line_sum) < 0.01
        assert order["total_value"] <= order["budget"] + 0.01

    def test_order_is_repriced_from_inventory(self, client):
        """Test that client-supplied prices cannot override inventory pricing."""
        inventory = {item["sku"]: item for item in client.get("/api/inventory").json()}
        response = client.post("/api/restock-orders", json={
            "budget": 100000,
            "lines": [{"item_sku": "PCB-002", "quantity": 10, "unit_cost": 0.01}]
        })
        assert response.status_code == 201

        line = response.json()["lines"][0]
        assert abs(line["unit_cost"] - inventory["PCB-002"]["unit_cost"]) < 0.01
        assert abs(line["line_total"] - 10 * inventory["PCB-002"]["unit_cost"]) < 0.01

    def test_expected_delivery_follows_lead_time(self, client):
        """Test that expected delivery is the creation date plus the lead time."""
        from datetime import datetime

        order = self.submit_plan(client).json()
        created = datetime.fromisoformat(order["created_date"])
        expected = datetime.fromisoformat(order["expected_delivery"])

        assert (expected - created).days == order["lead_time_days"]
        assert order["lead_time_days"] == max(line["lead_time_days"] for line in order["lines"])

    def test_order_over_budget_is_rejected(self, client):
        """Test that an order costing more than its budget returns 400."""
        response = client.post("/api/restock-orders", json={
            "budget": 10,
            "lines": [{"item_sku": "PCB-002", "quantity": 150}]
        })
        assert response.status_code == 400

    def test_order_with_unknown_sku_is_rejected(self, client):
        """Test that an unknown SKU returns 404."""
        response = client.post("/api/restock-orders", json={
            "budget": 5000,
            "lines": [{"item_sku": "DOES-NOT-EXIST", "quantity": 1}]
        })
        assert response.status_code == 404

    def test_order_without_lines_is_rejected(self, client):
        """Test that an order with no lines returns 400."""
        response = client.post("/api/restock-orders", json={"budget": 5000, "lines": []})
        assert response.status_code == 400

    def test_order_with_non_positive_quantity_is_rejected(self, client):
        """Test that a zero or negative quantity returns 400."""
        for quantity in [0, -5]:
            response = client.post("/api/restock-orders", json={
                "budget": 5000,
                "lines": [{"item_sku": "PCB-002", "quantity": quantity}]
            })
            assert response.status_code == 400, f"Quantity {quantity} should be rejected"
