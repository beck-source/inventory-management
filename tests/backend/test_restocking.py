"""
Tests for restocking API endpoints.
"""
import json
from datetime import datetime

import pytest


# Lead times must stay in step with LEAD_TIME_DAYS in server/main.py
EXPECTED_LEAD_TIMES = {
    "Circuit Boards": 14,
    "Sensors": 10,
    "Actuators": 21,
    "Controllers": 18,
    "Power Supplies": 12,
}

# A budget large enough to cover every shortfall in the current fixtures ($58,575)
FULL_BUDGET = 100000


class TestRestockRecommendationsEndpoint:
    """Test suite for GET /api/restocking/recommendations."""

    def test_get_recommendations_full_budget(self, client):
        """Test that a large budget fully covers every candidate."""
        response = client.get(f"/api/restocking/recommendations?budget={FULL_BUDGET}")
        assert response.status_code == 200

        data = response.json()
        assert data["candidate_count"] > 0
        assert len(data["recommendations"]) == data["candidate_count"]

        # Every line should close its whole shortfall when money is not the constraint
        for item in data["recommendations"]:
            assert item["fully_covered"] is True
            assert item["recommended_quantity"] == item["shortfall"]

        assert abs(data["budget_used"] - data["total_shortfall_cost"]) < 0.01

    def test_recommendations_response_structure(self, client):
        """Test that the recommendations response has the documented structure."""
        response = client.get("/api/restocking/recommendations?budget=20000")
        assert response.status_code == 200

        data = response.json()
        for field in [
            "budget", "budget_used", "budget_remaining", "total_shortfall_cost",
            "candidate_count", "cheapest_unit_cost", "recommendations",
        ]:
            assert field in data

        assert isinstance(data["recommendations"], list)
        assert len(data["recommendations"]) > 0

        first_item = data["recommendations"][0]
        for field in [
            "sku", "name", "category", "warehouse", "unit_cost", "quantity_on_hand",
            "reorder_point", "target_quantity", "shortfall", "recommended_quantity",
            "line_cost", "lead_time_days", "priority", "fully_covered",
        ]:
            assert field in first_item

    def test_recommendations_zero_budget(self, client):
        """Test that a zero budget recommends nothing but still reports metadata."""
        response = client.get("/api/restocking/recommendations?budget=0")
        assert response.status_code == 200

        data = response.json()
        assert data["recommendations"] == []
        assert data["budget_used"] == 0
        assert data["budget_remaining"] == 0

        # Metadata is budget-independent, which is what lets the client size its
        # slider and explain an empty result from a single request
        assert data["candidate_count"] > 0
        assert data["total_shortfall_cost"] > 0
        assert data["cheapest_unit_cost"] > 0

    def test_recommendations_below_cheapest_unit_cost(self, client):
        """Test that a budget under the cheapest unit cost recommends nothing."""
        response = client.get("/api/restocking/recommendations?budget=20000")
        cheapest = response.json()["cheapest_unit_cost"]

        response = client.get(
            f"/api/restocking/recommendations?budget={cheapest - 1}"
        )
        assert response.status_code == 200

        data = response.json()
        assert data["recommendations"] == []
        assert data["candidate_count"] > 0

    def test_recommendations_partial_fill(self, client):
        """Test that a budget covering only part of a shortfall fills it partially."""
        response = client.get("/api/restocking/recommendations?budget=20000")
        cheapest = response.json()["cheapest_unit_cost"]

        # Exactly one unit of the cheapest candidate is affordable
        response = client.get(f"/api/restocking/recommendations?budget={cheapest}")
        assert response.status_code == 200

        data = response.json()
        assert len(data["recommendations"]) == 1

        item = data["recommendations"][0]
        assert item["recommended_quantity"] == 1
        assert item["fully_covered"] is False
        assert abs(item["line_cost"] - cheapest) < 0.01

    def test_recommendations_critical_items_ranked_first(self, client):
        """Test that critical items are ranked ahead of non-critical ones."""
        response = client.get(f"/api/restocking/recommendations?budget={FULL_BUDGET}")
        priorities = [item["priority"] for item in response.json()["recommendations"]]

        assert "critical" in priorities
        assert "low" in priorities
        assert priorities.index("low") > max(
            i for i, p in enumerate(priorities) if p == "critical"
        )

    def test_recommendations_never_exceed_budget(self, client):
        """Test that allocations never exceed the budget at any budget level."""
        for budget in [0, 100, 1000, 20000, 50000, FULL_BUDGET]:
            response = client.get(f"/api/restocking/recommendations?budget={budget}")
            assert response.status_code == 200

            data = response.json()
            assert data["budget_used"] <= budget + 0.01
            assert abs(data["budget_used"] + data["budget_remaining"] - budget) < 0.01

    def test_recommendations_quantity_bounds(self, client):
        """Test that recommended quantities and shortfalls are internally consistent."""
        response = client.get("/api/restocking/recommendations?budget=30000")
        data = response.json()

        for item in data["recommendations"]:
            assert isinstance(item["recommended_quantity"], int)
            assert 1 <= item["recommended_quantity"] <= item["shortfall"]
            assert item["target_quantity"] == int(item["reorder_point"] * 1.5)
            assert item["shortfall"] == item["target_quantity"] - item["quantity_on_hand"]
            assert item["shortfall"] > 0

    def test_recommendations_line_cost_calculation(self, client):
        """Test that line costs and the budget total are calculated correctly."""
        response = client.get("/api/restocking/recommendations?budget=30000")
        data = response.json()

        for item in data["recommendations"]:
            expected = item["recommended_quantity"] * item["unit_cost"]
            assert abs(item["line_cost"] - expected) < 0.01

        total = sum(item["line_cost"] for item in data["recommendations"])
        assert abs(data["budget_used"] - total) < 0.01

    def test_recommendations_lead_time_per_line(self, client):
        """Test that each line carries the lead time for its category."""
        response = client.get(f"/api/restocking/recommendations?budget={FULL_BUDGET}")

        for item in response.json()["recommendations"]:
            assert item["lead_time_days"] == EXPECTED_LEAD_TIMES[item["category"]]

    def test_recommendations_priority_matches_reorder_point(self, client):
        """Test that priority is critical exactly when stock is at or below reorder point."""
        response = client.get(f"/api/restocking/recommendations?budget={FULL_BUDGET}")

        for item in response.json()["recommendations"]:
            is_critical = item["quantity_on_hand"] <= item["reorder_point"]
            assert item["priority"] == ("critical" if is_critical else "low")

    def test_recommendations_deterministic_order(self, client):
        """Test that identical requests return an identical ordering.

        Guards the sku tiebreak: two candidates currently match on shortfall and
        unit cost, so without it their relative order would be arbitrary.
        """
        first = client.get(f"/api/restocking/recommendations?budget={FULL_BUDGET}").json()
        second = client.get(f"/api/restocking/recommendations?budget={FULL_BUDGET}").json()

        assert [i["sku"] for i in first["recommendations"]] == [
            i["sku"] for i in second["recommendations"]
        ]

    def test_recommendations_by_warehouse(self, client):
        """Test filtering recommendations by warehouse."""
        response = client.get(
            f"/api/restocking/recommendations?budget={FULL_BUDGET}&warehouse=Tokyo"
        )
        assert response.status_code == 200

        for item in response.json()["recommendations"]:
            assert item["warehouse"] == "Tokyo"

    def test_recommendations_by_category(self, client):
        """Test filtering recommendations by category, case-insensitively."""
        response = client.get(
            f"/api/restocking/recommendations?budget={FULL_BUDGET}&category=actuators"
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data["recommendations"]) > 0
        for item in data["recommendations"]:
            assert item["category"].lower() == "actuators"

    def test_recommendations_missing_budget(self, client):
        """Test that omitting the budget parameter is a validation error."""
        response = client.get("/api/restocking/recommendations")
        assert response.status_code == 422

    def test_recommendations_negative_budget(self, client):
        """Test that a negative budget is a validation error."""
        response = client.get("/api/restocking/recommendations?budget=-100")
        assert response.status_code == 422

    def test_recommendations_match_inventory_endpoint(self, client):
        """Test that candidates match an independent calculation over /api/inventory."""
        inventory = client.get("/api/inventory").json()

        expected_skus = {
            item["sku"] for item in inventory
            if int(item["reorder_point"] * 1.5) - item["quantity_on_hand"] > 0
        }

        response = client.get(f"/api/restocking/recommendations?budget={FULL_BUDGET}")
        actual_skus = {item["sku"] for item in response.json()["recommendations"]}

        assert actual_skus == expected_skus


class TestRestockOrdersEndpoints:
    """Test suite for GET and POST /api/restocking/orders."""

    def _first_recommendation(self, client):
        """Get the top-ranked recommendation at a budget that covers everything."""
        response = client.get(f"/api/restocking/recommendations?budget={FULL_BUDGET}")
        return response.json()["recommendations"][0]

    def test_get_restock_orders_returns_list(self, client):
        """Test getting submitted restock orders."""
        response = client.get("/api/restocking/orders")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_restock_order(self, client, restock_store):
        """Test submitting a restock order."""
        item = self._first_recommendation(client)

        response = client.post("/api/restocking/orders", json={
            "budget": FULL_BUDGET,
            "items": [{"sku": item["sku"], "quantity": item["shortfall"]}],
        })
        assert response.status_code == 201

        order = response.json()
        assert order["order_number"].startswith("RST-")
        assert order["status"] == "Submitted"
        assert "id" in order
        assert abs(order["total_value"] - item["shortfall"] * item["unit_cost"]) < 0.01

        assert len(order["items"]) == 1
        line = order["items"][0]
        assert line["sku"] == item["sku"]
        assert line["name"] == item["name"]
        assert line["category"] == item["category"]
        assert abs(line["unit_cost"] - item["unit_cost"]) < 0.01

    def test_create_restock_order_lead_time_and_delivery(self, client, restock_store):
        """Test that expected delivery is the submission date plus the lead time."""
        item = self._first_recommendation(client)

        response = client.post("/api/restocking/orders", json={
            "budget": FULL_BUDGET,
            "items": [{"sku": item["sku"], "quantity": 1}],
        })
        assert response.status_code == 201

        order = response.json()
        assert order["lead_time_days"] == EXPECTED_LEAD_TIMES[item["category"]]

        submitted = datetime.fromisoformat(order["submitted_at"])
        expected = datetime.fromisoformat(order["expected_delivery"])
        assert (expected - submitted).days == order["lead_time_days"]

    def test_create_restock_order_lead_time_is_max_across_categories(self, client, restock_store):
        """Test that an order's lead time is the longest across its line items."""
        response = client.get(f"/api/restocking/recommendations?budget={FULL_BUDGET}")
        recommendations = response.json()["recommendations"]

        by_category = {}
        for item in recommendations:
            by_category.setdefault(item["category"], item)
        assert len(by_category) > 1, "fixture should span multiple categories"

        picked = list(by_category.values())
        response = client.post("/api/restocking/orders", json={
            "budget": FULL_BUDGET,
            "items": [{"sku": item["sku"], "quantity": 1} for item in picked],
        })
        assert response.status_code == 201

        assert response.json()["lead_time_days"] == max(
            EXPECTED_LEAD_TIMES[item["category"]] for item in picked
        )

    def test_create_then_get_restock_orders(self, client, restock_store):
        """Test that a submitted order appears in the orders list."""
        item = self._first_recommendation(client)

        created = client.post("/api/restocking/orders", json={
            "budget": FULL_BUDGET,
            "items": [{"sku": item["sku"], "quantity": 1}],
        }).json()

        response = client.get("/api/restocking/orders")
        assert response.status_code == 200

        order_numbers = [o["order_number"] for o in response.json()]
        assert created["order_number"] in order_numbers

    def test_create_restock_order_unknown_sku(self, client, restock_store):
        """Test that an unknown SKU is rejected."""
        response = client.post("/api/restocking/orders", json={
            "budget": 1000,
            "items": [{"sku": "NOPE-999", "quantity": 1}],
        })
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_create_restock_order_duplicate_sku(self, client, restock_store):
        """Test that the same SKU twice in one order is rejected."""
        item = self._first_recommendation(client)

        response = client.post("/api/restocking/orders", json={
            "budget": FULL_BUDGET,
            "items": [
                {"sku": item["sku"], "quantity": 1},
                {"sku": item["sku"], "quantity": 2},
            ],
        })
        assert response.status_code == 400
        assert "duplicate" in response.json()["detail"].lower()

    def test_create_restock_order_exceeds_budget(self, client, restock_store):
        """Test that an order costing more than its budget is rejected."""
        item = self._first_recommendation(client)

        response = client.post("/api/restocking/orders", json={
            "budget": item["unit_cost"],
            "items": [{"sku": item["sku"], "quantity": item["shortfall"] + 10}],
        })
        assert response.status_code == 400
        assert "budget" in response.json()["detail"].lower()

    def test_create_restock_order_zero_quantity(self, client, restock_store):
        """Test that a zero quantity is a validation error."""
        item = self._first_recommendation(client)

        response = client.post("/api/restocking/orders", json={
            "budget": 1000,
            "items": [{"sku": item["sku"], "quantity": 0}],
        })
        assert response.status_code == 422

    def test_create_restock_order_empty_items(self, client, restock_store):
        """Test that an order with no line items is a validation error."""
        response = client.post("/api/restocking/orders", json={
            "budget": 1000,
            "items": [],
        })
        assert response.status_code == 422

    def test_create_restock_order_ignores_client_prices(self, client, restock_store):
        """Test that line prices come from inventory, not from the request."""
        item = self._first_recommendation(client)

        response = client.post("/api/restocking/orders", json={
            "budget": FULL_BUDGET,
            "items": [{
                "sku": item["sku"],
                "quantity": 1,
                "unit_cost": 0.01,     # must be ignored
                "line_cost": 0.01,     # must be ignored
            }],
        })
        assert response.status_code == 201

        line = response.json()["items"][0]
        assert abs(line["unit_cost"] - item["unit_cost"]) < 0.01
        assert abs(line["line_cost"] - item["unit_cost"]) < 0.01

    def test_create_restock_order_persists_to_disk(self, client, restock_store):
        """Test that a submitted order is written to the data file."""
        item = self._first_recommendation(client)

        created = client.post("/api/restocking/orders", json={
            "budget": FULL_BUDGET,
            "items": [{"sku": item["sku"], "quantity": 1}],
        }).json()

        persisted_file = restock_store / "restock_orders.json"
        assert persisted_file.exists()

        persisted = json.loads(persisted_file.read_text())
        assert isinstance(persisted, list)
        assert persisted[-1]["order_number"] == created["order_number"]

        # The atomic write must not leave its temp file behind
        assert not (restock_store / "restock_orders.json.tmp").exists()

    def test_restock_order_ids_increment(self, client, restock_store):
        """Test that consecutive orders get distinct ids and order numbers."""
        item = self._first_recommendation(client)
        payload = {
            "budget": FULL_BUDGET,
            "items": [{"sku": item["sku"], "quantity": 1}],
        }

        first = client.post("/api/restocking/orders", json=payload).json()
        second = client.post("/api/restocking/orders", json=payload).json()

        assert first["id"] != second["id"]
        assert first["order_number"] != second["order_number"]
        assert int(second["id"]) == int(first["id"]) + 1

    def test_create_restock_order_does_not_affect_customer_orders(self, client, restock_store):
        """Test that restock orders stay out of the customer orders collection."""
        before = len(client.get("/api/orders").json())

        item = self._first_recommendation(client)
        client.post("/api/restocking/orders", json={
            "budget": FULL_BUDGET,
            "items": [{"sku": item["sku"], "quantity": 1}],
        })

        customer_orders = client.get("/api/orders").json()
        assert len(customer_orders) == before
        assert not any(o["status"] == "Submitted" for o in customer_orders)
