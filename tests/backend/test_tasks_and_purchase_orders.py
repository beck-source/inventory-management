"""
Tests for the tasks and purchase-order endpoints.
"""
import pytest

import main


@pytest.fixture(autouse=True)
def reset_state():
    """Keep in-memory state from leaking between tests."""
    main.tasks.clear()
    main.purchase_orders.clear()
    yield
    main.tasks.clear()
    main.purchase_orders.clear()


def make_task(client, title="Order filters", priority="high", due="2025-12-01"):
    return client.post("/api/tasks", json={"title": title, "priority": priority, "dueDate": due})


def make_po(client, backlog_item_id="1", **overrides):
    payload = {
        "backlog_item_id": backlog_item_id,
        "supplier_name": "Acme Supply",
        "quantity": 350,
        "unit_cost": 12.5,
        "expected_delivery_date": "2025-12-15",
        "notes": "rush",
    }
    payload.update(overrides)
    return client.post("/api/purchase-orders", json=payload)


class TestTasks:
    def test_get_tasks_empty(self, client):
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_task(self, client):
        response = make_task(client)
        assert response.status_code == 200
        task = response.json()
        assert task["title"] == "Order filters"
        assert task["priority"] == "high"
        assert task["dueDate"] == "2025-12-01"
        assert task["status"] == "pending"
        assert task["id"]

    def test_get_tasks_newest_first(self, client):
        make_task(client, title="first")
        make_task(client, title="second")
        titles = [t["title"] for t in client.get("/api/tasks").json()]
        assert titles == ["second", "first"]

    def test_create_task_requires_due_date(self, client):
        response = client.post("/api/tasks", json={"title": "No date"})
        assert response.status_code == 422

    def test_toggle_task(self, client):
        task_id = make_task(client).json()["id"]
        toggled = client.patch(f"/api/tasks/{task_id}")
        assert toggled.status_code == 200
        assert toggled.json()["status"] == "completed"
        assert client.patch(f"/api/tasks/{task_id}").json()["status"] == "pending"

    def test_toggle_task_not_found(self, client):
        assert client.patch("/api/tasks/nope").status_code == 404

    def test_delete_task(self, client):
        task_id = make_task(client).json()["id"]
        assert client.delete(f"/api/tasks/{task_id}").status_code == 200
        assert client.get("/api/tasks").json() == []

    def test_delete_task_not_found(self, client):
        assert client.delete("/api/tasks/nope").status_code == 404


class TestPurchaseOrders:
    def test_create_purchase_order(self, client):
        response = make_po(client)
        assert response.status_code == 200
        po = response.json()
        assert po["id"] == "PO-0001"
        assert po["backlog_item_id"] == "1"
        assert po["supplier_name"] == "Acme Supply"
        assert po["quantity"] == 350
        assert po["status"] == "pending"
        assert po["notes"] == "rush"

    def test_get_purchase_order_by_backlog_item(self, client):
        make_po(client, backlog_item_id="2")
        response = client.get("/api/purchase-orders/2")
        assert response.status_code == 200
        assert response.json()["backlog_item_id"] == "2"

    def test_get_purchase_order_not_found(self, client):
        assert client.get("/api/purchase-orders/1").status_code == 404

    def test_create_purchase_order_unknown_backlog_item(self, client):
        assert make_po(client, backlog_item_id="9999").status_code == 404

    def test_create_purchase_order_duplicate(self, client):
        make_po(client)
        assert make_po(client).status_code == 409

    @pytest.mark.parametrize("overrides", [{"quantity": 0}, {"quantity": -5}, {"unit_cost": -1}])
    def test_create_purchase_order_invalid_values(self, client, overrides):
        assert make_po(client, **overrides).status_code == 400

    def test_backlog_reflects_purchase_order(self, client):
        make_po(client, backlog_item_id="1")
        by_id = {item["id"]: item for item in client.get("/api/backlog").json()}
        assert by_id["1"]["has_purchase_order"] is True
        assert by_id["2"]["has_purchase_order"] is False
