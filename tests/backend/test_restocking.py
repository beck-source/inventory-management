"""
Tests for restocking API endpoints.
"""
import pytest


def _forecasts(client):
    return {f["item_sku"]: f for f in client.get("/api/demand").json()}


class TestRestockingEndpoints:
    """Test suite for restock order endpoints."""

    def test_create_restock_order_success(self, client):
        """Test placing a valid order: lead time is the max of item lead times."""
        forecasts = _forecasts(client)
        skus = ["WDG-001", "MTR-304"]
        items = [{"sku": s, "quantity": 2} for s in skus]
        total = sum(2 * forecasts[s]["unit_cost"] for s in skus)

        response = client.post("/api/restocking/orders", json={"budget": total + 100, "items": items})
        assert response.status_code == 201

        order = response.json()
        assert order["status"] == "Submitted"
        assert abs(order["total_value"] - total) < 0.01
        assert order["lead_time_days"] == max(forecasts[s]["lead_time_days"] for s in skus)
        assert order["expected_delivery"] > order["submitted_date"]

        listed = client.get("/api/submitted-orders").json()
        assert order["id"] in [o["id"] for o in listed]

    def test_client_supplied_cost_is_ignored(self, client):
        """Test that unit cost comes from the server, not the request."""
        forecasts = _forecasts(client)
        response = client.post("/api/restocking/orders", json={
            "budget": 100000,
            "items": [{"sku": "WDG-001", "quantity": 1, "unit_cost": 0.01}],
        })
        assert response.status_code == 201
        assert response.json()["items"][0]["unit_cost"] == forecasts["WDG-001"]["unit_cost"]

    def test_over_budget_rejected(self, client):
        """Test that an order exceeding the budget is rejected."""
        response = client.post("/api/restocking/orders", json={
            "budget": 1, "items": [{"sku": "MTR-304", "quantity": 10}],
        })
        assert response.status_code == 400
        assert "budget" in response.json()["detail"].lower()
        assert client.get("/api/submitted-orders").json() == []

    def test_empty_items_rejected(self, client):
        """Test that an order with no items is rejected."""
        response = client.post("/api/restocking/orders", json={"budget": 1000, "items": []})
        assert response.status_code == 400

    def test_unknown_sku_rejected(self, client):
        """Test that an unknown SKU is rejected."""
        response = client.post("/api/restocking/orders", json={
            "budget": 1000, "items": [{"sku": "NOPE-999", "quantity": 1}],
        })
        assert response.status_code == 400
        assert "unknown sku" in response.json()["detail"].lower()

    @pytest.mark.parametrize("quantity", [0, -5])
    def test_non_positive_quantity_rejected(self, client, quantity):
        """Test that zero or negative quantities are rejected."""
        response = client.post("/api/restocking/orders", json={
            "budget": 1000, "items": [{"sku": "WDG-001", "quantity": quantity}],
        })
        assert response.status_code == 400

    def test_submitted_orders_newest_first(self, client):
        """Test that submitted orders are listed newest first."""
        ids = []
        for qty in (1, 2, 3):
            r = client.post("/api/restocking/orders", json={
                "budget": 100000, "items": [{"sku": "FLT-405", "quantity": qty}],
            })
            ids.append(r.json()["id"])

        listed = [o["id"] for o in client.get("/api/submitted-orders").json()]
        assert listed == list(reversed(ids))
