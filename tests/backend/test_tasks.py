"""
Tests for tasks API endpoints.
"""
import pytest

import main


@pytest.fixture(autouse=True)
def clear_tasks():
    """Tasks live in module-level memory, so reset them around every test."""
    main.tasks.clear()
    yield
    main.tasks.clear()


def create_task(client, **overrides):
    payload = {"title": "Check stock", "priority": "high", "dueDate": "2025-10-08"}
    payload.update(overrides)
    return client.post("/api/tasks", json=payload)


class TestTasksEndpoints:
    """Test suite for task-related endpoints."""

    def test_get_all_tasks_empty(self, client):
        """Test getting tasks when none exist."""
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_task(self, client):
        """Test creating a task returns a pending task with an id."""
        response = create_task(client)
        assert response.status_code == 200

        task = response.json()
        assert task["id"] >= 1000
        assert task["title"] == "Check stock"
        assert task["priority"] == "high"
        assert task["dueDate"] == "2025-10-08"
        assert task["status"] == "pending"

    def test_create_task_strips_title(self, client):
        """Test that surrounding whitespace is removed from the title."""
        response = create_task(client, title="  Review spend  ")
        assert response.json()["title"] == "Review spend"

    def test_create_task_blank_title(self, client):
        """Test that a blank title is rejected."""
        response = create_task(client, title="   ")
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_create_task_invalid_priority(self, client):
        """Test that an unknown priority is rejected."""
        response = create_task(client, priority="urgent")
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_create_task_missing_due_date(self, client):
        """Test that a missing due date fails validation."""
        response = client.post("/api/tasks", json={"title": "No date"})
        assert response.status_code == 422

    def test_get_tasks_newest_first(self, client):
        """Test that tasks come back newest first."""
        create_task(client, title="first")
        create_task(client, title="second")

        titles = [t["title"] for t in client.get("/api/tasks").json()]
        assert titles == ["second", "first"]

    def test_task_ids_are_unique(self, client):
        """Test that two tasks never share an id."""
        first = create_task(client).json()
        second = create_task(client).json()
        assert first["id"] != second["id"]

    def test_toggle_task(self, client):
        """Test toggling a task back and forth between pending and completed."""
        task_id = create_task(client).json()["id"]

        response = client.patch(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

        response = client.patch(f"/api/tasks/{task_id}")
        assert response.json()["status"] == "pending"

    def test_toggle_nonexistent_task(self, client):
        """Test toggling a task that doesn't exist."""
        response = client.patch("/api/tasks/999999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_task(self, client):
        """Test deleting a task removes it from the list."""
        task_id = create_task(client).json()["id"]

        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert client.get("/api/tasks").json() == []

    def test_delete_nonexistent_task(self, client):
        """Test deleting a task that doesn't exist."""
        response = client.delete("/api/tasks/999999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
