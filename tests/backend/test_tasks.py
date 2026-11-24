"""
Tests for task API endpoints.
"""
import pytest

import main


@pytest.fixture(autouse=True)
def clear_tasks():
    """Tasks live in a module-level list, so reset it to keep tests independent."""
    main.tasks.clear()
    yield
    main.tasks.clear()


def _create_task(client, **overrides):
    payload = {"title": "Check Q4 stock", "priority": "high", "dueDate": "2030-01-15"}
    payload.update(overrides)
    return client.post("/api/tasks", json=payload)


class TestTasksEndpoints:
    """Test suite for task-related endpoints."""

    def test_get_tasks_empty(self, client):
        """Test that no tasks exist before any are created."""
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_task(self, client):
        """Test creating a valid task."""
        response = _create_task(client)
        assert response.status_code == 201

        task = response.json()
        assert task["title"] == "Check Q4 stock"
        assert task["priority"] == "high"
        assert task["dueDate"] == "2030-01-15"
        assert task["status"] == "pending"
        assert isinstance(task["id"], str)

    def test_task_ids_dont_clash_with_mock_task_ids(self, client):
        """Test that API task IDs are prefixed strings, not the numeric IDs mock tasks use."""
        task = _create_task(client).json()
        assert task["id"].startswith("task-")

    def test_get_tasks_newest_first(self, client):
        """Test that tasks are listed newest first, matching how App.vue prepends new tasks."""
        first = _create_task(client, title="First").json()
        second = _create_task(client, title="Second").json()

        data = client.get("/api/tasks").json()
        assert [t["id"] for t in data] == [second["id"], first["id"]]

    def test_create_task_default_priority(self, client):
        """Test that priority defaults to medium when omitted."""
        response = client.post("/api/tasks", json={"title": "No priority", "dueDate": "2030-01-15"})
        assert response.status_code == 201
        assert response.json()["priority"] == "medium"

    def test_create_task_trims_title(self, client):
        """Test that surrounding whitespace is removed from the title."""
        response = _create_task(client, title="  Padded  ")
        assert response.json()["title"] == "Padded"

    def test_create_task_blank_title(self, client):
        """Test that a whitespace-only title is rejected."""
        response = _create_task(client, title="   ")
        assert response.status_code == 400
        assert "title" in response.json()["detail"].lower()

    def test_create_task_invalid_priority(self, client):
        """Test that an unknown priority is rejected by validation."""
        response = _create_task(client, priority="urgent")
        assert response.status_code == 422

    def test_create_task_invalid_due_date(self, client):
        """Test that a malformed due date returns 400 rather than a server error."""
        response = _create_task(client, dueDate="15/01/2030")
        assert response.status_code == 400
        assert "yyyy-mm-dd" in response.json()["detail"].lower()

    def test_toggle_task(self, client):
        """Test toggling a task to completed and back to pending."""
        task_id = _create_task(client).json()["id"]

        response = client.patch(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

        response = client.patch(f"/api/tasks/{task_id}")
        assert response.json()["status"] == "pending"

    def test_toggle_nonexistent_task(self, client):
        """Test toggling a task that doesn't exist."""
        response = client.patch("/api/tasks/task-999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_task(self, client):
        """Test deleting a task removes it from the list."""
        task_id = _create_task(client).json()["id"]

        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 204
        assert client.get("/api/tasks").json() == []

    def test_delete_nonexistent_task(self, client):
        """Test deleting a task that doesn't exist."""
        response = client.delete("/api/tasks/task-999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
