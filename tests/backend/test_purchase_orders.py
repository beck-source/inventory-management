"""
Tests for purchase order API endpoints (raised against backlog / inventory shortage items).
"""
import pytest

import mock_data


@pytest.fixture(autouse=True)
def reset_purchase_orders():
    """
    Purchase orders live in a module-level list shared by every test.
    Snapshot and restore it IN PLACE: main.py bound the same list object at import,
    so rebinding mock_data.purchase_orders would not affect the app.
    """
    snapshot = list(mock_data.purchase_orders)
    yield
    mock_data.purchase_orders[:] = snapshot


def _payload(backlog_item_id, **overrides):
    payload = {
        "backlog_item_id": backlog_item_id,
        "supplier_name": "Acme Supply Co.",
        "quantity": 350,
        "unit_cost": 12.5,
        "expected_delivery_date": "2025-11-15",
        "notes": "Rush order",
    }
    payload.update(overrides)
    return payload


def _backlog_ids(client):
    return [item["id"] for item in client.get("/api/backlog").json()]


class TestPurchaseOrderEndpoints:
    """Test suite for purchase-order-related endpoints."""

    def test_create_purchase_order(self, client):
        """Test creating a purchase order for a backlog item."""
        backlog_id = _backlog_ids(client)[0]

        response = client.post("/api/purchase-orders", json=_payload(backlog_id))
        assert response.status_code == 201

        po = response.json()
        assert po["id"].startswith("PO-")
        assert po["backlog_item_id"] == backlog_id
        assert po["supplier_name"] == "Acme Supply Co."
        assert po["quantity"] == 350
        assert po["unit_cost"] == 12.5
        assert po["expected_delivery_date"] == "2025-11-15"
        assert po["status"] == "Pending"
        assert po["notes"] == "Rush order"
        assert "-" in po["created_date"]

    def test_create_purchase_order_without_notes(self, client):
        """Test that notes are optional."""
        backlog_id = _backlog_ids(client)[0]
        payload = _payload(backlog_id)
        del payload["notes"]

        response = client.post("/api/purchase-orders", json=payload)
        assert response.status_code == 201
        assert response.json()["notes"] is None

    def test_purchase_order_ids_are_unique(self, client):
        """Test that each purchase order gets its own id."""
        ids = _backlog_ids(client)
        first = client.post("/api/purchase-orders", json=_payload(ids[0])).json()
        second = client.post("/api/purchase-orders", json=_payload(ids[1])).json()
        assert first["id"] != second["id"]

    def test_create_purchase_order_unknown_backlog_item(self, client):
        """Test that a PO cannot be raised against a backlog item that doesn't exist."""
        response = client.post("/api/purchase-orders", json=_payload("nonexistent-999"))
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_duplicate_purchase_order(self, client):
        """Test that a backlog item can only have one purchase order."""
        backlog_id = _backlog_ids(client)[0]
        client.post("/api/purchase-orders", json=_payload(backlog_id))

        response = client.post("/api/purchase-orders", json=_payload(backlog_id))
        assert response.status_code == 409
        assert "already has" in response.json()["detail"].lower()

    @pytest.mark.parametrize("field,value", [
        ("quantity", 0),
        ("quantity", -5),
        ("unit_cost", -1),
        ("supplier_name", ""),
    ])
    def test_create_purchase_order_invalid_values(self, client, field, value):
        """Test request validation on quantity, unit cost and supplier."""
        backlog_id = _backlog_ids(client)[0]
        response = client.post("/api/purchase-orders", json=_payload(backlog_id, **{field: value}))
        assert response.status_code == 422

    def test_create_purchase_order_missing_fields(self, client):
        """Test that required fields are enforced."""
        response = client.post("/api/purchase-orders", json={"backlog_item_id": "1"})
        assert response.status_code == 422

    def test_get_purchase_order_by_backlog_item(self, client):
        """Test fetching the PO raised for a backlog item."""
        backlog_id = _backlog_ids(client)[0]
        created = client.post("/api/purchase-orders", json=_payload(backlog_id)).json()

        response = client.get(f"/api/purchase-orders/{backlog_id}")
        assert response.status_code == 200
        assert response.json() == created

    def test_get_purchase_order_none_exists(self, client):
        """Test that a backlog item without a PO returns 404."""
        backlog_id = _backlog_ids(client)[0]
        response = client.get(f"/api/purchase-orders/{backlog_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_backlog_flags_purchase_order(self, client):
        """Test that /api/backlog reports has_purchase_order once a PO exists."""
        backlog_id = _backlog_ids(client)[0]

        before = {b["id"]: b for b in client.get("/api/backlog").json()}
        assert before[backlog_id]["has_purchase_order"] is False

        client.post("/api/purchase-orders", json=_payload(backlog_id))

        after = {b["id"]: b for b in client.get("/api/backlog").json()}
        assert after[backlog_id]["has_purchase_order"] is True
        other_ids = [i for i in after if i != backlog_id]
        assert all(after[i]["has_purchase_order"] is False for i in other_ids)
