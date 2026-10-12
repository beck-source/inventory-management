"""
Tests for tasks API endpoints (GET/POST/PATCH/DELETE /api/tasks).

Tasks live in a mutable in-memory store, so each test creates the tasks it
needs and cleans them up to stay independent of ordering and seed state.
"""
import pytest


class TestTasksEndpoints:
    """Test suite for task-related endpoints."""

    def _create_task(self, client, title="Test task", priority="medium",
                     due_date="2025-08-15"):
        """Helper: create a task and return its JSON body."""
        response = client.post(
            "/api/tasks",
            json={"title": title, "priority": priority, "dueDate": due_date},
        )
        assert response.status_code == 201
        return response.json()

    def test_get_all_tasks(self, client):
        """Test getting all tasks returns a well-formed list."""
        response = client.get("/api/tasks")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        # Verify structure of every task
        for task in data:
            assert "id" in task
            assert "title" in task
            assert "priority" in task
            assert "dueDate" in task
            assert "status" in task
            assert task["status"] in ("pending", "completed")

    def test_create_task(self, client):
        """Test creating a task returns 201 with a pending task."""
        task = self._create_task(
            client, title="Reorder connectors", priority="high",
            due_date="2025-09-01",
        )
        try:
            assert task["title"] == "Reorder connectors"
            assert task["priority"] == "high"
            assert task["dueDate"] == "2025-09-01"
            # New tasks always start pending, regardless of request
            assert task["status"] == "pending"
            assert isinstance(task["id"], str)
            assert task["id"].startswith("task-")
        finally:
            client.delete(f"/api/tasks/{task['id']}")

    def test_create_task_defaults_priority(self, client):
        """Test priority defaults to 'medium' when omitted."""
        response = client.post(
            "/api/tasks", json={"title": "No priority", "dueDate": "2025-09-02"}
        )
        assert response.status_code == 201
        task = response.json()
        try:
            assert task["priority"] == "medium"
        finally:
            client.delete(f"/api/tasks/{task['id']}")

    def test_created_task_appears_in_list(self, client):
        """Test a created task is retrievable via GET."""
        task = self._create_task(client, title="Appears in list")
        try:
            data = client.get("/api/tasks").json()
            assert any(t["id"] == task["id"] for t in data)
        finally:
            client.delete(f"/api/tasks/{task['id']}")

    def test_toggle_task(self, client):
        """Test PATCH toggles status between pending and completed."""
        task = self._create_task(client, title="Toggle me")
        try:
            assert task["status"] == "pending"

            # pending -> completed
            response = client.patch(f"/api/tasks/{task['id']}")
            assert response.status_code == 200
            assert response.json()["status"] == "completed"

            # completed -> pending
            response = client.patch(f"/api/tasks/{task['id']}")
            assert response.status_code == 200
            assert response.json()["status"] == "pending"
        finally:
            client.delete(f"/api/tasks/{task['id']}")

    def test_delete_task(self, client):
        """Test deleting a task removes it from the store."""
        task = self._create_task(client, title="Delete me")

        response = client.delete(f"/api/tasks/{task['id']}")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["id"] == task["id"]

        # Confirm it is gone
        data = client.get("/api/tasks").json()
        assert all(t["id"] != task["id"] for t in data)

    def test_toggle_nonexistent_task(self, client):
        """Test toggling a task that doesn't exist returns 404."""
        response = client.patch("/api/tasks/nonexistent-999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_nonexistent_task(self, client):
        """Test deleting a task that doesn't exist returns 404."""
        response = client.delete("/api/tasks/nonexistent-999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_task_missing_required_field(self, client):
        """Test creating a task without required fields returns 422."""
        # Missing dueDate
        response = client.post("/api/tasks", json={"title": "Incomplete"})
        assert response.status_code == 422

        # Missing title
        response = client.post("/api/tasks", json={"dueDate": "2025-09-01"})
        assert response.status_code == 422
