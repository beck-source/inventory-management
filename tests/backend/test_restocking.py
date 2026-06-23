"""
Tests for restocking API endpoints (recommendations and submitted orders).
"""
import pytest


class TestRestockingRecommendations:
    """Test suite for the restocking recommendations endpoint."""

    def test_get_recommendations_returns_200_and_structure(self, client):
        """Test that recommendations are returned with the expected response shape."""
        response = client.get("/api/restocking/recommendations", params={"budget": 100000})
        assert response.status_code == 200

        data = response.json()
        assert "recommendations" in data
        assert "total_budget" in data
        assert "total_allocated" in data
        assert "remaining_budget" in data
        assert "item_count" in data
        assert isinstance(data["recommendations"], list)
        assert data["item_count"] == len(data["recommendations"])

        if len(data["recommendations"]) > 0:
            item = data["recommendations"][0]
            assert "sku" in item
            assert "item_name" in item
            assert "category" in item
            assert "warehouse" in item
            assert "current_demand" in item
            assert "forecasted_demand" in item
            assert "trend" in item
            assert "suggested_quantity" in item
            assert "unit_cost" in item
            assert "total_cost" in item

    def test_recommendations_respect_budget(self, client):
        """Test that the sum of recommended item costs never exceeds the given budget."""
        budget = 200.0
        response = client.get("/api/restocking/recommendations", params={"budget": budget})
        data = response.json()

        total_cost = sum(item["total_cost"] for item in data["recommendations"])
        assert total_cost <= budget
        assert abs(data["total_allocated"] - total_cost) < 0.01

    def test_recommendations_skip_non_positive_gap_items(self, client):
        """Test that items with forecasted demand not exceeding current demand are excluded."""
        response = client.get("/api/restocking/recommendations", params={"budget": 1000000})
        data = response.json()

        for item in data["recommendations"]:
            assert item["forecasted_demand"] - item["current_demand"] > 0
            assert item["suggested_quantity"] == item["forecasted_demand"] - item["current_demand"]

    def test_recommendations_sorted_by_trend_then_gap(self, client):
        """Test that increasing-trend items are ranked before stable and decreasing items."""
        response = client.get("/api/restocking/recommendations", params={"budget": 1000000})
        data = response.json()

        trend_rank = {"increasing": 0, "stable": 1, "decreasing": 2}
        ranks = [trend_rank.get(item["trend"], 1) for item in data["recommendations"]]
        assert ranks == sorted(ranks)

    def test_recommendations_zero_budget_returns_empty(self, client):
        """Test that a zero budget produces no recommendations."""
        response = client.get("/api/restocking/recommendations", params={"budget": 0})
        assert response.status_code == 200

        data = response.json()
        assert data["recommendations"] == []
        assert data["item_count"] == 0
        assert data["remaining_budget"] == 0

    def test_recommendations_negative_budget_returns_400(self, client):
        """Test that a negative budget is rejected with a 400 error."""
        response = client.get("/api/restocking/recommendations", params={"budget": -50})
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data


class TestRestockingOrders:
    """Test suite for submitting and listing restocking orders."""

    def test_create_restocking_order_returns_201_and_records(self, client):
        """Test that submitting a restocking order creates a record with the expected fields."""
        payload = {
            "items": [
                {
                    "sku": "TEST-SKU-1",
                    "item_name": "Test Widget",
                    "quantity": 10,
                    "unit_cost": 5.0,
                    "warehouse": "San Francisco",
                    "category": "Sensors",
                }
            ]
        }
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 201

        data = response.json()
        assert len(data) == 1
        order = data[0]
        assert order["sku"] == "TEST-SKU-1"
        assert order["quantity"] == 10
        assert order["unit_cost"] == 5.0
        assert order["total_cost"] == 50.0
        assert order["status"] == "Submitted"
        assert "id" in order
        assert "order_date" in order
        assert "lead_time_days" in order

    def test_create_restocking_order_assigns_lead_time_by_category(self, client):
        """Test that the simulated lead time matches the fixed per-category mapping."""
        payload = {
            "items": [
                {
                    "sku": "TEST-SKU-2",
                    "item_name": "Test Sensor",
                    "quantity": 1,
                    "unit_cost": 1.0,
                    "warehouse": "Tokyo",
                    "category": "Sensors",
                }
            ]
        }
        response = client.post("/api/restocking/orders", json=payload)
        data = response.json()
        assert data[0]["lead_time_days"] == 7

    def test_create_restocking_order_unknown_category_uses_default_lead_time(self, client):
        """Test that an unmapped category falls back to the default lead time."""
        payload = {
            "items": [
                {
                    "sku": "TEST-SKU-3",
                    "item_name": "Test Unknown",
                    "quantity": 1,
                    "unit_cost": 1.0,
                    "warehouse": "London",
                    "category": "Unmapped Category",
                }
            ]
        }
        response = client.post("/api/restocking/orders", json=payload)
        data = response.json()
        assert data[0]["lead_time_days"] == 9

    def test_create_restocking_order_one_record_per_item(self, client):
        """Test that submitting multiple items creates one distinct record per item."""
        payload = {
            "items": [
                {
                    "sku": "TEST-SKU-4",
                    "item_name": "Test Item A",
                    "quantity": 2,
                    "unit_cost": 3.0,
                    "warehouse": "San Francisco",
                    "category": "Circuit Boards",
                },
                {
                    "sku": "TEST-SKU-5",
                    "item_name": "Test Item B",
                    "quantity": 4,
                    "unit_cost": 6.0,
                    "warehouse": "London",
                    "category": "Controllers",
                },
            ]
        }
        response = client.post("/api/restocking/orders", json=payload)
        data = response.json()

        assert len(data) == 2
        assert data[0]["id"] != data[1]["id"]
        skus = {order["sku"] for order in data}
        assert skus == {"TEST-SKU-4", "TEST-SKU-5"}

    def test_create_restocking_order_empty_items_returns_400(self, client):
        """Test that submitting an order with no items is rejected."""
        response = client.post("/api/restocking/orders", json={"items": []})
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data

    def test_get_restocking_orders_returns_created_orders(self, client):
        """Test that a submitted order appears when listing all restocking orders."""
        payload = {
            "items": [
                {
                    "sku": "TEST-SKU-6",
                    "item_name": "Test Listing Item",
                    "quantity": 7,
                    "unit_cost": 2.5,
                    "warehouse": "San Francisco",
                    "category": "Actuators",
                }
            ]
        }
        create_response = client.post("/api/restocking/orders", json=payload)
        created_id = create_response.json()[0]["id"]

        list_response = client.get("/api/restocking/orders")
        assert list_response.status_code == 200

        data = list_response.json()
        assert isinstance(data, list)
        assert any(order["id"] == created_id for order in data)
