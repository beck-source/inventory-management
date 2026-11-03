"""
Tests for the purchase order endpoints and the purchase_order_id field on the backlog.
"""
import pytest

from mock_data import purchase_orders


@pytest.fixture(autouse=True)
def clear_purchase_orders():
    """Purchase orders live in shared in-memory state, so reset around each test."""
    purchase_orders.clear()
    yield
    purchase_orders.clear()


def valid_request(backlog_item_id="1", **overrides):
    body = {
        "backlog_item_id": backlog_item_id,
        "supplier_name": "Acme Supply",
        "quantity": 350,
        "unit_cost": 12.5,
        "expected_delivery_date": "2025-11-20",
        "notes": "Rush order",
    }
    body.update(overrides)
    return body


class TestCreatePurchaseOrder:
    def test_create_returns_201_and_pending_po(self, client):
        response = client.post("/api/purchase-orders", json=valid_request())
        assert response.status_code == 201
        po = response.json()
        assert po["id"] == "PO-0001"
        assert po["backlog_item_id"] == "1"
        assert po["status"] == "Pending"
        assert po["supplier_name"] == "Acme Supply"
        assert po["notes"] == "Rush order"

    def test_notes_are_optional(self, client):
        body = valid_request()
        del body["notes"]
        response = client.post("/api/purchase-orders", json=body)
        assert response.status_code == 201
        assert response.json()["notes"] is None

    def test_unknown_backlog_item_returns_404(self, client):
        response = client.post("/api/purchase-orders", json=valid_request("does-not-exist"))
        assert response.status_code == 404

    def test_second_po_for_same_item_returns_409(self, client):
        assert client.post("/api/purchase-orders", json=valid_request()).status_code == 201
        assert client.post("/api/purchase-orders", json=valid_request()).status_code == 409

    @pytest.mark.parametrize("overrides", [
        {"supplier_name": "   "},
        {"quantity": 0},
        {"quantity": -5},
        {"unit_cost": -0.01},
        {"expected_delivery_date": "20/11/2025"},
    ])
    def test_invalid_input_returns_400(self, client, overrides):
        response = client.post("/api/purchase-orders", json=valid_request(**overrides))
        assert response.status_code == 400
        assert purchase_orders == []

    def test_missing_field_returns_422(self, client):
        body = valid_request()
        del body["supplier_name"]
        assert client.post("/api/purchase-orders", json=body).status_code == 422


class TestGetPurchaseOrder:
    def test_get_by_backlog_item(self, client):
        created = client.post("/api/purchase-orders", json=valid_request()).json()
        response = client.get("/api/purchase-orders/1")
        assert response.status_code == 200
        assert response.json() == created

    def test_get_without_po_returns_404(self, client):
        assert client.get("/api/purchase-orders/1").status_code == 404


class TestBacklogPurchaseOrderLink:
    def test_backlog_has_no_po_by_default(self, client):
        for item in client.get("/api/backlog").json():
            assert item["has_purchase_order"] is False
            assert item["purchase_order_id"] is None

    def test_backlog_exposes_po_id_after_creation(self, client):
        po = client.post("/api/purchase-orders", json=valid_request("2")).json()
        items = {i["id"]: i for i in client.get("/api/backlog").json()}
        assert items["2"]["has_purchase_order"] is True
        assert items["2"]["purchase_order_id"] == po["id"]
        assert items["1"]["purchase_order_id"] is None
