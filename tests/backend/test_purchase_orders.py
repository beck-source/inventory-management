"""
Tests for purchase order API endpoints.
"""
import pytest


def _valid_backlog_item_id(client):
    """Return the id of a backlog item that has no purchase order yet."""
    response = client.get("/api/backlog")
    items = response.json()
    assert len(items) > 0

    available = [item for item in items if not item["has_purchase_order"]]
    assert len(available) > 0, "Expected at least one backlog item without a purchase order"
    return available[0]["id"]


def _po_payload(backlog_item_id, **overrides):
    """Build a valid CreatePurchaseOrderRequest body."""
    payload = {
        "backlog_item_id": backlog_item_id,
        "supplier_name": "Acme Components",
        "quantity": 350,
        "unit_cost": 6.75,
        "expected_delivery_date": "2026-08-15",
        "notes": "Rush order"
    }
    payload.update(overrides)
    return payload


class TestPurchaseOrderEndpoints:
    """Test suite for purchase-order-related endpoints."""

    def test_create_purchase_order(self, client):
        """Test creating a purchase order for a backlog item."""
        backlog_item_id = _valid_backlog_item_id(client)

        response = client.post("/api/purchase-orders", json=_po_payload(backlog_item_id))
        assert response.status_code == 200

        po = response.json()
        assert "id" in po
        assert po["backlog_item_id"] == backlog_item_id
        assert po["supplier_name"] == "Acme Components"
        assert po["quantity"] == 350
        assert po["unit_cost"] == 6.75
        assert po["expected_delivery_date"] == "2026-08-15"
        assert po["notes"] == "Rush order"
        # Status and created_date are server-assigned, not client-supplied
        assert po["status"] == "Pending"
        assert "created_date" in po

    def test_create_purchase_order_without_notes(self, client):
        """Test that notes are optional."""
        backlog_item_id = _valid_backlog_item_id(client)
        payload = _po_payload(backlog_item_id)
        del payload["notes"]

        response = client.post("/api/purchase-orders", json=payload)
        assert response.status_code == 200
        assert response.json()["notes"] is None

    def test_get_purchase_order_by_backlog_item(self, client):
        """Test retrieving a purchase order by its backlog item id."""
        backlog_item_id = _valid_backlog_item_id(client)
        created = client.post(
            "/api/purchase-orders", json=_po_payload(backlog_item_id)
        ).json()

        response = client.get(f"/api/purchase-orders/{backlog_item_id}")
        assert response.status_code == 200

        po = response.json()
        assert po["id"] == created["id"]
        assert po["backlog_item_id"] == backlog_item_id

    def test_get_purchase_order_for_backlog_item_without_one(self, client):
        """Test that a backlog item with no purchase order returns 404."""
        backlog_item_id = _valid_backlog_item_id(client)

        response = client.get(f"/api/purchase-orders/{backlog_item_id}")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "no purchase order found" in data["detail"].lower()

    def test_create_purchase_order_nonexistent_backlog_item(self, client):
        """Test creating a purchase order for a backlog item that doesn't exist."""
        response = client.post(
            "/api/purchase-orders", json=_po_payload("nonexistent-backlog-999")
        )
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_create_duplicate_purchase_order(self, client):
        """Test that a backlog item cannot have two purchase orders."""
        backlog_item_id = _valid_backlog_item_id(client)
        client.post("/api/purchase-orders", json=_po_payload(backlog_item_id))

        response = client.post(
            "/api/purchase-orders",
            json=_po_payload(backlog_item_id, supplier_name="Second Supplier")
        )
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert "already has a purchase order" in data["detail"].lower()

    @pytest.mark.parametrize("quantity", [0, -5])
    def test_create_purchase_order_invalid_quantity(self, client, quantity):
        """Test that a non-positive quantity is rejected."""
        backlog_item_id = _valid_backlog_item_id(client)

        response = client.post(
            "/api/purchase-orders", json=_po_payload(backlog_item_id, quantity=quantity)
        )
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert "quantity" in data["detail"].lower()

    def test_create_purchase_order_negative_unit_cost(self, client):
        """Test that a negative unit cost is rejected."""
        backlog_item_id = _valid_backlog_item_id(client)

        response = client.post(
            "/api/purchase-orders", json=_po_payload(backlog_item_id, unit_cost=-1.0)
        )
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert "unit cost" in data["detail"].lower()

    def test_create_purchase_order_missing_field(self, client):
        """Test that a missing required field fails validation."""
        response = client.post(
            "/api/purchase-orders", json={"supplier_name": "Incomplete Supplier"}
        )
        assert response.status_code == 422

    def test_backlog_reflects_created_purchase_order(self, client):
        """Test that the backlog endpoint exposes the new purchase order state."""
        backlog_item_id = _valid_backlog_item_id(client)
        created = client.post(
            "/api/purchase-orders", json=_po_payload(backlog_item_id)
        ).json()

        response = client.get("/api/backlog")
        assert response.status_code == 200

        item = next(i for i in response.json() if i["id"] == backlog_item_id)
        # Dashboard.vue keys the Create PO / View PO button off purchase_order_id
        assert item["has_purchase_order"] is True
        assert item["purchase_order_id"] == created["id"]

    def test_backlog_purchase_order_fields_default(self, client):
        """Test that backlog items without a purchase order report empty PO state."""
        response = client.get("/api/backlog")
        assert response.status_code == 200

        for item in response.json():
            if not item["has_purchase_order"]:
                assert item["purchase_order_id"] is None

    def test_purchase_order_types(self, client):
        """Test that purchase order numeric fields have proper types."""
        backlog_item_id = _valid_backlog_item_id(client)
        po = client.post(
            "/api/purchase-orders", json=_po_payload(backlog_item_id)
        ).json()

        assert isinstance(po["id"], str)
        assert isinstance(po["quantity"], int)
        assert isinstance(po["unit_cost"], (int, float))
        assert po["quantity"] > 0
        assert po["unit_cost"] >= 0

    def test_purchase_order_created_date_format(self, client):
        """Test that created_date is an ISO-style YYYY-MM-DD string."""
        backlog_item_id = _valid_backlog_item_id(client)
        po = client.post(
            "/api/purchase-orders", json=_po_payload(backlog_item_id)
        ).json()

        created_date = po["created_date"]
        assert len(created_date) == 10
        assert created_date.count("-") == 2
