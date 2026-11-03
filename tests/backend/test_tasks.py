"""
Tests for the task endpoints (in-memory, created through the API).
"""
import pytest

from mock_data import tasks


@pytest.fixture(autouse=True)
def clear_tasks():
    """Tasks live in shared in-memory state, so reset around each test."""
    tasks.clear()
    yield
    tasks.clear()


def create(client, **overrides):
    body = {"title": "Review Q4 stock", "priority": "high", "dueDate": "2025-11-10"}
    body.update(overrides)
    return client.post("/api/tasks", json=body)


class TestCreateTask:
    def test_create_returns_201_pending_task(self, client):
        response = create(client)
        assert response.status_code == 201
        task = response.json()
        assert task["title"] == "Review Q4 stock"
        assert task["priority"] == "high"
        assert task["dueDate"] == "2025-11-10"
        assert task["status"] == "pending"

    def test_ids_start_above_frontend_mock_task_ids(self, client):
        assert create(client).json()["id"] >= 1000

    def test_ids_are_not_reused_after_delete(self, client):
        first = create(client).json()["id"]
        second = create(client).json()["id"]
        client.delete(f"/api/tasks/{second}")
        third = create(client).json()["id"]
        assert first < second < third

    def test_title_is_trimmed(self, client):
        assert create(client, title="  Call supplier  ").json()["title"] == "Call supplier"

    def test_priority_defaults_to_medium(self, client):
        response = client.post("/api/tasks", json={"title": "x", "dueDate": "2025-11-10"})
        assert response.status_code == 201
        assert response.json()["priority"] == "medium"

    @pytest.mark.parametrize("overrides,status", [
        ({"title": "   "}, 400),
        ({"dueDate": "10.11.2025"}, 400),
        ({"priority": "urgent"}, 422),
    ])
    def test_invalid_input_rejected(self, client, overrides, status):
        assert create(client, **overrides).status_code == status
        assert tasks == []


class TestListTasks:
    def test_empty_list(self, client):
        assert client.get("/api/tasks").json() == []

    def test_newest_first(self, client):
        create(client, title="first")
        create(client, title="second")
        titles = [t["title"] for t in client.get("/api/tasks").json()]
        assert titles == ["second", "first"]


class TestToggleAndDelete:
    def test_toggle_flips_status_both_ways(self, client):
        task_id = create(client).json()["id"]
        assert client.patch(f"/api/tasks/{task_id}").json()["status"] == "completed"
        assert client.patch(f"/api/tasks/{task_id}").json()["status"] == "pending"

    def test_delete_removes_task(self, client):
        task_id = create(client).json()["id"]
        assert client.delete(f"/api/tasks/{task_id}").status_code == 200
        assert client.get("/api/tasks").json() == []

    def test_unknown_task_returns_404(self, client):
        assert client.patch("/api/tasks/9999").status_code == 404
        assert client.delete("/api/tasks/9999").status_code == 404
