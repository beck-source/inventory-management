"""
Tests for order endpoints, including the restocking POST /api/orders endpoint.
"""
from datetime import datetime


class TestDemandUnitCost:
    """Demand forecasts must expose a unit_cost so restocking can budget against them."""

    def test_demand_items_have_unit_cost(self, client):
        """Every demand forecast item includes a non-negative numeric unit_cost."""
        response = client.get("/api/demand")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0

        for forecast in data:
            assert "unit_cost" in forecast, f"{forecast['item_sku']} missing unit_cost"
            assert isinstance(forecast["unit_cost"], (int, float))
            assert forecast["unit_cost"] >= 0


class TestCreateRestockOrder:
    """Test suite for submitting restocking orders via POST /api/orders."""

    def _payload(self):
        return {
            "items": [
                {"sku": "WDG-001", "name": "Industrial Widget Type A", "quantity": 150, "unit_price": 12.50},
                {"sku": "GSK-203", "name": "High-Temperature Gasket", "quantity": 100, "unit_price": 8.25}
            ]
        }

    def test_create_restock_order_returns_201(self, client):
        """Submitting a restock order returns 201 with a Submitted order."""
        response = client.post("/api/orders", json=self._payload())
        assert response.status_code == 201

        order = response.json()
        assert order["status"] == "Submitted"
        assert order["customer"] == "Internal Restock"
        assert order["order_number"].startswith("RST-")
        assert len(order["items"]) == 2

    def test_total_value_is_calculated(self, client):
        """total_value equals the sum of quantity * unit_price across items."""
        response = client.post("/api/orders", json=self._payload())
        order = response.json()

        expected_total = round(150 * 12.50 + 100 * 8.25, 2)
        assert order["total_value"] == expected_total

    def test_lead_time_is_14_days(self, client):
        """expected_delivery is exactly 14 days after order_date."""
        response = client.post("/api/orders", json=self._payload())
        order = response.json()

        order_date = datetime.fromisoformat(order["order_date"])
        expected_delivery = datetime.fromisoformat(order["expected_delivery"])
        assert (expected_delivery - order_date).days == 14

    def test_submitted_order_appears_in_get_orders(self, client):
        """A submitted order is returned by GET /api/orders."""
        created = client.post("/api/orders", json=self._payload()).json()

        response = client.get("/api/orders")
        assert response.status_code == 200

        orders = response.json()
        assert any(o["id"] == created["id"] for o in orders), \
            "Submitted restock order should appear in GET /api/orders"

    def test_submitted_order_filterable_by_status(self, client):
        """The submitted order is returned when filtering orders by status=Submitted."""
        client.post("/api/orders", json=self._payload())

        response = client.get("/api/orders", params={"status": "Submitted"})
        assert response.status_code == 200

        submitted = response.json()
        assert len(submitted) > 0
        assert all(o["status"] == "Submitted" for o in submitted)

    def test_submitted_order_excluded_from_dashboard_value(self, client):
        """Internal restock orders must not inflate the dashboard's order value."""
        before = client.get("/api/dashboard/summary").json()["total_orders_value"]

        client.post("/api/orders", json=self._payload())

        after = client.get("/api/dashboard/summary").json()["total_orders_value"]
        assert after == before, "Submitted restock order should not change total_orders_value"
