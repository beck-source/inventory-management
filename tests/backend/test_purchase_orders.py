"""Tests for purchase order API endpoints."""
import pytest

from mock_data import purchase_orders


@pytest.fixture(autouse=True)
def isolate_purchase_orders():
    """Restore purchase orders after each test.

    `purchase_orders` is module-level state imported once per process, and
    `/api/backlog` derives its has_purchase_order flag from it, so an order left
    behind by one test would change what later tests see. Slice assignment
    restores the contents in place - rebinding would leave main.py on the old list.
    """
    saved = list(purchase_orders)
    yield
    purchase_orders[:] = saved


def valid_request(backlog_item_id="1", **overrides):
    """Build a well-formed create-purchase-order payload."""
    payload = {
        "backlog_item_id": backlog_item_id,
        "supplier_name": "Acme Supply",
        "quantity": 100,
        "unit_cost": 12.5,
        "expected_delivery_date": "2026-10-15",
        "notes": "Rush order"
    }
    payload.update(overrides)
    return payload


class TestCreatePurchaseOrder:
    """Test suite for creating purchase orders."""

    def test_create_returns_201_with_order(self, client):
        """Test that a valid request returns 201 and the created order."""
        response = client.post("/api/purchase-orders", json=valid_request())
        assert response.status_code == 201

        order = response.json()
        assert order["id"].startswith("PO-")
        assert order["backlog_item_id"] == "1"
        assert order["supplier_name"] == "Acme Supply"
        assert order["quantity"] == 100
        assert order["status"] == "Ordered"
        assert order["created_date"]

    def test_supplier_name_is_trimmed(self, client):
        """Test that surrounding whitespace is stripped from the supplier name."""
        response = client.post(
            "/api/purchase-orders",
            json=valid_request(supplier_name="  Acme Supply  ")
        )
        assert response.json()["supplier_name"] == "Acme Supply"

    def test_unknown_backlog_item_is_rejected(self, client):
        """Test that an unknown backlog item returns 404."""
        response = client.post(
            "/api/purchase-orders",
            json=valid_request(backlog_item_id="DOES-NOT-EXIST")
        )
        assert response.status_code == 404

    def test_duplicate_purchase_order_is_rejected(self, client):
        """Test that a backlog item cannot have two purchase orders."""
        assert client.post("/api/purchase-orders", json=valid_request("2")).status_code == 201

        response = client.post("/api/purchase-orders", json=valid_request("2"))
        assert response.status_code == 400

    def test_non_positive_quantity_is_rejected(self, client):
        """Test that a zero or negative quantity returns 400."""
        for quantity in [0, -10]:
            response = client.post("/api/purchase-orders", json=valid_request(quantity=quantity))
            assert response.status_code == 400, f"Quantity {quantity} should be rejected"

    def test_negative_unit_cost_is_rejected(self, client):
        """Test that a negative unit cost returns 400."""
        response = client.post("/api/purchase-orders", json=valid_request(unit_cost=-1))
        assert response.status_code == 400

    def test_blank_supplier_name_is_rejected(self, client):
        """Test that a blank supplier name returns 400."""
        response = client.post("/api/purchase-orders", json=valid_request(supplier_name="   "))
        assert response.status_code == 400


class TestGetPurchaseOrder:
    """Test suite for retrieving purchase orders."""

    def test_get_returns_the_created_order(self, client):
        """Test that a created order can be retrieved by backlog item id."""
        created = client.post("/api/purchase-orders", json=valid_request("3")).json()

        response = client.get("/api/purchase-orders/3")
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_get_unknown_backlog_item_returns_404(self, client):
        """Test that a backlog item with no purchase order returns 404."""
        response = client.get("/api/purchase-orders/DOES-NOT-EXIST")
        assert response.status_code == 404


class TestBacklogReflectsPurchaseOrders:
    """Test suite for the backlog endpoint's purchase order fields."""

    def test_backlog_exposes_both_flag_and_id(self, client):
        """Test that every backlog item carries has_purchase_order and purchase_order_id."""
        for item in client.get("/api/backlog").json():
            assert "has_purchase_order" in item
            assert "purchase_order_id" in item
            # The id is what the client branches on, so the two must agree.
            assert item["has_purchase_order"] == (item["purchase_order_id"] is not None)

    def test_creating_an_order_flips_the_backlog_flag(self, client):
        """Test that a new purchase order is reflected on the backlog item."""
        before = next(i for i in client.get("/api/backlog").json() if i["id"] == "4")
        assert before["has_purchase_order"] is False
        assert before["purchase_order_id"] is None

        created = client.post("/api/purchase-orders", json=valid_request("4")).json()

        after = next(i for i in client.get("/api/backlog").json() if i["id"] == "4")
        assert after["has_purchase_order"] is True
        assert after["purchase_order_id"] == created["id"]
