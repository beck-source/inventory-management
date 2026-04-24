"""
Tests for restocking order API endpoints.
"""
import pytest


VALID_PAYLOAD = {
    "items": [
        {
            "inventory_item_id": "32",
            "sku": "PSU-508",
            "name": "Battery Backup Power Supply",
            "quantity": 45,
            "unit_cost": 185.50
        },
        {
            "inventory_item_id": "4",
            "sku": "TMP-201",
            "name": "Temperature Sensor Module",
            "quantity": 55,
            "unit_cost": 89.50
        }
    ],
    "total_budget": 15000.00
}


class TestSubmitRestockingOrder:
    """Tests for POST /api/restocking-orders."""

    def test_submit_returns_201(self, client):
        """Valid payload returns HTTP 201."""
        response = client.post("/api/restocking-orders", json=VALID_PAYLOAD)
        assert response.status_code == 201

    def test_submit_returns_order_number(self, client):
        """Response includes an RST- prefixed order number."""
        response = client.post("/api/restocking-orders", json=VALID_PAYLOAD)
        data = response.json()
        assert "order_number" in data
        assert data["order_number"].startswith("RST-")

    def test_submit_status_is_submitted(self, client):
        """Submitted restocking order has status 'Submitted'."""
        response = client.post("/api/restocking-orders", json=VALID_PAYLOAD)
        data = response.json()
        assert data["status"] == "Submitted"

    def test_submit_customer_is_internal(self, client):
        """Customer field is 'Internal Restocking'."""
        response = client.post("/api/restocking-orders", json=VALID_PAYLOAD)
        data = response.json()
        assert data["customer"] == "Internal Restocking"

    def test_submit_total_value_calculated(self, client):
        """Total value equals sum of quantity * unit_cost across items."""
        response = client.post("/api/restocking-orders", json=VALID_PAYLOAD)
        data = response.json()
        expected = round(45 * 185.50 + 55 * 89.50, 2)
        assert data["total_value"] == expected

    def test_submit_has_expected_delivery(self, client):
        """Response includes an expected_delivery date."""
        response = client.post("/api/restocking-orders", json=VALID_PAYLOAD)
        data = response.json()
        assert "expected_delivery" in data
        assert data["expected_delivery"] is not None

    def test_submit_has_order_date(self, client):
        """Response includes an order_date."""
        response = client.post("/api/restocking-orders", json=VALID_PAYLOAD)
        data = response.json()
        assert "order_date" in data
        assert data["order_date"] is not None

    def test_submit_items_in_response(self, client):
        """Response includes the submitted items."""
        response = client.post("/api/restocking-orders", json=VALID_PAYLOAD)
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 2

    def test_submit_empty_items_returns_400(self, client):
        """Empty items list returns HTTP 400."""
        payload = {"items": [], "total_budget": 10000.0}
        response = client.post("/api/restocking-orders", json=payload)
        assert response.status_code == 400

    def test_submit_single_item(self, client):
        """Single item payload is accepted."""
        payload = {
            "items": [
                {
                    "inventory_item_id": "4",
                    "sku": "TMP-201",
                    "name": "Temperature Sensor Module",
                    "quantity": 10,
                    "unit_cost": 89.50
                }
            ],
            "total_budget": 5000.0
        }
        response = client.post("/api/restocking-orders", json=payload)
        assert response.status_code == 201


class TestLeadTimeCalculation:
    """Tests for lead time logic in POST /api/restocking-orders."""

    def test_small_quantity_lead_time(self, client):
        """Qty <= 20 results in 4-day lead time."""
        from datetime import datetime, timedelta
        payload = {
            "items": [
                {
                    "inventory_item_id": "4",
                    "sku": "TMP-201",
                    "name": "Temperature Sensor Module",
                    "quantity": 10,  # small
                    "unit_cost": 89.50
                }
            ],
            "total_budget": 5000.0
        }
        response = client.post("/api/restocking-orders", json=payload)
        data = response.json()
        order_date = datetime.fromisoformat(data["order_date"])
        expected_delivery = datetime.fromisoformat(data["expected_delivery"])
        lead_days = (expected_delivery - order_date).days
        assert lead_days == 4

    def test_medium_quantity_lead_time(self, client):
        """21 <= Qty <= 100 results in 8-day lead time."""
        from datetime import datetime
        payload = {
            "items": [
                {
                    "inventory_item_id": "4",
                    "sku": "TMP-201",
                    "name": "Temperature Sensor Module",
                    "quantity": 55,  # medium
                    "unit_cost": 89.50
                }
            ],
            "total_budget": 10000.0
        }
        response = client.post("/api/restocking-orders", json=payload)
        data = response.json()
        order_date = datetime.fromisoformat(data["order_date"])
        expected_delivery = datetime.fromisoformat(data["expected_delivery"])
        lead_days = (expected_delivery - order_date).days
        assert lead_days == 8

    def test_large_quantity_lead_time(self, client):
        """Qty > 100 results in 12-day lead time."""
        from datetime import datetime
        payload = {
            "items": [
                {
                    "inventory_item_id": "4",
                    "sku": "TMP-201",
                    "name": "Temperature Sensor Module",
                    "quantity": 150,  # large
                    "unit_cost": 89.50
                }
            ],
            "total_budget": 50000.0
        }
        response = client.post("/api/restocking-orders", json=payload)
        data = response.json()
        order_date = datetime.fromisoformat(data["order_date"])
        expected_delivery = datetime.fromisoformat(data["expected_delivery"])
        lead_days = (expected_delivery - order_date).days
        assert lead_days == 12

    def test_mixed_items_uses_max_lead_time(self, client):
        """Multiple items with different sizes use maximum lead time."""
        from datetime import datetime
        payload = {
            "items": [
                {
                    "inventory_item_id": "4",
                    "sku": "TMP-201",
                    "name": "Temperature Sensor Module",
                    "quantity": 10,   # small -> 4 days
                    "unit_cost": 89.50
                },
                {
                    "inventory_item_id": "32",
                    "sku": "PSU-508",
                    "name": "Battery Backup Power Supply",
                    "quantity": 150,  # large -> 12 days
                    "unit_cost": 185.50
                }
            ],
            "total_budget": 50000.0
        }
        response = client.post("/api/restocking-orders", json=payload)
        data = response.json()
        order_date = datetime.fromisoformat(data["order_date"])
        expected_delivery = datetime.fromisoformat(data["expected_delivery"])
        lead_days = (expected_delivery - order_date).days
        assert lead_days == 12  # max of 4 and 12


class TestGetRestockingOrders:
    """Tests for GET /api/restocking-orders."""

    def test_get_returns_200(self, client):
        """GET endpoint returns HTTP 200."""
        response = client.get("/api/restocking-orders")
        assert response.status_code == 200

    def test_get_returns_list(self, client):
        """GET returns a list."""
        response = client.get("/api/restocking-orders")
        assert isinstance(response.json(), list)

    def test_submitted_order_appears_in_list(self, client):
        """A submitted restocking order appears in GET /api/restocking-orders."""
        post_response = client.post("/api/restocking-orders", json=VALID_PAYLOAD)
        order_number = post_response.json()["order_number"]

        get_response = client.get("/api/restocking-orders")
        order_numbers = [o["order_number"] for o in get_response.json()]
        assert order_number in order_numbers


class TestRestockingOrderInOrders:
    """Tests that restocking orders appear in the main orders list."""

    def test_submitted_order_appears_in_orders(self, client):
        """A submitted restocking order appears in GET /api/orders."""
        post_response = client.post("/api/restocking-orders", json=VALID_PAYLOAD)
        order_number = post_response.json()["order_number"]

        orders_response = client.get("/api/orders")
        order_numbers = [o["order_number"] for o in orders_response.json()]
        assert order_number in order_numbers

    def test_submitted_order_has_submitted_status_in_orders(self, client):
        """Restocking order in /api/orders has status 'Submitted'."""
        post_response = client.post("/api/restocking-orders", json=VALID_PAYLOAD)
        order_number = post_response.json()["order_number"]

        orders_response = client.get("/api/orders")
        matching = [o for o in orders_response.json() if o["order_number"] == order_number]
        assert len(matching) == 1
        assert matching[0]["status"] == "Submitted"

    def test_filter_by_submitted_status(self, client):
        """GET /api/orders?status=Submitted returns submitted restocking orders."""
        client.post("/api/restocking-orders", json=VALID_PAYLOAD)

        response = client.get("/api/orders?status=Submitted")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        for order in data:
            assert order["status"] == "Submitted"
