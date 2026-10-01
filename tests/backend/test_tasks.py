"""
Tests for the in-memory task endpoints.
"""
import pytest

import main


@pytest.fixture(autouse=True)
def reset_tasks():
    """Start each test with no tasks."""
    main.tasks.clear()
    main.next_task_id = 1
    yield
    main.tasks.clear()
    main.next_task_id = 1


def create(client, **overrides):
    payload = {"title": "Check Q4 stock", "priority": "high", "dueDate": "2025-10-08", **overrides}
    return client.post("/api/tasks", json=payload)


class TestTaskEndpoints:
    """Test suite for /api/tasks."""

    def test_get_tasks_empty(self, client):
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_task(self, client):
        response = create(client, title="  Check Q4 stock  ")
        assert response.status_code == 201
        assert response.json() == {
            "id": "task-1",
            "title": "Check Q4 stock",
            "priority": "high",
            "dueDate": "2025-10-08",
            "status": "pending",
        }

    def test_get_tasks_newest_first(self, client):
        create(client, title="First")
        create(client, title="Second")
        titles = [t["title"] for t in client.get("/api/tasks").json()]
        assert titles == ["Second", "First"]

    def test_priority_defaults_to_medium(self, client):
        response = client.post("/api/tasks", json={"title": "No priority", "dueDate": "2025-10-08"})
        assert response.status_code == 201
        assert response.json()["priority"] == "medium"

    @pytest.mark.parametrize("overrides", [
        {"title": ""},
        {"priority": "urgent"},
        {"dueDate": "10/08/2025"},
    ])
    def test_create_task_rejects_invalid_input(self, client, overrides):
        assert create(client, **overrides).status_code in (400, 422)

    def test_create_task_rejects_blank_title(self, client):
        assert create(client, title="   ").status_code == 400

    def test_toggle_task(self, client):
        task_id = create(client).json()["id"]

        response = client.patch(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

        response = client.patch(f"/api/tasks/{task_id}")
        assert response.json()["status"] == "pending"

    def test_delete_task(self, client):
        task_id = create(client).json()["id"]

        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["id"] == task_id
        assert client.get("/api/tasks").json() == []

    def test_ids_not_reused_after_delete(self, client):
        first = create(client).json()["id"]
        client.delete(f"/api/tasks/{first}")
        assert create(client).json()["id"] == "task-2"

    @pytest.mark.parametrize("method", ["patch", "delete"])
    def test_unknown_task_returns_404(self, client, method):
        response = getattr(client, method)("/api/tasks/task-999")
        assert response.status_code == 404
