"""
Tests for task and purchase order API endpoints.
"""
import pytest

from mock_data import purchase_orders, tasks


@pytest.fixture(autouse=True)
def clear_in_memory_state():
    """Tasks and purchase orders live in module globals, so isolate every test from the last."""
    tasks.clear()
    purchase_orders.clear()
    yield
    tasks.clear()
    purchase_orders.clear()


def create_task(client, **overrides):
    payload = {"title": "Review Q4 stock", "priority": "high", "dueDate": "2026-11-01", **overrides}
    return client.post("/api/tasks", json=payload)


def po_payload(**overrides):
    return {
        "backlog_item_id": "1",
        "supplier_name": "Acme Filters",
        "quantity": 350,
        "unit_cost": 12.5,
        "expected_delivery_date": "2026-11-15",
        **overrides
    }


class TestTaskEndpoints:
    """Test suite for task endpoints."""

    def test_get_tasks_empty(self, client):
        """Test that no tasks exist before any are created."""
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_task(self, client):
        """Test creating a task returns it as pending and lists it."""
        response = create_task(client)
        assert response.status_code == 201

        task = response.json()
        assert task["title"] == "Review Q4 stock"
        assert task["priority"] == "high"
        assert task["dueDate"] == "2026-11-01"
        assert task["status"] == "pending"
        assert task["id"].startswith("api-")

        listed = client.get("/api/tasks").json()
        assert [t["id"] for t in listed] == [task["id"]]

    def test_create_task_defaults_priority(self, client):
        """Test that priority defaults to medium."""
        response = client.post("/api/tasks", json={"title": "Call supplier", "dueDate": "2026-11-01"})
        assert response.status_code == 201
        assert response.json()["priority"] == "medium"

    @pytest.mark.parametrize("overrides", [
        {"title": ""},
        {"priority": "urgent"},
        {"dueDate": "not-a-date"},
    ])
    def test_create_task_invalid_input(self, client, overrides):
        """Test that invalid task input is rejected."""
        response = create_task(client, **overrides)
        assert response.status_code == 422

    def test_toggle_task(self, client):
        """Test that toggling flips status both ways."""
        task_id = create_task(client).json()["id"]

        response = client.patch(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

        response = client.patch(f"/api/tasks/{task_id}")
        assert response.json()["status"] == "pending"

    def test_delete_task(self, client):
        """Test deleting a task removes it."""
        task_id = create_task(client).json()["id"]

        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["id"] == task_id
        assert client.get("/api/tasks").json() == []

    def test_task_ids_not_reused_after_delete(self, client):
        """Test that deleting a task never lets its id be handed out again."""
        first = create_task(client).json()["id"]
        second = create_task(client).json()["id"]
        client.delete(f"/api/tasks/{first}")

        third = create_task(client).json()["id"]
        assert third not in (first, second)

    @pytest.mark.parametrize("method", ["patch", "delete"])
    def test_nonexistent_task(self, client, method):
        """Test that toggling or deleting a missing task returns 404."""
        response = getattr(client, method)("/api/tasks/api-999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestPurchaseOrderEndpoints:
    """Test suite for purchase order endpoints."""

    def test_create_purchase_order(self, client):
        """Test creating a purchase order against a backlog item."""
        response = client.post("/api/purchase-orders", json=po_payload())
        assert response.status_code == 201

        po = response.json()
        assert po["backlog_item_id"] == "1"
        assert po["supplier_name"] == "Acme Filters"
        assert po["quantity"] == 350
        assert po["unit_cost"] == 12.5
        assert po["expected_delivery_date"] == "2026-11-15"
        assert po["status"] == "pending"
        assert "T" in po["created_date"]

    def test_get_purchase_order_by_backlog_item(self, client):
        """Test fetching the purchase order for a backlog item."""
        created = client.post("/api/purchase-orders", json=po_payload()).json()

        response = client.get("/api/purchase-orders/1")
        assert response.status_code == 200
        assert response.json() == created

    def test_get_nonexistent_purchase_order(self, client):
        """Test that a backlog item with no purchase order returns 404."""
        response = client.get("/api/purchase-orders/1")
        assert response.status_code == 404
        assert "detail" in response.json()

    def test_backlog_reports_purchase_order(self, client):
        """Test that the backlog flags the item a purchase order was raised for."""
        before = {b["id"]: b for b in client.get("/api/backlog").json()}
        assert before["1"]["has_purchase_order"] is False
        assert before["1"]["purchase_order_id"] is None

        po_id = client.post("/api/purchase-orders", json=po_payload()).json()["id"]

        after = {b["id"]: b for b in client.get("/api/backlog").json()}
        assert after["1"]["has_purchase_order"] is True
        assert after["1"]["purchase_order_id"] == po_id
        assert after["2"]["purchase_order_id"] is None

    def test_duplicate_purchase_order_rejected(self, client):
        """Test that a second purchase order for the same backlog item is rejected."""
        client.post("/api/purchase-orders", json=po_payload())

        response = client.post("/api/purchase-orders", json=po_payload())
        assert response.status_code == 400
        assert len(purchase_orders) == 1

    def test_purchase_order_unknown_backlog_item(self, client):
        """Test that a purchase order for a missing backlog item returns 404."""
        response = client.post("/api/purchase-orders", json=po_payload(backlog_item_id="999"))
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.parametrize("overrides", [
        {"supplier_name": ""},
        {"quantity": 0},
        {"unit_cost": -1},
        {"expected_delivery_date": "soon"},
    ])
    def test_purchase_order_invalid_input(self, client, overrides):
        """Test that invalid purchase order input is rejected."""
        response = client.post("/api/purchase-orders", json=po_payload(**overrides))
        assert response.status_code == 422
