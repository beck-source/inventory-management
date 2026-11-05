"""
Tests for orders API endpoints, including the restocking order creation
(POST /api/orders) and the demand-forecast cost fields that drive it.
"""
from datetime import datetime, timedelta


def _valid_order_payload():
    """A valid CreateOrderRequest body for a restocking order."""
    return {
        "items": [
            {"sku": "WDG-001", "name": "Industrial Widget Type A", "quantity": 150, "unit_price": 12.50},
            {"sku": "GSK-203", "name": "High-Temperature Gasket", "quantity": 100, "unit_price": 4.25},
        ],
        "total_value": 150 * 12.50 + 100 * 4.25,
        "lead_time_days": 10,
    }


class TestDemandForecastCostFields:
    """The Restocking feature adds unit_cost and lead_time_days to demand forecasts."""

    def test_demand_includes_cost_and_lead_time(self, client):
        """Every demand forecast should expose unit_cost and lead_time_days."""
        response = client.get("/api/demand")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        for forecast in data:
            assert "unit_cost" in forecast
            assert "lead_time_days" in forecast
            assert isinstance(forecast["unit_cost"], (int, float))
            assert isinstance(forecast["lead_time_days"], int)
            assert forecast["unit_cost"] >= 0
            assert forecast["lead_time_days"] >= 0


class TestCreateOrderEndpoint:
    """Test suite for POST /api/orders (restocking order submission)."""

    def test_create_order_returns_201(self, client):
        """Submitting a valid restocking order returns 201 with the created order."""
        response = client.post("/api/orders", json=_valid_order_payload())
        assert response.status_code == 201

        order = response.json()
        assert order["status"] == "Submitted"
        assert order["order_number"].startswith("ORD-2025-")
        assert order["customer"] == "Restocking (Internal)"
        assert order["lead_time_days"] == 10
        assert len(order["items"]) == 2
        assert order["actual_delivery"] is None

    def test_expected_delivery_matches_lead_time(self, client):
        """expected_delivery should equal order_date + lead_time_days."""
        payload = _valid_order_payload()
        response = client.post("/api/orders", json=payload)
        assert response.status_code == 201

        order = response.json()
        order_date = datetime.fromisoformat(order["order_date"])
        expected = datetime.fromisoformat(order["expected_delivery"])
        assert expected - order_date == timedelta(days=payload["lead_time_days"])

    def test_created_order_appears_in_list(self, client):
        """A submitted order is appended to the in-memory list and shows up in GET /api/orders."""
        before = client.get("/api/orders").json()

        create = client.post("/api/orders", json=_valid_order_payload())
        assert create.status_code == 201
        new_number = create.json()["order_number"]

        after = client.get("/api/orders").json()
        assert len(after) == len(before) + 1
        assert any(o["order_number"] == new_number for o in after)

    def test_submitted_order_is_retrievable_by_id(self, client):
        """The new order can be fetched individually via GET /api/orders/{id}."""
        new_id = client.post("/api/orders", json=_valid_order_payload()).json()["id"]
        response = client.get(f"/api/orders/{new_id}")
        assert response.status_code == 200
        assert response.json()["id"] == new_id

    def test_order_numbers_are_unique_across_submissions(self, client):
        """Two submissions must not collide on order_number."""
        first = client.post("/api/orders", json=_valid_order_payload()).json()
        second = client.post("/api/orders", json=_valid_order_payload()).json()
        assert first["order_number"] != second["order_number"]
        assert first["id"] != second["id"]

    def test_create_order_missing_items_returns_422(self, client):
        """A body without items fails Pydantic validation."""
        response = client.post("/api/orders", json={"total_value": 100, "lead_time_days": 5})
        assert response.status_code == 422

    def test_create_order_invalid_item_types_returns_422(self, client):
        """Non-numeric quantity should fail validation."""
        bad = {
            "items": [{"sku": "WDG-001", "name": "Widget", "quantity": "lots", "unit_price": 12.5}],
            "total_value": 100,
            "lead_time_days": 5,
        }
        response = client.post("/api/orders", json=bad)
        assert response.status_code == 422
