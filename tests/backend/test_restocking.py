"""
Tests for restock order API endpoints.
"""
from datetime import datetime, timedelta

import pytest


@pytest.fixture
def sample_restock_items():
    """Two restock lines with distinct lead times, for range assertions."""
    return [
        {
            "sku": "WDG-001",
            "name": "Industrial Widget Type A",
            "quantity": 180,
            "unit_cost": 34.50,
            "lead_time_days": 10
        },
        {
            "sku": "MTR-304",
            "name": "Electric Motor 5HP",
            "quantity": 42,
            "unit_cost": 485.00,
            "lead_time_days": 21
        }
    ]


@pytest.fixture
def restock_baseline(client):
    """
    Number of restock orders that already exist.

    Submitted restock orders are held in a module-level list in main.py, so it
    is shared across every test in the session and is NOT reset between tests.
    Tests must assert on deltas from this baseline rather than absolute counts.
    """
    response = client.get("/api/restock-orders")
    assert response.status_code == 200
    return len(response.json())


class TestRestockOrderEndpoints:
    """Test suite for restock-order endpoints."""

    def test_get_restock_orders(self, client):
        """Test getting submitted restock orders."""
        response = client.get("/api/restock-orders")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_create_restock_order(self, client, sample_restock_items, restock_baseline):
        """Test submitting a valid restock order."""
        expected_total = sum(
            item["quantity"] * item["unit_cost"] for item in sample_restock_items
        )

        response = client.post("/api/restock-orders", json={
            "budget": 100000,
            "items": sample_restock_items
        })
        assert response.status_code == 200

        order = response.json()
        assert order["status"] == "Submitted"
        assert order["budget"] == 100000
        assert len(order["items"]) == len(sample_restock_items)
        assert abs(order["total_cost"] - expected_total) < 0.01

    def test_create_restock_order_number_format(self, client, sample_restock_items):
        """Test that a submitted order gets an RO-YYYY-NNNN order number."""
        response = client.post("/api/restock-orders", json={
            "budget": 100000,
            "items": sample_restock_items
        })
        assert response.status_code == 200

        order_number = response.json()["order_number"]
        assert order_number.startswith("RO-")

        prefix, year, sequence = order_number.split("-")
        assert prefix == "RO"
        assert year == str(datetime.now().year)
        assert len(sequence) == 4
        assert sequence.isdigit()

    def test_create_restock_order_lead_time_range(self, client, sample_restock_items):
        """Test that lead times are derived from the item set."""
        response = client.post("/api/restock-orders", json={
            "budget": 100000,
            "items": sample_restock_items
        })
        assert response.status_code == 200

        order = response.json()
        lead_times = [item["lead_time_days"] for item in sample_restock_items]
        assert order["min_lead_time_days"] == min(lead_times)
        assert order["max_lead_time_days"] == max(lead_times)

    def test_create_restock_order_estimated_delivery(self, client, sample_restock_items):
        """Test that estimated delivery uses the longest lead time in the basket."""
        response = client.post("/api/restock-orders", json={
            "budget": 100000,
            "items": sample_restock_items
        })
        assert response.status_code == 200

        order = response.json()
        submitted = datetime.strptime(order["submitted_date"], "%Y-%m-%dT%H:%M:%S")
        expected = (submitted + timedelta(days=order["max_lead_time_days"])).strftime("%Y-%m-%d")
        assert order["estimated_delivery"] == expected

    def test_create_restock_order_single_item_lead_time(self, client):
        """Test that min and max lead time match for a single-line order."""
        response = client.post("/api/restock-orders", json={
            "budget": 5000,
            "items": [{
                "sku": "GSK-203",
                "name": "High-Temperature Gasket",
                "quantity": 100,
                "unit_cost": 12.80,
                "lead_time_days": 7
            }]
        })
        assert response.status_code == 200

        order = response.json()
        assert order["min_lead_time_days"] == 7
        assert order["max_lead_time_days"] == 7

    def test_submitted_order_appears_in_list(self, client, sample_restock_items, restock_baseline):
        """Test that a submitted order is returned by the GET endpoint."""
        post_response = client.post("/api/restock-orders", json={
            "budget": 100000,
            "items": sample_restock_items
        })
        assert post_response.status_code == 200
        order_number = post_response.json()["order_number"]

        get_response = client.get("/api/restock-orders")
        assert get_response.status_code == 200

        data = get_response.json()
        assert len(data) == restock_baseline + 1
        assert order_number in [order["order_number"] for order in data]

    def test_restock_orders_newest_first(self, client, sample_restock_items):
        """Test that the list returns the most recently submitted order first."""
        client.post("/api/restock-orders", json={
            "budget": 100000,
            "items": sample_restock_items
        })
        second = client.post("/api/restock-orders", json={
            "budget": 100000,
            "items": sample_restock_items
        })
        assert second.status_code == 200

        data = client.get("/api/restock-orders").json()
        assert data[0]["order_number"] == second.json()["order_number"]

    def test_create_restock_order_over_budget(self, client, sample_restock_items):
        """Test that an order exceeding the budget is rejected."""
        response = client.post("/api/restock-orders", json={
            "budget": 100,
            "items": sample_restock_items
        })
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert "exceeds budget" in data["detail"].lower()

    def test_create_restock_order_empty_items(self, client):
        """Test that an order with no items is rejected."""
        response = client.post("/api/restock-orders", json={
            "budget": 50000,
            "items": []
        })
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert "at least one item" in data["detail"].lower()

    def test_create_restock_order_zero_quantity(self, client):
        """Test that a zero-quantity line is rejected."""
        response = client.post("/api/restock-orders", json={
            "budget": 50000,
            "items": [{
                "sku": "GSK-203",
                "name": "High-Temperature Gasket",
                "quantity": 0,
                "unit_cost": 12.80,
                "lead_time_days": 7
            }]
        })
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert "greater than zero" in data["detail"].lower()

    def test_total_cost_recomputed_server_side(self, client, sample_restock_items):
        """Test that a client-supplied total_cost is ignored, not trusted."""
        expected_total = sum(
            item["quantity"] * item["unit_cost"] for item in sample_restock_items
        )

        response = client.post("/api/restock-orders", json={
            "budget": 100000,
            "total_cost": 1.0,  # Bogus value the server must ignore
            "items": sample_restock_items
        })
        assert response.status_code == 200

        assert abs(response.json()["total_cost"] - expected_total) < 0.01

    def test_create_restock_order_missing_field(self, client):
        """Test that a malformed item fails Pydantic validation."""
        response = client.post("/api/restock-orders", json={
            "budget": 50000,
            "items": [{"sku": "GSK-203", "quantity": 10}]
        })
        assert response.status_code == 422

    def test_restock_order_data_types(self, client, sample_restock_items):
        """Test that a submitted order has correctly typed fields."""
        response = client.post("/api/restock-orders", json={
            "budget": 100000,
            "items": sample_restock_items
        })
        assert response.status_code == 200

        order = response.json()
        assert isinstance(order["id"], str)
        assert isinstance(order["order_number"], str)
        assert isinstance(order["total_cost"], (int, float))
        assert isinstance(order["budget"], (int, float))
        assert isinstance(order["min_lead_time_days"], int)
        assert isinstance(order["max_lead_time_days"], int)
        assert isinstance(order["items"], list)
        assert order["total_cost"] > 0
        assert order["min_lead_time_days"] > 0

        for item in order["items"]:
            assert isinstance(item["sku"], str)
            assert isinstance(item["quantity"], int)
            assert isinstance(item["unit_cost"], (int, float))
            assert isinstance(item["lead_time_days"], int)


class TestInventoryLeadTime:
    """Test suite for the lead_time_days field added for restocking."""

    def test_inventory_items_have_lead_time(self, client):
        """Test that every inventory item exposes a usable lead time."""
        response = client.get("/api/inventory")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0

        for item in data:
            assert "lead_time_days" in item
            assert isinstance(item["lead_time_days"], int)
            assert item["lead_time_days"] > 0

    def test_demand_forecast_skus_exist_in_inventory(self, client):
        """Test that every forecast SKU joins to inventory, so restocking can price it."""
        inventory_skus = {item["sku"] for item in client.get("/api/inventory").json()}
        forecasts = client.get("/api/demand").json()
        assert len(forecasts) > 0

        for forecast in forecasts:
            assert forecast["item_sku"] in inventory_skus, (
                f"Forecast SKU {forecast['item_sku']} has no inventory record, "
                "so the restocking recommender cannot price it"
            )
