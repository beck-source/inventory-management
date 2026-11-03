"""
Tests for restocking order endpoints and restocking fields on /api/demand.
"""
from datetime import datetime, timedelta

import pytest

from main import restocking_orders

# Values from server/data/demand_forecasts.json
BRG_SKU, BRG_COST, BRG_LEAD = "BRG-102", 18.75, 7
MTR_SKU, MTR_COST, MTR_LEAD = "MTR-304", 310.0, 21


@pytest.fixture(autouse=True)
def clean_restocking_orders():
    """Restocking orders live in module-level state; isolate each test."""
    restocking_orders.clear()
    yield
    restocking_orders.clear()


def post_order(client, items, budget=1_000_000):
    return client.post("/api/restocking-orders", json={"budget": budget, "items": items})


class TestCreateRestockingOrder:
    """Test suite for POST /api/restocking-orders."""

    def test_create_order_success(self, client):
        """Test a valid order returns 201 with server-computed fields."""
        response = post_order(client, [
            {"sku": BRG_SKU, "quantity": 10},
            {"sku": MTR_SKU, "quantity": 2},
        ])
        assert response.status_code == 201

        order = response.json()
        assert order["status"] == "Submitted"
        assert order["budget"] == 1_000_000
        assert len(order["items"]) == 2

        brg = next(i for i in order["items"] if i["sku"] == BRG_SKU)
        assert brg["quantity"] == 10
        assert brg["unit_cost"] == BRG_COST
        assert abs(brg["line_total"] - 10 * BRG_COST) < 0.01
        assert brg["lead_time_days"] == BRG_LEAD
        assert brg["name"]

        expected_total = 10 * BRG_COST + 2 * MTR_COST
        assert abs(order["total_cost"] - expected_total) < 0.01

    def test_order_lead_time_is_max_of_items(self, client):
        """Test order lead time is the longest item lead time."""
        order = post_order(client, [
            {"sku": BRG_SKU, "quantity": 1},
            {"sku": MTR_SKU, "quantity": 1},
        ]).json()
        assert order["lead_time_days"] == max(BRG_LEAD, MTR_LEAD)

    def test_expected_delivery_is_submitted_plus_lead_time(self, client):
        """Test expected delivery equals submitted date plus lead time."""
        order = post_order(client, [
            {"sku": BRG_SKU, "quantity": 1},
            {"sku": MTR_SKU, "quantity": 1},
        ]).json()

        submitted = datetime.fromisoformat(order["submitted_date"])
        delivery = datetime.fromisoformat(order["expected_delivery"])
        assert delivery - submitted == timedelta(days=order["lead_time_days"])

    def test_order_number_format(self, client):
        """Test the first order number is RST-<year>-0001 and increments."""
        first = post_order(client, [{"sku": BRG_SKU, "quantity": 1}]).json()
        second = post_order(client, [{"sku": BRG_SKU, "quantity": 1}]).json()

        year = datetime.now().year
        assert first["order_number"] == f"RST-{year}-0001"
        assert second["order_number"] == f"RST-{year}-0002"
        assert first["id"] != second["id"]

    def test_client_cannot_influence_price(self, client):
        """Test client-supplied unit_cost and other extra fields are ignored."""
        response = post_order(client, [
            {
                "sku": BRG_SKU,
                "quantity": 10,
                "unit_cost": 0.01,
                "line_total": 0.10,
                "lead_time_days": 1,
            }
        ])
        assert response.status_code == 201

        order = response.json()
        item = order["items"][0]
        assert item["unit_cost"] == BRG_COST
        assert abs(item["line_total"] - 10 * BRG_COST) < 0.01
        assert item["lead_time_days"] == BRG_LEAD
        assert abs(order["total_cost"] - 10 * BRG_COST) < 0.01
        assert order["lead_time_days"] == BRG_LEAD

    def test_create_order_with_empty_items(self, client):
        """Test an order with no items is rejected."""
        response = post_order(client, [])
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_create_order_with_unknown_sku(self, client):
        """Test an unknown SKU is rejected."""
        response = post_order(client, [{"sku": "NOPE-999", "quantity": 1}])
        assert response.status_code == 400
        assert "NOPE-999" in response.json()["detail"]

    @pytest.mark.parametrize("quantity", [0, -5])
    def test_create_order_with_non_positive_quantity(self, client, quantity):
        """Test zero or negative quantities are rejected."""
        response = post_order(client, [{"sku": BRG_SKU, "quantity": quantity}])
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_create_order_exceeding_budget(self, client):
        """Test an order whose total is above budget is rejected."""
        # 10 x 18.75 = 187.50
        response = post_order(client, [{"sku": BRG_SKU, "quantity": 10}], budget=187.0)
        assert response.status_code == 400
        assert "budget" in response.json()["detail"].lower()

    def test_create_order_at_exact_budget(self, client):
        """Test an order whose total equals the budget is accepted."""
        response = post_order(client, [{"sku": BRG_SKU, "quantity": 10}], budget=187.5)
        assert response.status_code == 201

    def test_rejected_order_is_not_stored(self, client):
        """Test failed submissions do not appear in the order list."""
        post_order(client, [{"sku": "NOPE-999", "quantity": 1}])
        post_order(client, [{"sku": BRG_SKU, "quantity": 10}], budget=1.0)

        assert client.get("/api/restocking-orders").json() == []


class TestGetRestockingOrders:
    """Test suite for GET /api/restocking-orders."""

    def test_get_orders_initially_empty(self, client):
        """Test the list is empty before any order is submitted."""
        response = client.get("/api/restocking-orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_orders_newest_first(self, client):
        """Test orders are returned newest first."""
        first = post_order(client, [{"sku": BRG_SKU, "quantity": 1}]).json()
        second = post_order(client, [{"sku": MTR_SKU, "quantity": 1}]).json()
        third = post_order(client, [{"sku": BRG_SKU, "quantity": 2}]).json()

        response = client.get("/api/restocking-orders")
        assert response.status_code == 200

        numbers = [o["order_number"] for o in response.json()]
        assert numbers == [
            third["order_number"],
            second["order_number"],
            first["order_number"],
        ]

    def test_get_orders_structure(self, client):
        """Test stored orders have the full response structure."""
        post_order(client, [{"sku": BRG_SKU, "quantity": 3}])

        orders = client.get("/api/restocking-orders").json()
        assert len(orders) == 1

        order = orders[0]
        for field in ["id", "order_number", "submitted_date", "budget", "items",
                      "total_cost", "lead_time_days", "expected_delivery", "status"]:
            assert field in order

        for item in order["items"]:
            for field in ["sku", "name", "quantity", "unit_cost", "line_total", "lead_time_days"]:
                assert field in item


class TestDemandRestockingFields:
    """Test suite for restocking fields on /api/demand items."""

    def test_demand_items_include_restocking_fields(self, client):
        """Test all 9 demand items expose unit_cost, quantity_on_hand, lead_time_days."""
        response = client.get("/api/demand")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 9

        for item in data:
            assert isinstance(item["unit_cost"], (int, float)), item["item_sku"]
            assert isinstance(item["quantity_on_hand"], int), item["item_sku"]
            assert isinstance(item["lead_time_days"], int), item["item_sku"]
            assert item["unit_cost"] > 0
            assert item["quantity_on_hand"] >= 0
            assert item["lead_time_days"] > 0


class TestRestockingOrderHardening:
    """Test suite for invalid or edge-case restocking order payloads."""

    def test_duplicate_sku_rejected(self, client):
        """Test the same SKU on two lines is rejected."""
        payload = {"budget": 10000, "items": [
            {"sku": "WDG-001", "quantity": 5}, {"sku": "WDG-001", "quantity": 5}]}
        response = client.post("/api/restocking-orders", json=payload)
        assert response.status_code == 400
        assert client.get("/api/restocking-orders").json() == []

    @pytest.mark.parametrize("budget", ["NaN", "Infinity", "-5"])
    def test_non_finite_or_negative_budget_rejected(self, client, budget):
        """Test NaN, Infinity and negative budgets are rejected and nothing is stored."""
        body = '{"budget": %s, "items": [{"sku": "WDG-001", "quantity": 1}]}' % budget
        response = client.post("/api/restocking-orders", content=body,
                               headers={"content-type": "application/json"})
        assert response.status_code == 400
        assert client.get("/api/restocking-orders").status_code == 200
        assert client.get("/api/restocking-orders").json() == []

    def test_float_total_at_exact_budget_accepted(self, client):
        """Test 3 x 9.80 (29.400000000000002 in float) fits a 29.40 budget."""
        payload = {"budget": 29.4, "items": [{"sku": "GSK-203", "quantity": 3}]}
        response = client.post("/api/restocking-orders", json=payload)
        assert response.status_code == 201
        assert response.json()["total_cost"] == 29.4

    def test_mixed_valid_and_invalid_lines_rejected_whole(self, client):
        """Test one bad line rejects the whole order."""
        payload = {"budget": 10000, "items": [
            {"sku": "WDG-001", "quantity": 5}, {"sku": "NOPE-000", "quantity": 1}]}
        assert client.post("/api/restocking-orders", json=payload).status_code == 400
        assert client.get("/api/restocking-orders").json() == []
