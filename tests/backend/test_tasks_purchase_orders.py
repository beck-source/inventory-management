"""
Tests for task and purchase order API endpoints.
"""
import pytest

import main
import mock_data


@pytest.fixture(autouse=True)
def reset_state():
    """Tasks and purchase orders live in module-level lists; reset them around each test."""
    main.tasks.clear()
    mock_data.purchase_orders.clear()
    yield
    main.tasks.clear()
    mock_data.purchase_orders.clear()


def make_task(client, **overrides):
    payload = {"title": "Check stock", "priority": "high", "dueDate": "2025-10-20", **overrides}
    response = client.post("/api/tasks", json=payload)
    assert response.status_code == 201
    return response.json()


def make_po(client, backlog_item_id="1", **overrides):
    payload = {
        "backlog_item_id": backlog_item_id,
        "supplier_name": "Acme Parts",
        "quantity": 350,
        "unit_cost": 12.5,
        "expected_delivery_date": "2025-11-01",
        **overrides,
    }
    return client.post("/api/purchase-orders", json=payload)


class TestTasksEndpoints:
    """Test suite for task CRUD endpoints."""

    def test_get_all_tasks_empty(self, client):
        """No tasks exist before any are created."""
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_task(self, client):
        """A created task is pending, has a string id, and echoes its fields."""
        task = make_task(client)
        assert task["status"] == "pending"
        assert isinstance(task["id"], str)
        assert task["title"] == "Check stock"
        assert task["priority"] == "high"
        assert task["dueDate"] == "2025-10-20"

    def test_get_tasks_newest_first(self, client):
        """Listed tasks are ordered newest first."""
        first = make_task(client, title="first")
        second = make_task(client, title="second")
        ids = [t["id"] for t in client.get("/api/tasks").json()]
        assert ids == [second["id"], first["id"]]

    def test_create_task_invalid_priority(self, client):
        """Unknown priorities are rejected."""
        response = client.post("/api/tasks", json={"title": "x", "priority": "urgent", "dueDate": "2025-10-20"})
        assert response.status_code == 422

    def test_create_task_empty_title(self, client):
        """Empty titles are rejected."""
        response = client.post("/api/tasks", json={"title": "", "dueDate": "2025-10-20"})
        assert response.status_code == 422

    def test_toggle_task(self, client):
        """PATCH flips pending -> completed -> pending."""
        task = make_task(client)
        assert client.patch(f"/api/tasks/{task['id']}").json()["status"] == "completed"
        assert client.patch(f"/api/tasks/{task['id']}").json()["status"] == "pending"

    def test_delete_task(self, client):
        """A deleted task no longer appears in the list."""
        task = make_task(client)
        response = client.delete(f"/api/tasks/{task['id']}")
        assert response.status_code == 200
        assert client.get("/api/tasks").json() == []

    def test_toggle_nonexistent_task(self, client):
        """Toggling an unknown task returns 404."""
        response = client.patch("/api/tasks/nonexistent-999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_nonexistent_task(self, client):
        """Deleting an unknown task returns 404."""
        response = client.delete("/api/tasks/nonexistent-999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestPurchaseOrderEndpoints:
    """Test suite for purchase order endpoints."""

    def test_create_purchase_order(self, client):
        """A created PO is pending and echoes the request fields."""
        response = make_po(client, notes="rush")
        assert response.status_code == 201
        po = response.json()
        assert po["id"].startswith("PO-")
        assert po["backlog_item_id"] == "1"
        assert po["status"] == "pending"
        assert po["quantity"] == 350
        assert abs(po["unit_cost"] - 12.5) < 0.01
        assert po["notes"] == "rush"
        assert "T" in po["created_date"]

    def test_get_purchase_order_by_backlog_item(self, client):
        """A PO can be looked up by its backlog item id."""
        created = make_po(client).json()
        response = client.get("/api/purchase-orders/1")
        assert response.status_code == 200
        assert response.json() == created

    def test_get_nonexistent_purchase_order(self, client):
        """Looking up a backlog item without a PO returns 404."""
        response = client.get("/api/purchase-orders/1")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_po_unknown_backlog_item(self, client):
        """Creating a PO for an unknown backlog item returns 404."""
        response = make_po(client, backlog_item_id="nonexistent-999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_duplicate_po(self, client):
        """A backlog item can only have one PO."""
        assert make_po(client).status_code == 201
        assert make_po(client).status_code == 409

    def test_backlog_reflects_purchase_order(self, client):
        """The backlog endpoint exposes the PO id on the matching item only."""
        po = make_po(client).json()
        backlog = {b["id"]: b for b in client.get("/api/backlog").json()}
        assert backlog["1"]["has_purchase_order"] is True
        assert backlog["1"]["purchase_order_id"] == po["id"]
        others = [b for bid, b in backlog.items() if bid != "1"]
        assert all(b["purchase_order_id"] is None and not b["has_purchase_order"] for b in others)
