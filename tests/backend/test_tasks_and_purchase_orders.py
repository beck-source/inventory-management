"""
Tests for tasks and purchase orders API endpoints.

NOTE: The backend uses MODULE-LEVEL in-memory stores (tasks_store,
purchase_orders) that persist across tests within the same process. These
tests therefore avoid asserting absolute counts from an assumed-empty start.
Instead they capture counts before/after a mutation and assert the delta, and
they reference resources by the IDs they create so the tests remain
order-independent.
"""
import pytest


class TestTasksEndpoints:
    """Test suite for /api/tasks endpoints."""

    def _create_task(self, client, title="Reconcile inventory counts",
                     priority="high", due_date="2026-07-01"):
        """Helper: create a task and return the parsed response."""
        payload = {
            "title": title,
            "priority": priority,
            "dueDate": due_date,
        }
        response = client.post("/api/tasks", json=payload)
        return response, payload

    def test_get_all_tasks_returns_list(self, client):
        """Test that getting all tasks returns a JSON list."""
        response = client.get("/api/tasks")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_create_task_returns_201_and_string_id(self, client):
        """Test creating a task returns 201 with a non-numeric string id."""
        response, payload = self._create_task(client)
        assert response.status_code == 201

        task = response.json()

        # id must be a string and NOT purely numeric (e.g. "task-...")
        assert "id" in task
        assert isinstance(task["id"], str)
        assert not task["id"].isdigit(), \
            f"Task id should not be purely numeric, got {task['id']!r}"
        assert task["id"].startswith("task-")

    def test_create_task_default_status_pending(self, client):
        """Test that a newly created task has status 'pending'."""
        response, payload = self._create_task(client)
        assert response.status_code == 201

        task = response.json()
        assert task["status"] == "pending"

    def test_create_task_echoes_payload(self, client):
        """Test that the created task echoes title, priority, and dueDate."""
        response, payload = self._create_task(
            client,
            title="Audit supplier contracts",
            priority="medium",
            due_date="2026-08-15",
        )
        assert response.status_code == 201

        task = response.json()
        assert task["title"] == payload["title"]
        assert task["priority"] == payload["priority"]
        assert task["dueDate"] == payload["dueDate"]

    def test_created_task_appears_in_list_newest_first(self, client):
        """Test that a newly created task appears in GET and before older ones."""
        # Create an older task first, then a newer one.
        older_resp, _ = self._create_task(client, title="Older task")
        assert older_resp.status_code == 201
        older_id = older_resp.json()["id"]

        newer_resp, _ = self._create_task(client, title="Newer task")
        assert newer_resp.status_code == 201
        newer_id = newer_resp.json()["id"]

        response = client.get("/api/tasks")
        assert response.status_code == 200
        data = response.json()

        ids = [t["id"] for t in data]
        # Both tasks must be present.
        assert older_id in ids
        assert newer_id in ids

        # Newest-first ordering: the newer task appears before the older one.
        assert ids.index(newer_id) < ids.index(older_id)

    def test_create_task_increases_count_by_one(self, client):
        """Test the store grows by exactly one task (delta, not absolute)."""
        before = len(client.get("/api/tasks").json())

        response, _ = self._create_task(client)
        assert response.status_code == 201

        after = len(client.get("/api/tasks").json())
        assert after == before + 1

    def test_patch_task_toggles_status(self, client):
        """Test PATCH toggles a task status pending -> completed and back."""
        create_resp, _ = self._create_task(client)
        assert create_resp.status_code == 201
        task = create_resp.json()
        task_id = task["id"]
        assert task["status"] == "pending"

        # Toggle to completed.
        response = client.patch(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

        # Toggle back to pending.
        response = client.patch(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "pending"

    def test_patch_nonexistent_task_returns_404(self, client):
        """Test PATCH on an unknown task id returns 404."""
        response = client.patch("/api/tasks/task-nonexistent-999")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_delete_task_returns_204_and_removes_it(self, client):
        """Test DELETE returns 204 and the task no longer appears in GET."""
        create_resp, _ = self._create_task(client)
        assert create_resp.status_code == 201
        task_id = create_resp.json()["id"]

        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 204

        # Task should no longer be present.
        ids = [t["id"] for t in client.get("/api/tasks").json()]
        assert task_id not in ids

    def test_delete_nonexistent_task_returns_404(self, client):
        """Test DELETE on an unknown task id returns 404."""
        response = client.delete("/api/tasks/task-nonexistent-999")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()


class TestPurchaseOrdersEndpoints:
    """Test suite for /api/purchase-orders endpoints."""

    def _create_purchase_order(self, client, backlog_item_id="backlog-test-1"):
        """Helper: create a purchase order and return the response + payload."""
        payload = {
            "backlog_item_id": backlog_item_id,
            "supplier_name": "Acme Components Ltd",
            "quantity": 250,
            "unit_cost": 12.75,
            "expected_delivery_date": "2026-07-30",
            "notes": "Expedited order for backlog clearance",
        }
        response = client.post("/api/purchase-orders", json=payload)
        return response, payload

    def test_create_purchase_order_returns_201(self, client):
        """Test creating a purchase order returns 201 with a generated id."""
        response, payload = self._create_purchase_order(
            client, backlog_item_id="backlog-create-201"
        )
        assert response.status_code == 201

        po = response.json()
        assert "id" in po
        assert po["id"]  # non-empty generated id

    def test_create_purchase_order_default_status_pending(self, client):
        """Test a newly created purchase order has status 'Pending'."""
        response, _ = self._create_purchase_order(
            client, backlog_item_id="backlog-status-pending"
        )
        assert response.status_code == 201

        po = response.json()
        assert po["status"] == "Pending"

    def test_create_purchase_order_echoes_payload(self, client):
        """Test the created PO echoes backlog_item_id and payload fields."""
        response, payload = self._create_purchase_order(
            client, backlog_item_id="backlog-echo-fields"
        )
        assert response.status_code == 201

        po = response.json()
        assert po["backlog_item_id"] == payload["backlog_item_id"]
        assert po["supplier_name"] == payload["supplier_name"]
        assert po["quantity"] == payload["quantity"]
        assert po["unit_cost"] == payload["unit_cost"]
        assert po["expected_delivery_date"] == payload["expected_delivery_date"]
        assert po["notes"] == payload["notes"]

    def test_get_purchase_order_by_backlog_item_id(self, client):
        """Test fetching a PO by its backlog_item_id returns the created PO."""
        backlog_item_id = "backlog-get-by-id"
        create_resp, payload = self._create_purchase_order(
            client, backlog_item_id=backlog_item_id
        )
        assert create_resp.status_code == 201
        created_id = create_resp.json()["id"]

        response = client.get(f"/api/purchase-orders/{backlog_item_id}")
        assert response.status_code == 200

        po = response.json()
        assert po["backlog_item_id"] == backlog_item_id
        assert po["id"] == created_id
        assert po["supplier_name"] == payload["supplier_name"]

    def test_get_purchase_order_for_unknown_backlog_item_returns_404(self, client):
        """Test fetching a PO for a backlog_item_id with no PO returns 404."""
        response = client.get("/api/purchase-orders/backlog-nonexistent-999")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        # The 404 status is the contract; assert the message references the
        # missing purchase order without pinning exact wording.
        assert "purchase order" in data["detail"].lower()
