"""
Tests for Purchase Order and Task API endpoints.
"""
import pytest

import mock_data


@pytest.fixture(autouse=True)
def isolated_state():
    """Start each test with no purchase orders or tasks, then restore in place
    (main.py holds references to these same list objects)."""
    saved_pos = list(mock_data.purchase_orders)
    saved_tasks = list(mock_data.tasks)
    mock_data.purchase_orders.clear()
    mock_data.tasks.clear()
    yield
    mock_data.purchase_orders[:] = saved_pos
    mock_data.tasks[:] = saved_tasks


@pytest.fixture
def backlog_item_id(client):
    return client.get("/api/backlog").json()[0]["id"]


@pytest.fixture
def po_payload(backlog_item_id):
    return {
        "backlog_item_id": backlog_item_id,
        "supplier_name": "Acme Components",
        "quantity": 50,
        "unit_cost": 12.5,
        "expected_delivery_date": "2025-11-01",
        "notes": "Expedite",
    }


class TestPurchaseOrderEndpoints:
    """Test suite for /api/purchase-orders and backlog PO linkage."""

    def test_create_purchase_order(self, client, po_payload):
        """Test creating a PO returns 201 with server-generated fields."""
        response = client.post("/api/purchase-orders", json=po_payload)
        assert response.status_code == 201

        po = response.json()
        assert po["id"].startswith("PO-")
        assert po["status"] == "Pending"
        assert "T" in po["created_date"]
        for key in ["backlog_item_id", "supplier_name", "quantity", "unit_cost", "expected_delivery_date", "notes"]:
            assert po[key] == po_payload[key]

    def test_get_purchase_order_by_backlog_item(self, client, po_payload):
        """Test fetching a created PO by its backlog item id."""
        created = client.post("/api/purchase-orders", json=po_payload).json()

        response = client.get(f"/api/purchase-orders/{po_payload['backlog_item_id']}")
        assert response.status_code == 200
        assert response.json() == created

    def test_backlog_reflects_purchase_order(self, client, po_payload):
        """Test backlog items expose has_purchase_order and purchase_order_id."""
        before = {b["id"]: b for b in client.get("/api/backlog").json()}
        target = before[po_payload["backlog_item_id"]]
        assert target["has_purchase_order"] is False
        assert target["purchase_order_id"] is None

        created = client.post("/api/purchase-orders", json=po_payload).json()

        after = {b["id"]: b for b in client.get("/api/backlog").json()}
        assert after[po_payload["backlog_item_id"]]["has_purchase_order"] is True
        assert after[po_payload["backlog_item_id"]]["purchase_order_id"] == created["id"]
        # Other items are unaffected
        for item_id, item in after.items():
            if item_id != po_payload["backlog_item_id"]:
                assert item["has_purchase_order"] is False

    def test_get_nonexistent_purchase_order(self, client, backlog_item_id):
        """Test 404 when a backlog item has no PO."""
        response = client.get(f"/api/purchase-orders/{backlog_item_id}")
        assert response.status_code == 404
        assert "detail" in response.json()

    def test_create_purchase_order_unknown_backlog_item(self, client, po_payload):
        """Test 404 when the backlog item doesn't exist."""
        po_payload["backlog_item_id"] = "nonexistent-999"
        response = client.post("/api/purchase-orders", json=po_payload)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_duplicate_purchase_order(self, client, po_payload):
        """Test 409 when the backlog item already has a PO."""
        assert client.post("/api/purchase-orders", json=po_payload).status_code == 201
        response = client.post("/api/purchase-orders", json=po_payload)
        assert response.status_code == 409
        assert len(mock_data.purchase_orders) == 1

    @pytest.mark.parametrize("field,value", [
        ("quantity", 0),
        ("quantity", -5),
        ("unit_cost", -1),
        ("supplier_name", ""),
        ("expected_delivery_date", "next week"),
    ])
    def test_create_purchase_order_validation(self, client, po_payload, field, value):
        """Test invalid input is rejected with 422."""
        po_payload[field] = value
        response = client.post("/api/purchase-orders", json=po_payload)
        assert response.status_code == 422
        assert mock_data.purchase_orders == []


class TestTaskEndpoints:
    """Test suite for /api/tasks."""

    def _create(self, client, title="Check stock", priority="high", due="2025-10-20"):
        return client.post("/api/tasks", json={"title": title, "priority": priority, "dueDate": due})

    def test_get_all_tasks_empty(self, client):
        """Test getting tasks when none exist."""
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_task(self, client):
        """Test creating a task returns 201 with a string id and pending status."""
        response = self._create(client)
        assert response.status_code == 201

        task = response.json()
        assert task == {
            "id": "TASK-1",
            "title": "Check stock",
            "priority": "high",
            "dueDate": "2025-10-20",
            "status": "pending",
        }
        # String id avoids collisions with the numeric mock-task ids on the client
        assert isinstance(task["id"], str)

    def test_get_tasks_newest_first(self, client):
        """Test tasks are listed newest first, matching the client's unshift()."""
        self._create(client, title="first")
        self._create(client, title="second")
        titles = [t["title"] for t in client.get("/api/tasks").json()]
        assert titles == ["second", "first"]

    def test_toggle_task(self, client):
        """Test PATCH flips status pending -> completed -> pending."""
        task_id = self._create(client).json()["id"]

        response = client.patch(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

        assert client.patch(f"/api/tasks/{task_id}").json()["status"] == "pending"

    def test_delete_task(self, client):
        """Test deleting a task removes it."""
        task_id = self._create(client).json()["id"]

        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["id"] == task_id
        assert client.get("/api/tasks").json() == []

    def test_task_ids_unique_after_delete(self, client):
        """Test ids are not reused after a deletion."""
        first = self._create(client).json()["id"]
        second = self._create(client).json()["id"]
        client.delete(f"/api/tasks/{first}")
        third = self._create(client).json()["id"]
        assert third not in (first, second)

    @pytest.mark.parametrize("method", ["patch", "delete"])
    def test_nonexistent_task(self, client, method):
        """Test 404 for toggling or deleting a missing task."""
        response = getattr(client, method)("/api/tasks/TASK-999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.parametrize("payload", [
        {"title": "", "priority": "high", "dueDate": "2025-10-20"},
        {"title": "x", "priority": "urgent", "dueDate": "2025-10-20"},
        {"title": "x", "priority": "low", "dueDate": "tomorrow"},
        {"title": "x", "priority": "low"},
    ])
    def test_create_task_validation(self, client, payload):
        """Test invalid task input is rejected with 422."""
        response = client.post("/api/tasks", json=payload)
        assert response.status_code == 422
        assert mock_data.tasks == []
