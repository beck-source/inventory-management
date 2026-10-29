"""
Tests for purchase order API endpoints.
"""
import pytest

import main


@pytest.fixture(autouse=True)
def clear_purchase_orders():
    """Purchase orders live in module-level memory, so reset them around every test."""
    main.purchase_orders.clear()
    yield
    main.purchase_orders.clear()


@pytest.fixture
def backlog_item_id(client):
    """ID of a real backlog item."""
    return client.get("/api/backlog").json()[0]["id"]


def build_payload(backlog_item_id, **overrides):
    payload = {
        "backlog_item_id": backlog_item_id,
        "supplier_name": "Acme Components",
        "quantity": 100,
        "unit_cost": 12.5,
        "expected_delivery_date": "2025-12-01",
        "notes": "Rush order",
    }
    payload.update(overrides)
    return payload


class TestPurchaseOrdersEndpoints:
    """Test suite for purchase-order-related endpoints."""

    def test_create_purchase_order(self, client, backlog_item_id):
        """Test creating a purchase order for a backlog item."""
        response = client.post("/api/purchase-orders", json=build_payload(backlog_item_id))
        assert response.status_code == 200

        po = response.json()
        assert po["id"].startswith("PO-")
        assert po["backlog_item_id"] == backlog_item_id
        assert po["supplier_name"] == "Acme Components"
        assert po["quantity"] == 100
        assert po["unit_cost"] == 12.5
        assert po["status"] == "Ordered"
        assert po["notes"] == "Rush order"
        assert "T" in po["created_date"]

    def test_create_purchase_order_without_notes(self, client, backlog_item_id):
        """Test that notes are optional."""
        payload = build_payload(backlog_item_id)
        del payload["notes"]

        response = client.post("/api/purchase-orders", json=payload)
        assert response.status_code == 200
        assert response.json()["notes"] is None

    def test_create_purchase_order_unknown_backlog_item(self, client):
        """Test that an unknown backlog item returns 404."""
        response = client.post("/api/purchase-orders", json=build_payload("nonexistent-999"))
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_purchase_order_duplicate(self, client, backlog_item_id):
        """Test that a backlog item can only have one purchase order."""
        client.post("/api/purchase-orders", json=build_payload(backlog_item_id))

        response = client.post("/api/purchase-orders", json=build_payload(backlog_item_id))
        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower()

    @pytest.mark.parametrize("overrides", [
        {"supplier_name": "   "},
        {"quantity": 0},
        {"quantity": -5},
        {"unit_cost": 0},
        {"unit_cost": -1.0},
    ])
    def test_create_purchase_order_invalid_values(self, client, backlog_item_id, overrides):
        """Test that blank suppliers and non-positive numbers are rejected."""
        response = client.post("/api/purchase-orders", json=build_payload(backlog_item_id, **overrides))
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_create_purchase_order_missing_fields(self, client):
        """Test that missing required fields fail validation."""
        response = client.post("/api/purchase-orders", json={"backlog_item_id": "1"})
        assert response.status_code == 422

    def test_get_purchase_order_by_backlog_item(self, client, backlog_item_id):
        """Test fetching the purchase order for a backlog item."""
        created = client.post("/api/purchase-orders", json=build_payload(backlog_item_id)).json()

        response = client.get(f"/api/purchase-orders/{backlog_item_id}")
        assert response.status_code == 200
        assert response.json() == created

    def test_get_nonexistent_purchase_order(self, client, backlog_item_id):
        """Test fetching a purchase order for a backlog item that has none."""
        response = client.get(f"/api/purchase-orders/{backlog_item_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_backlog_reports_purchase_order(self, client, backlog_item_id):
        """Test that /api/backlog flags an item once it has a purchase order."""
        def flag():
            items = client.get("/api/backlog").json()
            return next(i for i in items if i["id"] == backlog_item_id)["has_purchase_order"]

        assert flag() is False
        client.post("/api/purchase-orders", json=build_payload(backlog_item_id))
        assert flag() is True
