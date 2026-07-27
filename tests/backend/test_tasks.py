"""
Tests for tasks API endpoints.
"""
import pytest


class TestTasksEndpoints:
    """Test suite for task-related endpoints."""

    def test_get_all_tasks(self, client):
        """Test getting all tasks."""
        response = client.get("/api/tasks")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_create_task(self, client):
        """Test creating a task."""
        response = client.post("/api/tasks", json={
            "title": "Review Q3 inventory levels",
            "priority": "high",
            "dueDate": "2026-08-15"
        })
        assert response.status_code == 200

        task = response.json()
        assert "id" in task
        assert task["title"] == "Review Q3 inventory levels"
        assert task["priority"] == "high"
        assert task["dueDate"] == "2026-08-15"
        # New tasks always start pending; status is not client-supplied
        assert task["status"] == "pending"

    def test_created_task_appears_in_list(self, client):
        """Test that a created task is returned by the list endpoint."""
        create_response = client.post("/api/tasks", json={
            "title": "Approve Tokyo warehouse orders",
            "priority": "medium",
            "dueDate": "2026-08-20"
        })
        task_id = create_response.json()["id"]

        response = client.get("/api/tasks")
        assert response.status_code == 200

        data = response.json()
        assert any(task["id"] == task_id for task in data)

    def test_task_id_is_string(self, client):
        """Test that task ids are strings, keeping them distinct from mock task ids."""
        response = client.post("/api/tasks", json={
            "title": "Check reorder points",
            "priority": "low",
            "dueDate": "2026-09-01"
        })
        assert response.status_code == 200
        assert isinstance(response.json()["id"], str)

    def test_create_task_trims_title(self, client):
        """Test that surrounding whitespace is stripped from the title."""
        response = client.post("/api/tasks", json={
            "title": "   Audit backlog   ",
            "priority": "medium",
            "dueDate": "2026-08-10"
        })
        assert response.status_code == 200
        assert response.json()["title"] == "Audit backlog"

    def test_create_task_empty_title(self, client):
        """Test that a blank title is rejected."""
        response = client.post("/api/tasks", json={
            "title": "   ",
            "priority": "medium",
            "dueDate": "2026-08-10"
        })
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert "empty" in data["detail"].lower()

    def test_create_task_invalid_priority(self, client):
        """Test that an unsupported priority is rejected."""
        response = client.post("/api/tasks", json={
            "title": "Invalid priority task",
            "priority": "urgent",
            "dueDate": "2026-08-10"
        })
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert "priority" in data["detail"].lower()

    def test_create_task_missing_field(self, client):
        """Test that a missing required field fails validation."""
        response = client.post("/api/tasks", json={"title": "No due date"})
        assert response.status_code == 422

    @pytest.mark.parametrize("priority", ["high", "medium", "low"])
    def test_create_task_accepts_valid_priorities(self, client, priority):
        """Test that each supported priority is accepted."""
        response = client.post("/api/tasks", json={
            "title": f"Task with {priority} priority",
            "priority": priority,
            "dueDate": "2026-08-12"
        })
        assert response.status_code == 200
        assert response.json()["priority"] == priority

    def test_toggle_task(self, client):
        """Test toggling a task from pending to completed."""
        create_response = client.post("/api/tasks", json={
            "title": "Toggle me",
            "priority": "medium",
            "dueDate": "2026-08-18"
        })
        task_id = create_response.json()["id"]

        response = client.patch(f"/api/tasks/{task_id}")
        assert response.status_code == 200

        task = response.json()
        assert task["id"] == task_id
        assert task["status"] == "completed"

    def test_toggle_task_twice_returns_to_pending(self, client):
        """Test that toggling twice restores the original status."""
        create_response = client.post("/api/tasks", json={
            "title": "Toggle me twice",
            "priority": "low",
            "dueDate": "2026-08-19"
        })
        task_id = create_response.json()["id"]

        client.patch(f"/api/tasks/{task_id}")
        response = client.patch(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "pending"

    def test_toggle_nonexistent_task(self, client):
        """Test toggling a task that doesn't exist."""
        response = client.patch("/api/tasks/task-nonexistent-999")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_delete_task(self, client):
        """Test deleting a task."""
        create_response = client.post("/api/tasks", json={
            "title": "Delete me",
            "priority": "high",
            "dueDate": "2026-08-22"
        })
        task_id = create_response.json()["id"]

        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == task_id
        assert data["deleted"] is True

    def test_deleted_task_removed_from_list(self, client):
        """Test that a deleted task no longer appears in the list."""
        create_response = client.post("/api/tasks", json={
            "title": "Transient task",
            "priority": "low",
            "dueDate": "2026-08-25"
        })
        task_id = create_response.json()["id"]

        client.delete(f"/api/tasks/{task_id}")

        response = client.get("/api/tasks")
        data = response.json()
        assert all(task["id"] != task_id for task in data)

    def test_create_after_delete_does_not_reuse_id(self, client):
        """Test that deleting a task cannot make the next create reuse a live id."""
        first = client.post("/api/tasks", json={
            "title": "First", "priority": "low", "dueDate": "2026-08-01"
        }).json()
        second = client.post("/api/tasks", json={
            "title": "Second", "priority": "low", "dueDate": "2026-08-02"
        }).json()

        # Deleting the earlier task must not free its slot for reuse
        client.delete(f"/api/tasks/{first['id']}")

        third = client.post("/api/tasks", json={
            "title": "Third", "priority": "low", "dueDate": "2026-08-03"
        }).json()

        assert third["id"] != second["id"]

        response = client.get("/api/tasks")
        ids = [task["id"] for task in response.json()]
        assert len(ids) == len(set(ids))

    def test_delete_nonexistent_task(self, client):
        """Test deleting a task that doesn't exist."""
        response = client.delete("/api/tasks/task-nonexistent-999")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_task_structure(self, client):
        """Test that every task exposes the full client-facing structure."""
        client.post("/api/tasks", json={
            "title": "Structure check",
            "priority": "medium",
            "dueDate": "2026-08-30"
        })

        response = client.get("/api/tasks")
        data = response.json()
        assert len(data) > 0

        valid_priorities = ["high", "medium", "low"]
        valid_statuses = ["pending", "completed"]

        for task in data:
            assert isinstance(task["id"], str)
            assert isinstance(task["title"], str)
            # dueDate is camelCase to match the client task shape
            assert isinstance(task["dueDate"], str)
            assert task["priority"] in valid_priorities
            assert task["status"] in valid_statuses
