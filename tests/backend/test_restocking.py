"""
Tests for restocking-order API endpoints and demand-forecast enrichment.
"""
import pytest


@pytest.fixture
def sample_restocking_request():
    """A valid create-restocking-order request body.

    Mechanical Components lead time is 18 days and Sensors is 7, so the order's
    lead time should resolve to 18 (the slowest item gates the order).
    """
    return {
        "budget": 10000,
        "warehouse": "San Francisco",
        "items": [
            {
                "sku": "GSK-203",
                "name": "High-Temperature Gasket",
                "category": "Mechanical Components",
                "quantity": 600,
                "unit_cost": 8.75,
            },
            {
                "sku": "SNR-420",
                "name": "Temperature Sensor Module",
                "category": "Sensors",
                "quantity": 100,
                "unit_cost": 28.50,
            },
        ],
    }


class TestDemandForecastEnrichment:
    """The Restocking tab depends on category + unit_cost on each forecast."""

    def test_demand_includes_category_and_unit_cost(self, client):
        """Every demand forecast must expose category and a positive unit_cost."""
        response = client.get("/api/demand")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        for forecast in data:
            assert "category" in forecast
            assert "unit_cost" in forecast
            assert isinstance(forecast["unit_cost"], (int, float))
            assert forecast["unit_cost"] > 0


class TestRestockingOrderEndpoints:
    """Test suite for restocking-order creation and retrieval."""

    def test_get_restocking_orders_returns_list(self, client):
        """Getting restocking orders returns a list (possibly empty)."""
        response = client.get("/api/restocking-orders")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_restocking_order(self, client, sample_restocking_request):
        """Submitting a valid order returns 201 with a fully-computed order."""
        response = client.post("/api/restocking-orders", json=sample_restocking_request)
        assert response.status_code == 201

        order = response.json()
        assert order["id"].startswith("RO-")
        assert order["status"] == "Submitted"
        assert order["budget"] == 10000
        assert order["warehouse"] == "San Francisco"
        assert "created_at" in order
        assert "expected_delivery" in order
        assert len(order["items"]) == 2

    def test_line_totals_and_total_cost(self, client, sample_restocking_request):
        """Line totals = qty * unit_cost, and total_cost = sum of line totals."""
        response = client.post("/api/restocking-orders", json=sample_restocking_request)
        order = response.json()

        for item in order["items"]:
            expected_line = item["quantity"] * item["unit_cost"]
            assert abs(item["line_total"] - expected_line) < 0.01

        expected_total = sum(item["line_total"] for item in order["items"])
        assert abs(order["total_cost"] - expected_total) < 0.01
        # 600 * 8.75 + 100 * 28.50 = 5250 + 2850 = 8100
        assert abs(order["total_cost"] - 8100.0) < 0.01

    def test_lead_time_is_max_across_categories(self, client, sample_restocking_request):
        """Order lead time is the slowest item's category lead time (18 for Mech Components)."""
        response = client.post("/api/restocking-orders", json=sample_restocking_request)
        order = response.json()
        assert order["lead_time_days"] == 18

    def test_expected_delivery_matches_lead_time(self, client, sample_restocking_request):
        """expected_delivery must equal created_at date + lead_time_days."""
        from datetime import datetime, timedelta

        response = client.post("/api/restocking-orders", json=sample_restocking_request)
        order = response.json()

        created_date = datetime.fromisoformat(order["created_at"]).date()
        expected = created_date + timedelta(days=order["lead_time_days"])
        assert order["expected_delivery"] == expected.strftime("%Y-%m-%d")

    def test_pure_category_lead_time_not_floored_by_default(self, client):
        """A single-category order must use that category's lead time, not the
        14-day default. Sensors = 7; a Sensors-only order must report 7, not 14.
        """
        response = client.post(
            "/api/restocking-orders",
            json={
                "budget": 5000,
                "warehouse": "London",
                "items": [
                    {
                        "sku": "SNR-420",
                        "name": "Temperature Sensor Module",
                        "category": "Sensors",
                        "quantity": 10,
                        "unit_cost": 28.50,
                    }
                ],
            },
        )
        assert response.status_code == 201
        assert response.json()["lead_time_days"] == 7

    def test_unknown_category_uses_default_lead_time(self, client):
        """A category not in the lead-time map falls back to the 14-day default."""
        response = client.post(
            "/api/restocking-orders",
            json={
                "budget": 5000,
                "warehouse": "London",
                "items": [
                    {
                        "sku": "XYZ-999",
                        "name": "Mystery Part",
                        "category": "Nonexistent Category",
                        "quantity": 10,
                        "unit_cost": 5.0,
                    }
                ],
            },
        )
        assert response.status_code == 201
        assert response.json()["lead_time_days"] == 14

    def test_submitted_order_appears_in_get(self, client, sample_restocking_request):
        """A submitted order is retrievable via GET afterwards."""
        create = client.post("/api/restocking-orders", json=sample_restocking_request)
        created_id = create.json()["id"]

        response = client.get("/api/restocking-orders")
        ids = [o["id"] for o in response.json()]
        assert created_id in ids

    def test_warehouse_filter(self, client):
        """The warehouse query param filters submitted orders."""
        client.post(
            "/api/restocking-orders",
            json={
                "budget": 5000,
                "warehouse": "Tokyo",
                "items": [
                    {
                        "sku": "CTL-330",
                        "name": "Logic Controller Board",
                        "category": "Controllers",
                        "quantity": 5,
                        "unit_cost": 95.0,
                    }
                ],
            },
        )
        response = client.get("/api/restocking-orders?warehouse=Tokyo")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        for order in data:
            assert order["warehouse"] == "Tokyo"

    def test_empty_order_rejected(self, client):
        """An order with no items returns 400."""
        response = client.post(
            "/api/restocking-orders",
            json={"budget": 1000, "warehouse": "London", "items": []},
        )
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_invalid_quantity_rejected(self, client):
        """An item with a non-positive quantity returns 400."""
        response = client.post(
            "/api/restocking-orders",
            json={
                "budget": 1000,
                "warehouse": "London",
                "items": [
                    {
                        "sku": "CTL-330",
                        "name": "Logic Controller Board",
                        "category": "Controllers",
                        "quantity": 0,
                        "unit_cost": 95.0,
                    }
                ],
            },
        )
        assert response.status_code == 400

    def test_missing_required_fields_returns_422(self, client):
        """A malformed body (missing items entirely) returns a validation error."""
        response = client.post("/api/restocking-orders", json={"budget": 1000})
        assert response.status_code == 422
