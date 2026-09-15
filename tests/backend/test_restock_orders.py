"""
Tests for the restock order endpoints (POST/GET /api/restock-orders).
"""
from datetime import datetime


class TestRestockOrders:
    def test_create_restock_order_computes_delivery_and_totals(self, client):
        payload = {
            "budget": 5000,
            "items": [
                {"item_sku": "WDG-001", "item_name": "Industrial Widget Type A", "quantity": 10, "unit_cost": 25.0}
            ]
        }
        response = client.post("/api/restock-orders", json=payload)
        assert response.status_code == 201
        order = response.json()

        assert order["total_cost"] == 250.0
        assert order["items"][0]["line_total"] == 250.0

        order_date = datetime.fromisoformat(order["order_date"])
        expected = datetime.fromisoformat(order["expected_delivery_date"])
        assert (expected - order_date).days == 14

    def test_get_restock_orders_lists_created_order(self, client):
        client.post("/api/restock-orders", json={
            "budget": 1000,
            "items": [{"item_sku": "BRG-102", "item_name": "Steel Bearing Assembly", "quantity": 5, "unit_cost": 10.0}]
        })
        response = client.get("/api/restock-orders")
        assert response.status_code == 200
        assert any(o["items"][0]["item_sku"] == "BRG-102" for o in response.json())

    def test_create_restock_order_rejects_empty_items(self, client):
        response = client.post("/api/restock-orders", json={"budget": 1000, "items": []})
        assert response.status_code == 400
