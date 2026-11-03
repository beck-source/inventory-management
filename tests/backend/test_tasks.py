"""
Tests for task endpoints (list, create, toggle, delete).
"""
import pytest

import mock_data


@pytest.fixture(autouse=True)
def reset_tasks():
    """Tasks live in a shared in-memory list, so clear it around every test."""
    mock_data.tasks.clear()
    yield
    mock_data.tasks.clear()


def create(client, **overrides):
    body = {"title": "Reorder sensors", "priority": "high", "dueDate": "2025-12-01"}
    body.update(overrides)
    return client.post("/api/tasks", json=body)


class TestTasks:
    def test_list_empty(self, client):
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_assigns_id_and_pending_status(self, client):
        response = create(client)
        assert response.status_code == 201
        task = response.json()
        assert task["id"] >= 5  # ids 1-4 are reserved for the client's mock user tasks
        assert task["status"] == "pending"
        assert task["title"] == "Reorder sensors"
        assert task["dueDate"] == "2025-12-01"
        assert client.get("/api/tasks").json() == [task]

    def test_ids_are_unique_after_delete(self, client):
        first = create(client).json()
        second = create(client).json()
        client.delete(f"/api/tasks/{second['id']}")
        third = create(client).json()
        assert len({first["id"], third["id"]}) == 2

    @pytest.mark.parametrize("overrides", [
        {"title": ""},
        {"priority": "urgent"},
        {"dueDate": "not-a-date"},
    ])
    def test_create_validation(self, client, overrides):
        assert create(client, **overrides).status_code == 422

    def test_toggle(self, client):
        task_id = create(client).json()["id"]
        assert client.patch(f"/api/tasks/{task_id}").json()["status"] == "completed"
        assert client.patch(f"/api/tasks/{task_id}").json()["status"] == "pending"

    def test_delete(self, client):
        task_id = create(client).json()["id"]
        assert client.delete(f"/api/tasks/{task_id}").status_code == 204
        assert client.get("/api/tasks").json() == []

    def test_missing_task_returns_404(self, client):
        assert client.patch("/api/tasks/999").status_code == 404
        assert client.delete("/api/tasks/999").status_code == 404
