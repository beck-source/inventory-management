"""
Tests for task and purchase order API endpoints.
"""
import pytest


def _unused_backlog_item_id(client):
    """Return a backlog item id that has no purchase order yet.

    Purchase orders cannot be deleted, and the list is shared for the whole
    test process, so each test picks an item that is still free.
    """
    for item in client.get("/api/backlog").json():
        if not item["has_purchase_order"]:
            return item["id"]
    pytest.skip("All backlog items already have purchase orders")


class TestTaskEndpoints:
    """Test suite for task endpoints."""

    def test_create_task_returns_201_with_pending_status(self, client):
        """Test creating a task returns it as pending."""
        response = client.post(
            "/api/tasks",
            json={"title": "Check reorder points", "priority": "high", "dueDate": "2026-12-01"},
        )
        assert response.status_code == 201

        task = response.json()
        assert task["title"] == "Check reorder points"
        assert task["priority"] == "high"
        assert task["dueDate"] == "2026-12-01"
        assert task["status"] == "pending"
        assert isinstance(task["id"], int)

        client.delete(f"/api/tasks/{task['id']}")

    def test_create_task_rejects_blank_title(self, client):
        """Test a whitespace-only title is rejected."""
        response = client.post(
            "/api/tasks",
            json={"title": "   ", "priority": "low", "dueDate": "2026-12-01"},
        )
        assert response.status_code == 400
        assert "Title" in response.json()["detail"]

    def test_create_task_rejects_unknown_priority(self, client):
        """Test a priority outside low/medium/high is rejected."""
        response = client.post(
            "/api/tasks",
            json={"title": "x", "priority": "urgent", "dueDate": "2026-12-01"},
        )
        assert response.status_code == 400

    def test_create_task_rejects_bad_due_date(self, client):
        """Test a due date that is not YYYY-MM-DD is rejected."""
        response = client.post(
            "/api/tasks",
            json={"title": "x", "priority": "low", "dueDate": "12/01/2026"},
        )
        assert response.status_code == 400
        assert "dueDate" in response.json()["detail"]

    def test_get_tasks_lists_newest_first(self, client):
        """Test the task list puts the most recently created task first."""
        first = client.post(
            "/api/tasks", json={"title": "first", "priority": "low", "dueDate": "2026-12-01"}
        ).json()
        second = client.post(
            "/api/tasks", json={"title": "second", "priority": "low", "dueDate": "2026-12-02"}
        ).json()

        ids = [task["id"] for task in client.get("/api/tasks").json()]
        assert ids.index(second["id"]) < ids.index(first["id"])

        client.delete(f"/api/tasks/{first['id']}")
        client.delete(f"/api/tasks/{second['id']}")

    def test_toggle_task_switches_status_both_ways(self, client):
        """Test PATCH flips a task between pending and completed."""
        task = client.post(
            "/api/tasks", json={"title": "toggle me", "priority": "medium", "dueDate": "2026-12-01"}
        ).json()

        toggled = client.patch(f"/api/tasks/{task['id']}")
        assert toggled.status_code == 200
        assert toggled.json()["status"] == "completed"

        toggled_back = client.patch(f"/api/tasks/{task['id']}")
        assert toggled_back.json()["status"] == "pending"

        client.delete(f"/api/tasks/{task['id']}")

    def test_delete_task_removes_it(self, client):
        """Test a deleted task no longer appears in the list."""
        task = client.post(
            "/api/tasks", json={"title": "delete me", "priority": "low", "dueDate": "2026-12-01"}
        ).json()

        response = client.delete(f"/api/tasks/{task['id']}")
        assert response.status_code == 200

        ids = [t["id"] for t in client.get("/api/tasks").json()]
        assert task["id"] not in ids

    def test_deleted_task_id_is_not_reused(self, client):
        """Test a new task never reuses the id of a deleted one."""
        first = client.post(
            "/api/tasks", json={"title": "a", "priority": "low", "dueDate": "2026-12-01"}
        ).json()
        client.delete(f"/api/tasks/{first['id']}")

        second = client.post(
            "/api/tasks", json={"title": "b", "priority": "low", "dueDate": "2026-12-01"}
        ).json()
        assert second["id"] != first["id"]

        client.delete(f"/api/tasks/{second['id']}")

    def test_toggle_missing_task_returns_404(self, client):
        """Test toggling an unknown task id returns 404."""
        response = client.patch("/api/tasks/999999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_missing_task_returns_404(self, client):
        """Test deleting an unknown task id returns 404."""
        response = client.delete("/api/tasks/999999")
        assert response.status_code == 404


class TestPurchaseOrderEndpoints:
    """Test suite for purchase order endpoints."""

    def test_create_purchase_order_returns_201(self, client):
        """Test a valid request creates a purchase order for the backlog item."""
        backlog_id = _unused_backlog_item_id(client)
        response = client.post(
            "/api/purchase-orders",
            json={
                "backlog_item_id": backlog_id,
                "supplier_name": "Acme Parts",
                "quantity": 25,
                "unit_cost": 12.5,
                "expected_delivery_date": "2026-12-20",
                "notes": "Rush",
            },
        )
        assert response.status_code == 201

        po = response.json()
        assert po["id"].startswith("PO-")
        assert po["backlog_item_id"] == backlog_id
        assert po["supplier_name"] == "Acme Parts"
        assert po["quantity"] == 25
        assert po["unit_cost"] == 12.5
        assert po["status"] == "Ordered"
        assert po["notes"] == "Rush"

    def test_created_purchase_order_is_visible_on_backlog(self, client):
        """Test the backlog reports has_purchase_order after a PO is created."""
        backlog_id = _unused_backlog_item_id(client)
        client.post(
            "/api/purchase-orders",
            json={
                "backlog_item_id": backlog_id,
                "supplier_name": "Acme Parts",
                "quantity": 1,
                "unit_cost": 1.0,
                "expected_delivery_date": "2026-12-20",
            },
        )

        item = next(i for i in client.get("/api/backlog").json() if i["id"] == backlog_id)
        assert item["has_purchase_order"] is True

    def test_get_purchase_order_by_backlog_item(self, client):
        """Test fetching the PO for a backlog item returns that PO."""
        backlog_id = _unused_backlog_item_id(client)
        created = client.post(
            "/api/purchase-orders",
            json={
                "backlog_item_id": backlog_id,
                "supplier_name": "Acme Parts",
                "quantity": 5,
                "unit_cost": 2.0,
                "expected_delivery_date": "2026-12-20",
            },
        ).json()

        response = client.get(f"/api/purchase-orders/{backlog_id}")
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_duplicate_purchase_order_returns_409(self, client):
        """Test a second PO for the same backlog item is rejected."""
        backlog_id = _unused_backlog_item_id(client)
        body = {
            "backlog_item_id": backlog_id,
            "supplier_name": "Acme Parts",
            "quantity": 5,
            "unit_cost": 2.0,
            "expected_delivery_date": "2026-12-20",
        }
        assert client.post("/api/purchase-orders", json=body).status_code == 201
        assert client.post("/api/purchase-orders", json=body).status_code == 409

    def test_purchase_order_for_unknown_backlog_item_returns_404(self, client):
        """Test a PO against a backlog item that does not exist is rejected."""
        response = client.post(
            "/api/purchase-orders",
            json={
                "backlog_item_id": "does-not-exist",
                "supplier_name": "Acme Parts",
                "quantity": 5,
                "unit_cost": 2.0,
                "expected_delivery_date": "2026-12-20",
            },
        )
        assert response.status_code == 404

    @pytest.mark.parametrize(
        "overrides",
        [
            {"supplier_name": "   "},
            {"quantity": 0},
            {"unit_cost": -1.0},
            {"expected_delivery_date": "20-12-2026"},
        ],
    )
    def test_invalid_purchase_order_is_rejected(self, client, overrides):
        """Test each invalid field value returns 400."""
        body = {
            "backlog_item_id": "1",
            "supplier_name": "Acme Parts",
            "quantity": 5,
            "unit_cost": 2.0,
            "expected_delivery_date": "2026-12-20",
        }
        body.update(overrides)
        response = client.post("/api/purchase-orders", json=body)
        assert response.status_code == 400

    def test_get_purchase_order_without_one_returns_404(self, client):
        """Test fetching a PO for a backlog item that has none returns 404."""
        response = client.get("/api/purchase-orders/does-not-exist")
        assert response.status_code == 404
