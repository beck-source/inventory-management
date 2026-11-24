"""
Tests for purchase order API endpoints.
"""
from datetime import date, timedelta

import pytest

import main


@pytest.fixture(autouse=True)
def restore_purchase_orders():
    """Purchase orders are a module-level list loaded from JSON; restore it after each test."""
    original = list(main.purchase_orders)
    yield
    main.purchase_orders[:] = original


def _future_date(days=14):
    return (date.today() + timedelta(days=days)).isoformat()


def _po_payload(**overrides):
    payload = {
        "backlog_item_id": "1",
        "supplier_name": "Acme Filters",
        "quantity": 350,
        "unit_cost": 12.5,
        "expected_delivery_date": _future_date(),
        "notes": "Rush order",
    }
    payload.update(overrides)
    return payload


class TestPurchaseOrderEndpoints:
    """Test suite for purchase-order-related endpoints."""

    def test_create_purchase_order(self, client):
        """Test creating a valid purchase order for a backlog item."""
        response = client.post("/api/purchase-orders", json=_po_payload())
        assert response.status_code == 201

        po = response.json()
        assert po["id"].startswith("PO-")
        assert po["backlog_item_id"] == "1"
        assert po["supplier_name"] == "Acme Filters"
        assert po["quantity"] == 350
        assert abs(po["unit_cost"] - 12.5) < 0.01
        assert po["status"] == "Pending"
        assert po["notes"] == "Rush order"
        assert "T" in po["created_date"]

    def test_get_purchase_order_by_backlog_item(self, client):
        """Test fetching a purchase order by the backlog item it was raised for."""
        created = client.post("/api/purchase-orders", json=_po_payload()).json()

        response = client.get("/api/purchase-orders/1")
        assert response.status_code == 200
        assert response.json() == created

    def test_get_nonexistent_purchase_order(self, client):
        """Test fetching a purchase order for a backlog item that has none."""
        response = client.get("/api/purchase-orders/999")
        assert response.status_code == 404
        assert "detail" in response.json()

    def test_backlog_reports_purchase_order_id(self, client):
        """Test that the backlog shows the PO ID, which the Dashboard uses to show View PO."""
        before = {b["id"]: b for b in client.get("/api/backlog").json()}
        assert before["1"]["purchase_order_id"] is None
        assert before["1"]["has_purchase_order"] is False

        po = client.post("/api/purchase-orders", json=_po_payload()).json()

        after = {b["id"]: b for b in client.get("/api/backlog").json()}
        assert after["1"]["purchase_order_id"] == po["id"]
        assert after["1"]["has_purchase_order"] is True
        assert after["2"]["purchase_order_id"] is None

    def test_create_duplicate_purchase_order(self, client):
        """Test that a second PO for the same backlog item is rejected."""
        client.post("/api/purchase-orders", json=_po_payload())
        response = client.post("/api/purchase-orders", json=_po_payload())
        assert response.status_code == 409

    def test_create_purchase_order_unknown_backlog_item(self, client):
        """Test raising a PO for a backlog item that doesn't exist."""
        response = client.post("/api/purchase-orders", json=_po_payload(backlog_item_id="999"))
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_purchase_order_blank_supplier(self, client):
        """Test that a whitespace-only supplier name is rejected."""
        response = client.post("/api/purchase-orders", json=_po_payload(supplier_name="   "))
        assert response.status_code == 400

    @pytest.mark.parametrize("quantity", [0, -5])
    def test_create_purchase_order_non_positive_quantity(self, client, quantity):
        """Test that zero or negative quantities are rejected."""
        response = client.post("/api/purchase-orders", json=_po_payload(quantity=quantity))
        assert response.status_code == 400

    def test_create_purchase_order_negative_unit_cost(self, client):
        """Test that a negative unit cost is rejected."""
        response = client.post("/api/purchase-orders", json=_po_payload(unit_cost=-1))
        assert response.status_code == 400

    def test_create_purchase_order_past_delivery_date(self, client):
        """Test that a delivery date clearly in the past is rejected."""
        two_days_ago = (date.today() - timedelta(days=2)).isoformat()
        response = client.post("/api/purchase-orders", json=_po_payload(expected_delivery_date=two_days_ago))
        assert response.status_code == 400
        assert "past" in response.json()["detail"].lower()

    def test_create_purchase_order_allows_yesterday_for_timezones(self, client):
        """Test that the server's yesterday is accepted, since it can be the user's today in UTC+ zones."""
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        response = client.post("/api/purchase-orders", json=_po_payload(expected_delivery_date=yesterday))
        assert response.status_code == 201

    def test_create_purchase_order_invalid_delivery_date(self, client):
        """Test that a malformed delivery date returns 400 rather than a server error."""
        response = client.post("/api/purchase-orders", json=_po_payload(expected_delivery_date="soon"))
        assert response.status_code == 400

    def test_create_purchase_order_blank_notes_stored_as_null(self, client):
        """Test that whitespace-only notes are stored as null."""
        response = client.post("/api/purchase-orders", json=_po_payload(notes="  "))
        assert response.json()["notes"] is None
