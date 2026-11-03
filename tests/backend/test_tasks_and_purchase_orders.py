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
        created = make_task(client).json()
        response = client.delete(f"/api/tasks/{created['id']}")
        assert response.status_code == 200
        assert response.json() == created
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


class TestInputValidation:
    """Validation limits, ID uniqueness and caps for runtime-created records."""

    @pytest.mark.parametrize("payload", [
        {"title": "", "priority": "high", "dueDate": "2025-12-01"},
        {"title": "x" * 201, "priority": "high", "dueDate": "2025-12-01"},
        {"title": "ok", "priority": "urgent", "dueDate": "2025-12-01"},
        {"title": "ok", "priority": "high", "dueDate": "not-a-date"},
    ])
    def test_invalid_task_rejected(self, client, payload):
        assert client.post("/api/tasks", json=payload).status_code == 422

    def test_task_ids_unique_after_delete(self, client):
        first = make_task(client).json()["id"]
        second = make_task(client).json()["id"]
        client.delete(f"/api/tasks/{first}")
        third = make_task(client).json()["id"]
        assert len({first, second, third}) == 3

    def test_task_cap(self, client, monkeypatch):
        monkeypatch.setattr(main, "MAX_STORED_RECORDS", 2)
        assert make_task(client).status_code == 200
        assert make_task(client).status_code == 200
        assert make_task(client).status_code == 429

    @pytest.mark.parametrize("overrides", [
        {"supplier_name": ""},
        {"supplier_name": "x" * 201},
        {"notes": "x" * 2001},
        {"expected_delivery_date": "soon"},
        {"quantity": 10**9},
        {"unit_cost": 10**9},
    ])
    def test_invalid_purchase_order_rejected(self, client, overrides):
        assert make_po(client, **overrides).status_code == 422

    def test_purchase_order_cap(self, client, monkeypatch):
        monkeypatch.setattr(main, "MAX_STORED_RECORDS", 1)
        assert make_po(client, "1").status_code == 200
        assert make_po(client, "2").status_code == 429

    def test_purchase_order_ids_unique(self, client):
        ids = {make_po(client, str(i)).json()["id"] for i in range(1, 4)}
        assert len(ids) == 3

    def test_restock_item_list_too_long(self, client):
        items = [{"sku": f"S{i}", "quantity": 1} for i in range(201)]
        assert client.post("/api/restock/orders", json={"budget": 100, "items": items}).status_code == 422


class TestMonthValidation:
    @pytest.mark.parametrize("path", ["/api/orders", "/api/dashboard/summary"])
    @pytest.mark.parametrize("month", ["garbage", "2025-13", "2025", "Q5-2025", "01", "2025-1"])
    def test_invalid_month_returns_400(self, client, path, month):
        assert client.get(path, params={"month": month}).status_code == 400

    @pytest.mark.parametrize("month", ["", "all", "2025-01", "Q1-2025"])
    def test_valid_month_accepted(self, client, month):
        assert client.get("/api/orders", params={"month": month}).status_code == 200

    def test_month_exact_prefix(self, client):
        for order in client.get("/api/orders", params={"month": "2025-01"}).json():
            assert order["order_date"][:7] == "2025-01"


class TestCors:
    def test_allowed_origin(self, client):
        r = client.get("/api/orders", headers={"Origin": "http://localhost:3000"})
        assert r.headers["access-control-allow-origin"] == "http://localhost:3000"
        assert "access-control-allow-credentials" not in r.headers

    def test_disallowed_origin(self, client):
        r = client.get("/api/orders", headers={"Origin": "http://evil.example"})
        assert "access-control-allow-origin" not in r.headers
