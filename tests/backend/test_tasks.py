"""Tests for task API endpoints."""
import pytest

from mock_data import tasks


@pytest.fixture(autouse=True)
def isolate_tasks():
    """Restore tasks after each test.

    `tasks` is module-level state imported once per process, so a task created by
    one test would stay visible to every later test. Slice assignment restores the
    contents in place - rebinding would leave main.py pointing at the old list.
    """
    saved = list(tasks)
    yield
    tasks[:] = saved


def valid_request(**overrides):
    """Build a well-formed create-task payload."""
    payload = {"title": "Review Q4 stock levels", "priority": "high", "dueDate": "2026-10-08"}
    payload.update(overrides)
    return payload


class TestGetTasks:
    """Test suite for listing tasks."""

    def test_get_tasks_returns_list(self, client):
        """Test that the tasks endpoint returns a list."""
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_tasks_expose_the_client_contract(self, client):
        """Test that every task carries the fields the client renders."""
        client.post("/api/tasks", json=valid_request())

        for task in client.get("/api/tasks").json():
            for field in ["id", "title", "priority", "dueDate", "status"]:
                assert field in task, f"Missing field: {field}"

    def test_tasks_are_returned_newest_first(self, client):
        """Test that the most recently created task is listed first."""
        client.post("/api/tasks", json=valid_request(title="First"))
        second = client.post("/api/tasks", json=valid_request(title="Second")).json()

        assert client.get("/api/tasks").json()[0]["id"] == second["id"]


class TestCreateTask:
    """Test suite for creating tasks."""

    def test_create_returns_201_with_task(self, client):
        """Test that a valid request returns 201 and the created task."""
        response = client.post("/api/tasks", json=valid_request())
        assert response.status_code == 201

        task = response.json()
        assert task["title"] == "Review Q4 stock levels"
        assert task["priority"] == "high"
        assert task["dueDate"] == "2026-10-08"
        assert task["status"] == "pending"

    def test_created_task_id_cannot_collide_with_mock_tasks(self, client):
        """Test that ids are prefixed, since the client merges numeric mock ids."""
        task_id = client.post("/api/tasks", json=valid_request()).json()["id"]

        assert task_id.startswith("T-")
        assert not task_id.isdigit()

    def test_title_is_trimmed(self, client):
        """Test that surrounding whitespace is stripped from the title."""
        response = client.post("/api/tasks", json=valid_request(title="  Padded  "))
        assert response.json()["title"] == "Padded"

    def test_default_priority_is_medium(self, client):
        """Test that priority defaults to medium when omitted."""
        response = client.post(
            "/api/tasks",
            json={"title": "No priority given", "dueDate": "2026-10-08"}
        )
        assert response.json()["priority"] == "medium"

    def test_blank_title_is_rejected(self, client):
        """Test that a blank title returns 400."""
        response = client.post("/api/tasks", json=valid_request(title="   "))
        assert response.status_code == 400

    def test_blank_due_date_is_rejected(self, client):
        """Test that a blank due date returns 400."""
        response = client.post("/api/tasks", json=valid_request(dueDate=""))
        assert response.status_code == 400

    def test_unknown_priority_is_rejected(self, client):
        """Test that a priority outside the allowed set returns 400."""
        response = client.post("/api/tasks", json=valid_request(priority="urgent"))
        assert response.status_code == 400


class TestToggleTask:
    """Test suite for toggling task status."""

    def test_toggle_flips_between_pending_and_completed(self, client):
        """Test that toggling moves a task through both states."""
        task_id = client.post("/api/tasks", json=valid_request()).json()["id"]

        assert client.patch(f"/api/tasks/{task_id}").json()["status"] == "completed"
        assert client.patch(f"/api/tasks/{task_id}").json()["status"] == "pending"

    def test_toggle_persists_for_later_reads(self, client):
        """Test that a toggled status is visible on the next list request."""
        task_id = client.post("/api/tasks", json=valid_request()).json()["id"]
        client.patch(f"/api/tasks/{task_id}")

        listed = next(t for t in client.get("/api/tasks").json() if t["id"] == task_id)
        assert listed["status"] == "completed"

    def test_toggle_unknown_task_returns_404(self, client):
        """Test that toggling an unknown task returns 404."""
        assert client.patch("/api/tasks/DOES-NOT-EXIST").status_code == 404


class TestDeleteTask:
    """Test suite for deleting tasks."""

    def test_delete_returns_204_and_removes_the_task(self, client):
        """Test that a deleted task is gone from the list."""
        task_id = client.post("/api/tasks", json=valid_request()).json()["id"]

        assert client.delete(f"/api/tasks/{task_id}").status_code == 204
        assert task_id not in [t["id"] for t in client.get("/api/tasks").json()]

    def test_delete_unknown_task_returns_404(self, client):
        """Test that deleting an unknown task returns 404."""
        assert client.delete("/api/tasks/DOES-NOT-EXIST").status_code == 404

    def test_delete_leaves_other_tasks_untouched(self, client):
        """Test that deleting one task does not remove the others."""
        keep = client.post("/api/tasks", json=valid_request(title="Keep")).json()
        drop = client.post("/api/tasks", json=valid_request(title="Drop")).json()

        client.delete(f"/api/tasks/{drop['id']}")

        remaining = [t["id"] for t in client.get("/api/tasks").json()]
        assert keep["id"] in remaining
        assert drop["id"] not in remaining
