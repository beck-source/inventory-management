"""Tests for the restocking order endpoints."""


def make_item(sku="WDG-001", category="Actuators", quantity=10, unit_cost=10.0):
    return {
        "sku": sku,
        "name": f"Item {sku}",
        "category": category,
        "quantity": quantity,
        "unit_cost": unit_cost,
    }


class TestDemandCostFields:
    def test_demand_includes_unit_cost_and_category(self, client):
        response = client.get("/api/demand")
        assert response.status_code == 200
        for forecast in response.json():
            assert forecast["unit_cost"] > 0
            assert forecast["category"]


class TestCreateRestockOrder:
    def test_create_order_success(self, client):
        payload = {"budget": 1000, "items": [make_item(quantity=10, unit_cost=12.5)]}
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["total_cost"] == 125.0
        assert data["status"] == "Submitted"
        assert data["lead_time_days"] == 10
        assert data["order_number"].startswith("RST-")

    def test_lead_time_is_max_across_items(self, client):
        payload = {
            "budget": 10000,
            "items": [
                make_item("SNR-420", "Sensors"),
                make_item("PCB-001", "Circuit Boards"),
                make_item("PSU-501", "Power Supplies"),
            ],
        }
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 201
        assert response.json()["lead_time_days"] == 14

    def test_unknown_category_uses_default_lead_time(self, client):
        payload = {"budget": 1000, "items": [make_item(category="Mystery")]}
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 201
        assert response.json()["lead_time_days"] == 10

    def test_over_budget_rejected(self, client):
        payload = {"budget": 50, "items": [make_item(quantity=10, unit_cost=10.0)]}
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 400
        assert "budget" in response.json()["detail"].lower()

    def test_empty_items_rejected(self, client):
        response = client.post("/api/restocking/orders", json={"budget": 100, "items": []})
        assert response.status_code == 400

    def test_zero_quantity_rejected(self, client):
        payload = {"budget": 100, "items": [make_item(quantity=0)]}
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 400

    def test_invalid_payload_rejected(self, client):
        response = client.post("/api/restocking/orders", json={"items": []})
        assert response.status_code == 422


class TestGetRestockOrders:
    def test_empty_by_default(self, client):
        response = client.get("/api/restocking/orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_submitted_orders_newest_first(self, client):
        for sku in ("AAA-001", "BBB-002"):
            client.post("/api/restocking/orders", json={"budget": 1000, "items": [make_item(sku)]})
        data = client.get("/api/restocking/orders").json()
        assert len(data) == 2
        assert data[0]["items"][0]["sku"] == "BBB-002"

    def test_submitted_orders_do_not_affect_orders_endpoint(self, client):
        before = len(client.get("/api/orders").json())
        client.post("/api/restocking/orders", json={"budget": 1000, "items": [make_item()]})
        assert len(client.get("/api/orders").json()) == before
