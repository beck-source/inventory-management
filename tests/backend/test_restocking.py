"""
Tests for restocking API endpoints.

Covers GET /api/restocking/recommendations (budget-aware recommendations derived
from demand forecast gaps priced against inventory unit_cost) and
POST /api/restocking/order (submits the recommended set as a new in-memory order).
"""
import re
from datetime import datetime


def _expected_candidates(client):
    """Build the expected priced restock candidates from the live demand +
    inventory data, mirroring the backend join logic (positive gaps only,
    inventory match required)."""
    demand = client.get("/api/demand").json()
    inventory = client.get("/api/inventory").json()
    inv_by_sku = {i["sku"]: i for i in inventory}

    candidates = []
    skipped = []
    for f in demand:
        gap = f["forecasted_demand"] - f["current_demand"]
        if gap <= 0:
            continue
        inv = inv_by_sku.get(f["item_sku"])
        if inv is None:
            skipped.append(f["item_sku"])
            continue
        candidates.append({
            "sku": f["item_sku"],
            "quantity": gap,
            "unit_cost": inv["unit_cost"],
            "line_cost": round(gap * inv["unit_cost"], 2),
            "trend": f["trend"],
        })
    return candidates, skipped


class TestRestockingRecommendations:
    """Test suite for GET /api/restocking/recommendations."""

    def test_recommendations_response_structure(self, client):
        """Recommendations return the documented shape."""
        response = client.get("/api/restocking/recommendations?budget=10000")
        assert response.status_code == 200

        data = response.json()
        for key in ("budget", "items", "total_cost", "item_count",
                    "max_budget", "skipped_no_inventory"):
            assert key in data
        assert isinstance(data["items"], list)
        assert isinstance(data["skipped_no_inventory"], list)
        assert data["item_count"] == len(data["items"])

    def test_line_item_structure_and_cost(self, client):
        """Each recommended line item is well-formed and line_cost is correct."""
        data = client.get("/api/restocking/recommendations?budget=1000000000").json()
        assert len(data["items"]) > 0

        for item in data["items"]:
            for key in ("sku", "name", "quantity", "unit_cost", "line_cost", "trend"):
                assert key in item
            assert isinstance(item["quantity"], int)
            assert item["quantity"] > 0
            assert isinstance(item["unit_cost"], (int, float))
            assert abs(item["line_cost"] - round(item["quantity"] * item["unit_cost"], 2)) < 0.01

    def test_total_cost_respects_budget(self, client):
        """Total cost never exceeds the requested budget."""
        for budget in (0, 2000, 5000, 30000):
            data = client.get(f"/api/restocking/recommendations?budget={budget}").json()
            assert data["total_cost"] <= budget + 0.01
            assert abs(data["total_cost"] - sum(i["line_cost"] for i in data["items"])) < 0.01

    def test_total_cost_capped_at_max_budget(self, client):
        """A very large budget selects everything and caps total at max_budget."""
        data = client.get("/api/restocking/recommendations?budget=1000000000").json()
        assert data["max_budget"] > 0
        assert abs(data["total_cost"] - data["max_budget"]) < 0.01

    def test_max_budget_matches_all_positive_gaps(self, client):
        """max_budget equals the cost to cover every positive, in-stock gap."""
        candidates, skipped = _expected_candidates(client)
        expected_max = round(sum(c["line_cost"] for c in candidates), 2)

        data = client.get("/api/restocking/recommendations?budget=0").json()
        assert abs(data["max_budget"] - expected_max) < 0.01
        # budget 0 yields no items but still reports max_budget
        assert data["item_count"] == 0
        assert data["max_budget"] > 0
        # skipped list matches expectation (empty when all demand SKUs are in stock)
        assert sorted(data["skipped_no_inventory"]) == sorted(skipped)

    def test_only_positive_gap_items_recommended(self, client):
        """Stable-at-zero and decreasing-demand SKUs never appear."""
        candidates, _ = _expected_candidates(client)
        eligible_skus = {c["sku"] for c in candidates}

        data = client.get("/api/restocking/recommendations?budget=1000000000").json()
        returned_skus = {i["sku"] for i in data["items"]}
        assert returned_skus == eligible_skus

    def test_increasing_trend_prioritized(self, client):
        """In the selected list, no 'increasing' item appears after a non-increasing one."""
        data = client.get("/api/restocking/recommendations?budget=1000000000").json()
        trends = [i["trend"] for i in data["items"]]
        seen_non_increasing = False
        for trend in trends:
            if trend != "increasing":
                seen_non_increasing = True
            elif seen_non_increasing:
                assert False, "increasing item ranked after a non-increasing item"

    def test_recommendations_deterministic(self, client):
        """The same budget always yields the same set of SKUs in the same order."""
        a = client.get("/api/restocking/recommendations?budget=8000").json()
        b = client.get("/api/restocking/recommendations?budget=8000").json()
        assert [i["sku"] for i in a["items"]] == [i["sku"] for i in b["items"]]


class TestRestockingOrder:
    """Test suite for POST /api/restocking/order."""

    def _recommended_items(self, client, budget=8000):
        return client.get(f"/api/restocking/recommendations?budget={budget}").json()["items"]

    def test_submit_order_success(self, client):
        """Submitting a recommended set creates a valid Submitted order."""
        items = self._recommended_items(client)
        assert len(items) > 0

        response = client.post("/api/restocking/order", json={"items": items})
        assert response.status_code == 201

        order = response.json()
        assert order["status"] == "Submitted"
        assert order["customer"] == "Internal Restock"
        assert re.match(r"^ORD-2025-\d{4}$", order["order_number"])

        # total_value equals the sum of submitted line costs
        expected_total = round(sum(i["line_cost"] for i in items), 2)
        assert abs(order["total_value"] - expected_total) < 0.01

        # order items use the Order item shape (unit_price, not unit_cost)
        assert len(order["items"]) == len(items)
        for oi in order["items"]:
            for key in ("sku", "name", "quantity", "unit_price"):
                assert key in oi

    def test_submit_order_lead_time_is_14_days(self, client):
        """expected_delivery is exactly 14 days after order_date."""
        items = self._recommended_items(client)
        order = client.post("/api/restocking/order", json={"items": items}).json()

        order_date = datetime.fromisoformat(order["order_date"])
        expected_delivery = datetime.fromisoformat(order["expected_delivery"])
        assert (expected_delivery - order_date).days == 14

    def test_submit_empty_order_rejected(self, client):
        """An order with no items returns 400."""
        response = client.post("/api/restocking/order", json={"items": []})
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_submitted_order_appears_in_orders(self, client):
        """A submitted order is retrievable via GET /api/orders?status=Submitted."""
        before = len(client.get("/api/orders?status=Submitted").json())

        items = self._recommended_items(client)
        created = client.post("/api/restocking/order", json={"items": items}).json()

        after = client.get("/api/orders?status=Submitted").json()
        assert len(after) == before + 1
        assert any(o["order_number"] == created["order_number"] for o in after)

    def test_submitted_orders_have_unique_numbers(self, client):
        """Sequential submissions generate distinct order numbers and ids."""
        items = self._recommended_items(client)
        first = client.post("/api/restocking/order", json={"items": items}).json()
        second = client.post("/api/restocking/order", json={"items": items}).json()
        assert first["order_number"] != second["order_number"]
        assert first["id"] != second["id"]
