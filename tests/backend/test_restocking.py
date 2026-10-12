"""
Tests for the restocking order endpoint.
"""
import pytest


class TestRestockOrderCreation:
    """Test suite for POST /api/restock-orders."""

    def test_create_restock_order_success(self, client):
        """Test placing a restocking order with a single item."""
        payload = {
            "items": [
                {
                    "sku": "PSU-508",
                    "name": "Battery Backup Power Supply",
                    "quantity": 75,
                    "unit_cost": 185.5,
                    "warehouse": "Tokyo",
                    "category": "Power Supplies"
                }
            ],
            "budget": 20000
        }
        response = client.post("/api/restock-orders", json=payload)
        assert response.status_code == 201

        order = response.json()
        assert order["status"] == "Submitted"
        assert order["order_number"].startswith("ORD-2025-")
        assert order["warehouse"] == "Tokyo"
        assert order["category"] == "Power Supplies"
        assert order["lead_time_days"] == 12
        assert order["items"][0]["sku"] == "PSU-508"
        assert order["items"][0]["unit_price"] == 185.5

    def test_create_restock_order_empty_items_returns_400(self, client):
        """Test that submitting an order with no items is rejected."""
        response = client.post("/api/restock-orders", json={"items": [], "budget": 5000})
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data

    def test_create_restock_order_lead_time_matches_warehouse(self, client):
        """Test that lead time is derived from the item's warehouse."""
        payload = {
            "items": [
                {
                    "sku": "TMP-201",
                    "name": "Temperature Sensor Module",
                    "quantity": 25,
                    "unit_cost": 89.5,
                    "warehouse": "London",
                    "category": "Sensors"
                }
            ],
            "budget": 5000
        }
        response = client.post("/api/restock-orders", json=payload)
        order = response.json()
        assert order["lead_time_days"] == 10

    def test_create_restock_order_total_value_calculation(self, client):
        """Test that total_value is the sum of quantity * unit_cost across items."""
        payload = {
            "items": [
                {"sku": "PSU-508", "name": "Battery Backup Power Supply", "quantity": 10, "unit_cost": 185.5, "warehouse": "Tokyo", "category": "Power Supplies"},
                {"sku": "GYR-207", "name": "Gyroscope Module", "quantity": 5, "unit_cost": 95.0, "warehouse": "Tokyo", "category": "Sensors"}
            ],
            "budget": 5000
        }
        response = client.post("/api/restock-orders", json=payload)
        order = response.json()

        expected_total = round(10 * 185.5 + 5 * 95.0, 2)
        assert abs(order["total_value"] - expected_total) < 0.01

    def test_create_restock_order_multiple_warehouses_uses_max_lead_time(self, client):
        """Test that a multi-warehouse order uses the slowest warehouse's lead time and null warehouse/category."""
        payload = {
            "items": [
                {"sku": "PSU-501", "name": "5V 10A Switching Power Supply", "quantity": 5, "unit_cost": 18.99, "warehouse": "San Francisco", "category": "Power Supplies"},
                {"sku": "GYR-207", "name": "Gyroscope Module", "quantity": 5, "unit_cost": 95.0, "warehouse": "Tokyo", "category": "Sensors"}
            ],
            "budget": 5000
        }
        response = client.post("/api/restock-orders", json=payload)
        order = response.json()

        assert order["lead_time_days"] == 12  # Tokyo is slower than San Francisco
        assert order["warehouse"] is None
        assert order["category"] is None

    def test_restock_order_appears_in_get_orders(self, client):
        """Test that a submitted restock order is retrievable via GET /api/orders."""
        payload = {
            "items": [
                {"sku": "MCU-401", "name": "8-bit Microcontroller", "quantity": 50, "unit_cost": 8.25, "warehouse": "San Francisco", "category": "Controllers"}
            ],
            "budget": 5000
        }
        create_response = client.post("/api/restock-orders", json=payload)
        created_order = create_response.json()

        list_response = client.get("/api/orders?status=Submitted")
        assert list_response.status_code == 200
        order_numbers = [o["order_number"] for o in list_response.json()]
        assert created_order["order_number"] in order_numbers

    def test_restock_order_unique_id_and_order_number(self, client):
        """Test that placing two restock orders produces distinct ids and order numbers."""
        payload = {
            "items": [
                {"sku": "DSP-403", "name": "Digital Signal Processor", "quantity": 20, "unit_cost": 7.75, "warehouse": "London", "category": "Controllers"}
            ],
            "budget": 5000
        }
        first = client.post("/api/restock-orders", json=payload).json()
        second = client.post("/api/restock-orders", json=payload).json()

        assert first["id"] != second["id"]
        assert first["order_number"] != second["order_number"]
