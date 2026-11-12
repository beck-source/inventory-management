"""
Tests for task and purchase order API endpoints.
"""
import pytest

import main


@pytest.fixture(autouse=True)
def reset_in_memory_state():
    """Tasks and purchase orders live in module-level memory; reset between tests."""
    original_pos = list(main.purchase_orders)
    main.tasks.clear()
    main.next_task_id = 1
    yield
    main.tasks.clear()
    main.next_task_id = 1
    # purchase_orders is shared with mock_data, so restore in place.
    main.purchase_orders[:] = original_pos


def _create_task(client, **overrides):
    payload = {"title": "Review stock", "priority": "high", "dueDate": "2026-12-01", **overrides}
    return client.post("/api/tasks", json=payload)


def _po_payload(backlog_item_id, **overrides):
    return {
        "backlog_item_id": backlog_item_id,
        "supplier_name": "Acme Supply",
        "quantity": 50,
        "unit_cost": 12.5,
        "expected_delivery_date": "2026-12-15",
        "notes": "Rush",
        **overrides,
    }


def _first_backlog_id(client):
    return client.get("/api/backlog").json()[0]["id"]


class TestTasksEndpoints:
    """Test suite for task endpoints."""

    def test_get_tasks_empty(self, client):
        """Test that no API tasks exist initially."""
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_task(self, client):
        """Test creating a task returns it as pending with a string id."""
        response = _create_task(client)
        assert response.status_code == 201

        task = response.json()
        assert task["id"] == "task-1"
        assert task["title"] == "Review stock"
        assert task["priority"] == "high"
        assert task["dueDate"] == "2026-12-01"
        assert task["status"] == "pending"

    def test_created_tasks_listed_newest_first(self, client):
        """Test that new tasks appear first in the list."""
        _create_task(client, title="First")
        _create_task(client, title="Second")

        titles = [t["title"] for t in client.get("/api/tasks").json()]
        assert titles == ["Second", "First"]

    def test_create_task_invalid_date(self, client):
        """Test that a non-ISO due date is rejected."""
        response = _create_task(client, dueDate="next week")
        assert response.status_code == 400
        assert "dueDate" in response.json()["detail"]

    def test_create_task_invalid_priority(self, client):
        """Test that an unknown priority is rejected."""
        response = _create_task(client, priority="urgent")
        assert response.status_code == 422

    def test_create_task_empty_title(self, client):
        """Test that an empty title is rejected."""
        response = _create_task(client, title="")
        assert response.status_code == 422

    def test_toggle_task(self, client):
        """Test that PATCH flips status between pending and completed."""
        task_id = _create_task(client).json()["id"]

        response = client.patch(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

        response = client.patch(f"/api/tasks/{task_id}")
        assert response.json()["status"] == "pending"

    def test_delete_task(self, client):
        """Test deleting a task removes it from the list."""
        task_id = _create_task(client).json()["id"]

        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert client.get("/api/tasks").json() == []

    def test_task_ids_not_reused_after_delete(self, client):
        """Test that ids keep increasing after a delete."""
        first_id = _create_task(client).json()["id"]
        client.delete(f"/api/tasks/{first_id}")

        assert _create_task(client).json()["id"] == "task-2"

    @pytest.mark.parametrize("method", ["patch", "delete"])
    def test_nonexistent_task(self, client, method):
        """Test toggling or deleting a missing task returns 404."""
        response = getattr(client, method)("/api/tasks/task-999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestPurchaseOrderEndpoints:
    """Test suite for purchase order endpoints."""

    def test_backlog_has_purchase_order_fields(self, client):
        """Test that backlog items expose PO status fields."""
        for item in client.get("/api/backlog").json():
            assert item["has_purchase_order"] is False
            assert item["purchase_order_id"] is None

    def test_create_purchase_order(self, client):
        """Test creating a PO returns the stored order."""
        backlog_id = _first_backlog_id(client)
        response = client.post("/api/purchase-orders", json=_po_payload(backlog_id))
        assert response.status_code == 201

        po = response.json()
        assert po["id"].startswith("PO-")
        assert po["backlog_item_id"] == backlog_id
        assert po["supplier_name"] == "Acme Supply"
        assert po["quantity"] == 50
        assert abs(po["unit_cost"] - 12.5) < 0.01
        assert po["status"] == "Pending"
        assert "-" in po["created_date"]

    def test_backlog_reflects_created_purchase_order(self, client):
        """Test that the backlog links to a newly created PO."""
        backlog_id = _first_backlog_id(client)
        po_id = client.post("/api/purchase-orders", json=_po_payload(backlog_id)).json()["id"]

        item = next(b for b in client.get("/api/backlog").json() if b["id"] == backlog_id)
        assert item["has_purchase_order"] is True
        assert item["purchase_order_id"] == po_id

    def test_get_purchase_order_by_backlog_item(self, client):
        """Test fetching a PO by its backlog item id."""
        backlog_id = _first_backlog_id(client)
        created = client.post("/api/purchase-orders", json=_po_payload(backlog_id)).json()

        response = client.get(f"/api/purchase-orders/{backlog_id}")
        assert response.status_code == 200
        assert response.json() == created

    def test_get_nonexistent_purchase_order(self, client):
        """Test fetching a PO for an item without one returns 404."""
        response = client.get("/api/purchase-orders/nonexistent-999")
        assert response.status_code == 404
        assert "detail" in response.json()

    def test_duplicate_purchase_order_rejected(self, client):
        """Test that a second PO for the same backlog item returns 409."""
        backlog_id = _first_backlog_id(client)
        client.post("/api/purchase-orders", json=_po_payload(backlog_id))

        response = client.post("/api/purchase-orders", json=_po_payload(backlog_id))
        assert response.status_code == 409

    def test_purchase_order_unknown_backlog_item(self, client):
        """Test that a PO for a missing backlog item returns 404."""
        response = client.post("/api/purchase-orders", json=_po_payload("nonexistent-999"))
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_purchase_order_invalid_date(self, client):
        """Test that a non-ISO delivery date is rejected."""
        backlog_id = _first_backlog_id(client)
        response = client.post(
            "/api/purchase-orders", json=_po_payload(backlog_id, expected_delivery_date="soon")
        )
        assert response.status_code == 400

    @pytest.mark.parametrize("field,value", [
        ("quantity", 0),
        ("unit_cost", 0),
        ("supplier_name", ""),
    ])
    def test_purchase_order_invalid_values(self, client, field, value):
        """Test that out-of-range PO fields are rejected."""
        backlog_id = _first_backlog_id(client)
        response = client.post("/api/purchase-orders", json=_po_payload(backlog_id, **{field: value}))
        assert response.status_code == 422
