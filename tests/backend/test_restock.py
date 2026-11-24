"""
Tests for restocking order API endpoints.
"""
import pytest

import main


@pytest.fixture(autouse=True)
def clear_restock_orders():
    """Restock orders live in a module-level list, so reset it to keep tests independent."""
    main.restock_orders.clear()
    yield
    main.restock_orders.clear()


class TestRestockEndpoints:
    """Test suite for restocking-related endpoints."""

    def test_demand_forecasts_include_cost_and_lead_time(self, client):
        """Test that forecasts expose the pricing data the Restocking tab needs."""
        response = client.get("/api/demand")
        assert response.status_code == 200

        for forecast in response.json():
            assert isinstance(forecast["unit_cost"], (int, float))
            assert isinstance(forecast["lead_time_days"], int)
            assert forecast["unit_cost"] > 0
            assert forecast["lead_time_days"] > 0

    def test_get_restock_orders_empty(self, client):
        """Test that no restock orders exist before any are submitted."""
        response = client.get("/api/restock-orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_restock_order(self, client):
        """Test submitting a valid restock order."""
        payload = {
            "budget": 25000,
            "items": [
                {"sku": "WDG-001", "quantity": 10},
                {"sku": "CTL-330", "quantity": 1},
            ],
        }
        response = client.post("/api/restock-orders", json=payload)
        assert response.status_code == 201

        order = response.json()
        assert order["order_number"].startswith("RST-")
        assert order["status"] == "Submitted"
        assert order["budget"] == 25000
        assert len(order["items"]) == 2
        assert "T" in order["submitted_date"]
        assert "T" in order["expected_delivery"]

    def test_restock_order_total_calculation(self, client):
        """Test that totals are computed server-side from forecast unit costs."""
        forecasts = {f["item_sku"]: f for f in client.get("/api/demand").json()}
        payload = {"budget": 100000, "items": [{"sku": "WDG-001", "quantity": 10}, {"sku": "FLT-405", "quantity": 5}]}

        order = client.post("/api/restock-orders", json=payload).json()

        expected = 10 * forecasts["WDG-001"]["unit_cost"] + 5 * forecasts["FLT-405"]["unit_cost"]
        assert abs(order["total_value"] - expected) < 0.01
        for item in order["items"]:
            assert abs(item["line_total"] - item["quantity"] * item["unit_cost"]) < 0.01
            assert item["unit_cost"] == forecasts[item["sku"]]["unit_cost"]

    def test_restock_order_lead_time_is_longest_item(self, client):
        """Test that order lead time equals the slowest line item's lead time."""
        payload = {"budget": 100000, "items": [{"sku": "FLT-405", "quantity": 1}, {"sku": "CTL-330", "quantity": 1}]}
        order = client.post("/api/restock-orders", json=payload).json()

        assert order["lead_time_days"] == max(i["lead_time_days"] for i in order["items"])

    def test_created_restock_order_appears_in_list(self, client):
        """Test that submitted orders are returned newest first."""
        first = client.post("/api/restock-orders", json={"budget": 1000, "items": [{"sku": "PSU-501", "quantity": 1}]}).json()
        second = client.post("/api/restock-orders", json={"budget": 1000, "items": [{"sku": "GSK-203", "quantity": 1}]}).json()

        data = client.get("/api/restock-orders").json()
        assert [o["id"] for o in data] == [second["id"], first["id"]]
        assert first["order_number"] != second["order_number"]

    def test_restock_order_over_budget(self, client):
        """Test that an order exceeding the budget is rejected."""
        response = client.post("/api/restock-orders", json={"budget": 100, "items": [{"sku": "WDG-001", "quantity": 10}]})
        assert response.status_code == 400
        assert "budget" in response.json()["detail"].lower()
        assert client.get("/api/restock-orders").json() == []

    def test_restock_order_unknown_sku(self, client):
        """Test that an unknown SKU is rejected."""
        response = client.post("/api/restock-orders", json={"budget": 1000, "items": [{"sku": "NOPE-999", "quantity": 1}]})
        assert response.status_code == 400
        assert "NOPE-999" in response.json()["detail"]

    @pytest.mark.parametrize("quantity", [0, -5])
    def test_restock_order_invalid_quantity(self, client, quantity):
        """Test that zero or negative quantities are rejected."""
        response = client.post("/api/restock-orders", json={"budget": 1000, "items": [{"sku": "PSU-501", "quantity": quantity}]})
        assert response.status_code == 400

    def test_restock_order_total_equal_to_budget(self, client):
        """Test that an order costing exactly the budget is accepted (boundary)."""
        forecasts = {f["item_sku"]: f for f in client.get("/api/demand").json()}
        budget = 2 * forecasts["WDG-001"]["unit_cost"]
        response = client.post("/api/restock-orders", json={"budget": budget, "items": [{"sku": "WDG-001", "quantity": 2}]})
        assert response.status_code == 201

    @pytest.mark.parametrize("budget", ["-1", "NaN", "Infinity"])
    def test_restock_order_invalid_budget(self, client, budget):
        """Test that negative or non-finite budgets are rejected (NaN would otherwise bypass the budget check)."""
        body = '{"budget": %s, "items": [{"sku": "WDG-001", "quantity": 1000}]}' % budget
        response = client.post("/api/restock-orders", content=body, headers={"Content-Type": "application/json"})
        assert response.status_code == 400
        assert client.get("/api/restock-orders").json() == []

    def test_restock_order_duplicate_sku(self, client):
        """Test that the same SKU can't appear twice in one order."""
        payload = {"budget": 10000, "items": [{"sku": "PSU-501", "quantity": 1}, {"sku": "PSU-501", "quantity": 1}]}
        response = client.post("/api/restock-orders", json=payload)
        assert response.status_code == 400
        assert "duplicate" in response.json()["detail"].lower()

    def test_restock_order_empty_items(self, client):
        """Test that an order with no items is rejected."""
        response = client.post("/api/restock-orders", json={"budget": 1000, "items": []})
        assert response.status_code == 400
