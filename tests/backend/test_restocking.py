"""Tests for restocking-related API endpoints."""
import pytest
import sys
from pathlib import Path

server_path = Path(__file__).parent.parent.parent / "server"
sys.path.insert(0, str(server_path))

import main as app_module


@pytest.fixture(autouse=True)
def clear_restocking_orders():
    app_module.restocking_orders.clear()
    yield
    app_module.restocking_orders.clear()


class TestDemandUnitCost:
    def test_demand_forecasts_include_unit_cost(self, client):
        response = client.get("/api/demand")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        for item in data:
            assert "unit_cost" in item
            assert isinstance(item["unit_cost"], float)
            assert item["unit_cost"] > 0


class TestRestockingOrders:
    SAMPLE_ITEMS = [
        {"sku": "WDG-001", "name": "Industrial Widget Type A", "quantity": 150, "unit_cost": 245.00},
        {"sku": "FLT-405", "name": "Oil Filter Cartridge", "quantity": 150, "unit_cost": 8.25},
    ]

    def test_get_restocking_orders_empty(self, client):
        response = client.get("/api/restocking-orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_post_restocking_order_returns_201(self, client):
        response = client.post("/api/restocking-orders", json={"items": self.SAMPLE_ITEMS})
        assert response.status_code == 201

    def test_post_restocking_order_structure(self, client):
        response = client.post("/api/restocking-orders", json={"items": self.SAMPLE_ITEMS})
        data = response.json()
        assert "id" in data
        assert "order_number" in data
        assert data["order_number"].startswith("RST-")
        assert data["status"] == "Submitted"
        assert "submitted_date" in data
        assert "expected_delivery" in data
        assert len(data["items"]) == 2

    def test_post_restocking_order_total_cost(self, client):
        response = client.post("/api/restocking-orders", json={"items": self.SAMPLE_ITEMS})
        data = response.json()
        expected_total = (150 * 245.00) + (150 * 8.25)
        assert abs(data["total_cost"] - expected_total) < 0.01

    def test_post_restocking_order_14_day_lead_time(self, client):
        from datetime import datetime, timedelta
        response = client.post("/api/restocking-orders", json={"items": self.SAMPLE_ITEMS})
        data = response.json()
        submitted = datetime.fromisoformat(data["submitted_date"])
        expected = datetime.fromisoformat(data["expected_delivery"])
        assert (expected - submitted).days == 14

    def test_get_restocking_orders_newest_first(self, client):
        client.post("/api/restocking-orders", json={"items": self.SAMPLE_ITEMS})
        client.post("/api/restocking-orders", json={"items": [self.SAMPLE_ITEMS[0]]})
        response = client.get("/api/restocking-orders")
        data = response.json()
        assert len(data) == 2
        # Newest (second posted) should be first
        assert data[0]["order_number"] == "RST-2026-0002"
        assert data[1]["order_number"] == "RST-2026-0001"

    def test_post_restocking_order_numbering(self, client):
        r1 = client.post("/api/restocking-orders", json={"items": self.SAMPLE_ITEMS})
        r2 = client.post("/api/restocking-orders", json={"items": self.SAMPLE_ITEMS})
        assert r1.json()["order_number"] == "RST-2026-0001"
        assert r2.json()["order_number"] == "RST-2026-0002"

    def test_post_restocking_order_empty_items(self, client):
        response = client.post("/api/restocking-orders", json={"items": []})
        assert response.status_code == 201
        data = response.json()
        assert data["items"] == []
        assert data["total_cost"] == 0.0
