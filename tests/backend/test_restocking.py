"""
Tests for restocking API endpoints.
"""
import pytest
from datetime import datetime, timedelta


class TestRestockingEndpoints:
    """Test suite for restocking-related endpoints."""

    def test_get_restocking_orders_empty_initially(self, client):
        """Test that restocking orders list is empty on fresh app."""
        response = client.get("/api/restocking-orders")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_create_restocking_order_happy_path(self, client):
        """Test creating a restocking order with valid items."""
        order_payload = {
            "items": [
                {
                    "sku": "PCB-001",
                    "name": "Single Layer PCB Assembly",
                    "quantity": 150,
                    "unit_cost": 24.99
                },
                {
                    "sku": "PRX-204",
                    "name": "Proximity Sensor",
                    "quantity": 2,
                    "unit_cost": 8.5
                }
            ],
            "warehouse": "San Francisco",
            "category": "Circuit Boards"
        }
        response = client.post("/api/restocking-orders", json=order_payload)
        assert response.status_code == 201

        order = response.json()
        # Verify structure
        assert "id" in order
        assert "order_number" in order
        assert order["order_number"].startswith("RSO-")
        assert "items" in order
        assert len(order["items"]) == 2
        assert "total_cost" in order
        assert "order_date" in order
        assert "expected_delivery" in order
        assert "lead_time_days" in order
        assert order["lead_time_days"] == 14
        assert "status" in order
        assert order["status"] == "Processing"
        assert order["warehouse"] == "San Francisco"
        assert order["category"] == "Circuit Boards"

        # Verify calculations
        expected_total = (150 * 24.99) + (2 * 8.5)
        assert abs(order["total_cost"] - expected_total) < 0.01

        # Verify subtotals
        assert abs(order["items"][0]["subtotal"] - (150 * 24.99)) < 0.01
        assert abs(order["items"][1]["subtotal"] - (2 * 8.5)) < 0.01

        # Verify dates are ISO format and lead time is correct
        order_date = datetime.fromisoformat(order["order_date"])
        expected_delivery = datetime.fromisoformat(order["expected_delivery"])
        delta = expected_delivery - order_date
        assert delta.days == 14

    def test_create_restocking_order_empty_items_rejected(self, client):
        """Test that creating an order with empty items is rejected."""
        order_payload = {
            "items": [],
            "warehouse": "Tokyo",
            "category": "Power Supplies"
        }
        response = client.post("/api/restocking-orders", json=order_payload)
        assert response.status_code == 400

        error = response.json()
        assert "detail" in error
        assert "at least one item" in error["detail"].lower()

    def test_get_restocking_orders_after_create(self, client):
        """Test that created order appears in GET list."""
        # Get initial count
        initial_response = client.get("/api/restocking-orders")
        initial_count = len(initial_response.json())

        # Create order
        order_payload = {
            "items": [
                {
                    "sku": "PCB-001",
                    "name": "Single Layer PCB Assembly",
                    "quantity": 100,
                    "unit_cost": 24.99
                }
            ],
            "warehouse": "San Francisco",
            "category": "Circuit Boards"
        }
        create_response = client.post("/api/restocking-orders", json=order_payload)
        assert create_response.status_code == 201
        created_order = create_response.json()

        # Get all orders and verify the created one is there
        get_response = client.get("/api/restocking-orders")
        assert get_response.status_code == 200

        orders = get_response.json()
        assert len(orders) == initial_count + 1
        # Find the created order in the list by matching its ID
        found_order = next((o for o in orders if o["id"] == created_order["id"]), None)
        assert found_order is not None
        assert found_order["order_number"] == created_order["order_number"]

    def test_get_restocking_orders_filtered_by_warehouse(self, client):
        """Test filtering restocking orders by warehouse."""
        # Create order for London (unique warehouse for this test)
        order_london = {
            "items": [
                {
                    "sku": "TMP-201",
                    "name": "Temperature Sensor Module",
                    "quantity": 75,
                    "unit_cost": 89.5
                }
            ],
            "warehouse": "London",
            "category": "Sensors"
        }
        response1 = client.post("/api/restocking-orders", json=order_london)
        assert response1.status_code == 201
        london_order = response1.json()

        # Create second order for London to verify multiple filtering
        order_london2 = {
            "items": [
                {
                    "sku": "PSU-502",
                    "name": "12V 5A Power Supply Module",
                    "quantity": 30,
                    "unit_cost": 22.5
                }
            ],
            "warehouse": "London",
            "category": "Power Supplies"
        }
        response2 = client.post("/api/restocking-orders", json=order_london2)
        assert response2.status_code == 201

        # Filter by London and verify we get at least our two orders
        get_response = client.get("/api/restocking-orders?warehouse=London")
        assert get_response.status_code == 200

        orders = get_response.json()
        # Verify both our London orders are in the results
        london_ids = {london_order["id"], response2.json()["id"]}
        returned_ids = {o["id"] for o in orders}
        assert london_ids.issubset(returned_ids)

        # Verify all returned orders have London as warehouse
        for order in orders:
            assert order["warehouse"] == "London"

    def test_restocking_order_item_structure(self, client):
        """Test that order items have proper structure."""
        order_payload = {
            "items": [
                {
                    "sku": "PSU-501",
                    "name": "5V 10A Switching Power Supply",
                    "quantity": 25,
                    "unit_cost": 18.99
                }
            ]
        }
        response = client.post("/api/restocking-orders", json=order_payload)
        assert response.status_code == 201

        order = response.json()
        assert "items" in order
        assert isinstance(order["items"], list)

        item = order["items"][0]
        assert "sku" in item
        assert "name" in item
        assert "quantity" in item
        assert "unit_cost" in item
        assert "subtotal" in item
        assert isinstance(item["quantity"], int)
        assert isinstance(item["unit_cost"], (int, float))
        assert isinstance(item["subtotal"], (int, float))
        assert item["subtotal"] > 0

    def test_restocking_order_total_cost_calculation(self, client):
        """Test that order total cost is calculated correctly."""
        order_payload = {
            "items": [
                {
                    "sku": "PCB-001",
                    "name": "Single Layer PCB Assembly",
                    "quantity": 100,
                    "unit_cost": 24.99
                },
                {
                    "sku": "PRX-204",
                    "name": "Proximity Sensor",
                    "quantity": 50,
                    "unit_cost": 8.5
                }
            ]
        }
        response = client.post("/api/restocking-orders", json=order_payload)
        assert response.status_code == 201

        order = response.json()
        # Calculate expected total from items
        calculated_total = sum(
            item["quantity"] * item["unit_cost"]
            for item in order["items"]
        )
        # Allow small floating point differences
        assert abs(order["total_cost"] - calculated_total) < 0.01
