"""
Tests for tasks API endpoints (the Tasks modal in the top nav).
"""
import pytest

import mock_data


@pytest.fixture(autouse=True)
def reset_tasks():
    """
    Tasks live in a module-level list shared by every test.
    Snapshot and restore it IN PLACE: main.py bound the same list object at import,
    so rebinding mock_data.tasks would not affect the app.
    """
    snapshot = list(mock_data.tasks)
    yield
    mock_data.tasks[:] = snapshot


def _create(client, **overrides):
    payload = {"title": "Check Tokyo stock", "priority": "high", "dueDate": "2025-10-20"}
    payload.update(overrides)
    return client.post("/api/tasks", json=payload)


class TestTasksEndpoints:
    """Test suite for task-related endpoints."""

    def test_get_tasks_empty_by_default(self, client):
        """Test that the list is an empty array (not a 404) before any task exists."""
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_task(self, client):
        """Test creating a task returns the full task, always pending."""
        response = _create(client)
        assert response.status_code == 201

        task = response.json()
        assert task["title"] == "Check Tokyo stock"
        assert task["priority"] == "high"
        assert task["dueDate"] == "2025-10-20"
        assert task["status"] == "pending"
        assert isinstance(task["id"], str) and task["id"]

    def test_create_task_trims_title(self, client):
        """Test that surrounding whitespace is stripped from the title."""
        response = _create(client, title="  Review spend  ")
        assert response.status_code == 201
        assert response.json()["title"] == "Review spend"

    def test_create_task_blank_title(self, client):
        """Test that a whitespace-only title is rejected."""
        response = _create(client, title="   ")
        assert response.status_code == 400
        assert "title" in response.json()["detail"].lower()

    def test_create_task_empty_title(self, client):
        """Test that an empty title fails request validation."""
        response = _create(client, title="")
        assert response.status_code == 422

    def test_create_task_invalid_priority(self, client):
        """Test that priority must be high, medium or low."""
        response = _create(client, priority="urgent")
        assert response.status_code == 422

    @pytest.mark.parametrize("due_date", ["10/20/2025", "not-a-date", "2025-13-45"])
    def test_create_task_invalid_due_date(self, client, due_date):
        """Test that dueDate must be a real YYYY-MM-DD date."""
        response = _create(client, dueDate=due_date)
        assert response.status_code == 400
        assert "dueDate" in response.json()["detail"]

    def test_create_task_missing_due_date(self, client):
        """Test that dueDate is required."""
        response = client.post("/api/tasks", json={"title": "No date", "priority": "low"})
        assert response.status_code == 422

    def test_get_tasks_newest_first(self, client):
        """Test that tasks come back newest first, matching how the client prepends them."""
        first = _create(client, title="first").json()
        second = _create(client, title="second").json()

        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert [t["id"] for t in response.json()] == [second["id"], first["id"]]

    def test_task_ids_are_unique_after_delete(self, client):
        """Test that deleting a task never causes a later task to reuse its id."""
        first = _create(client, title="first").json()
        client.delete(f"/api/tasks/{first['id']}")
        second = _create(client, title="second").json()
        assert second["id"] != first["id"]

    def test_task_ids_do_not_collide_with_demo_tasks(self, client):
        """Test that ids are strings; the client's demo tasks use integer ids 1-4."""
        assert isinstance(_create(client).json()["id"], str)

    def test_toggle_task(self, client):
        """Test toggling a task flips pending <-> completed."""
        task = _create(client).json()

        response = client.patch(f"/api/tasks/{task['id']}")
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

        response = client.patch(f"/api/tasks/{task['id']}")
        assert response.json()["status"] == "pending"

    def test_toggle_persists(self, client):
        """Test that a toggled status is what the list endpoint returns."""
        task = _create(client).json()
        client.patch(f"/api/tasks/{task['id']}")

        listed = client.get("/api/tasks").json()
        assert listed[0]["status"] == "completed"

    def test_toggle_nonexistent_task(self, client):
        """Test toggling a task that doesn't exist."""
        response = client.patch("/api/tasks/nonexistent-task-999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_task(self, client):
        """Test deleting a task removes it from the list."""
        task = _create(client).json()

        response = client.delete(f"/api/tasks/{task['id']}")
        assert response.status_code == 204

        assert client.get("/api/tasks").json() == []

    def test_delete_nonexistent_task(self, client):
        """Test deleting a task that doesn't exist."""
        response = client.delete("/api/tasks/nonexistent-task-999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
