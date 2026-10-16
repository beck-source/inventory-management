"""
Tests for the restocking order endpoints.
"""
import pytest
from main import submitted_orders


@pytest.fixture(autouse=True)
def clear_submitted_orders():
    """Restocking orders live in module memory, so reset them around each test."""
    submitted_orders.clear()
    yield
    submitted_orders.clear()


class TestRestockingOrders:
    """Test suite for POST and GET /api/restocking/orders."""

    def test_create_order_returns_201_with_server_computed_totals(self, client):
        """Totals and lead time come from server data: WDG-001 is $40.00 (Actuators, 21 days)."""
        response = client.post("/api/restocking/orders", json={
            "items": [{"sku": "WDG-001", "quantity": 3}]
        })
        assert response.status_code == 201

        data = response.json()
        assert data["order_number"].startswith("RST-")
        assert data["status"] == "Submitted"
        assert data["total_value"] == 120.0
        assert data["lead_time_days"] == 21
        assert data["items"][0]["name"] == "Industrial Widget Type A"
        assert data["items"][0]["line_total"] == 120.0

    def test_order_lead_time_is_longest_line(self, client):
        """The order arrives when its slowest line does (Actuators 21 days beats Power Supplies 7 days)."""
        response = client.post("/api/restocking/orders", json={
            "items": [
                {"sku": "PSU-501", "quantity": 2},
                {"sku": "WDG-001", "quantity": 1}
            ]
        })
        assert response.status_code == 201

        data = response.json()
        assert data["lead_time_days"] == 21
        lead_times = {line["sku"]: line["lead_time_days"] for line in data["items"]}
        assert lead_times == {"PSU-501": 7, "WDG-001": 21}

    def test_client_supplied_price_is_ignored(self, client):
        """Extra price fields in the request do not change the server-side unit cost."""
        response = client.post("/api/restocking/orders", json={
            "items": [{"sku": "PSU-501", "quantity": 1, "unit_cost": 0.01}]
        })
        assert response.status_code == 201
        assert response.json()["items"][0]["unit_cost"] == 18.99

    def test_get_lists_submitted_orders_newest_first(self, client):
        """A submitted order appears in the GET list, with the most recent first."""
        client.post("/api/restocking/orders", json={"items": [{"sku": "PSU-501", "quantity": 1}]})
        second = client.post("/api/restocking/orders", json={"items": [{"sku": "CTL-330", "quantity": 1}]}).json()

        response = client.get("/api/restocking/orders")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == second["id"]

    def test_submitted_quantity_shows_as_on_order_in_demand(self, client):
        """Submitted units count as on order for their SKU only, so recommendations can drop them."""
        client.post("/api/restocking/orders", json={"items": [{"sku": "PSU-501", "quantity": 2}]})
        client.post("/api/restocking/orders", json={"items": [{"sku": "PSU-501", "quantity": 3}]})

        forecasts = {f["item_sku"]: f for f in client.get("/api/demand").json()}
        assert forecasts["PSU-501"]["on_order"] == 5
        assert forecasts["WDG-001"]["on_order"] == 0

    def test_submitted_orders_do_not_change_main_orders_feed(self, client):
        """Restocking orders must not leak into /api/orders, which feeds dashboard totals."""
        before = client.get("/api/orders").json()
        client.post("/api/restocking/orders", json={"items": [{"sku": "PSU-501", "quantity": 1}]})
        after = client.get("/api/orders").json()
        assert len(after) == len(before)

    def test_empty_items_returns_400(self, client):
        response = client.post("/api/restocking/orders", json={"items": []})
        assert response.status_code == 400

    def test_zero_quantity_returns_400(self, client):
        response = client.post("/api/restocking/orders", json={
            "items": [{"sku": "PSU-501", "quantity": 0}]
        })
        assert response.status_code == 400

    def test_negative_quantity_returns_400(self, client):
        response = client.post("/api/restocking/orders", json={
            "items": [{"sku": "PSU-501", "quantity": -5}]
        })
        assert response.status_code == 400

    def test_oversized_quantity_returns_400(self, client):
        """A direct API call cannot submit an absurd quantity."""
        response = client.post("/api/restocking/orders", json={
            "items": [{"sku": "PSU-501", "quantity": 10**12}]
        })
        assert response.status_code == 400
        assert submitted_orders == []

    def test_unknown_sku_returns_400(self, client):
        response = client.post("/api/restocking/orders", json={
            "items": [{"sku": "NOPE-999", "quantity": 1}]
        })
        assert response.status_code == 400

    def test_duplicate_sku_returns_400(self, client):
        response = client.post("/api/restocking/orders", json={
            "items": [
                {"sku": "PSU-501", "quantity": 1},
                {"sku": "PSU-501", "quantity": 2}
            ]
        })
        assert response.status_code == 400

    def test_invalid_payload_returns_422(self, client):
        response = client.post("/api/restocking/orders", json={"items": [{"sku": "PSU-501"}]})
        assert response.status_code == 422
