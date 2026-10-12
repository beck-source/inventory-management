"""
Tests for restocking API endpoints (budget recommendations and submitted restock orders).
"""
import pytest

import mock_data


@pytest.fixture(autouse=True)
def clear_submitted_orders():
    """Reset the in-memory submitted restock orders so each test starts from a clean slate."""
    mock_data.submitted_restock_orders.clear()
    yield
    mock_data.submitted_restock_orders.clear()


class TestRestockRecommendationEndpoint:
    """Test suite for GET /api/restock/recommendations."""

    def test_get_recommendations_structure(self, client):
        """Test that a recommendation response has the expected shape."""
        response = client.get("/api/restock/recommendations?budget=100000")
        assert response.status_code == 200

        data = response.json()
        assert data["budget"] == 100000
        assert isinstance(data["items"], list)
        assert isinstance(data["unfunded_items"], list)
        assert len(data["items"]) > 0

        first_item = data["items"][0]
        for field in [
            "item_sku", "item_name", "category", "trend", "forecasted_demand",
            "quantity_on_hand", "shortfall", "recommended_quantity", "unit_cost",
            "line_total", "lead_time_days", "fully_funded"
        ]:
            assert field in first_item

    def test_recommendations_respect_budget(self, client):
        """Test that the allocated total never exceeds the requested budget."""
        for budget in [0, 5000, 25000, 100000, 500000]:
            response = client.get(f"/api/restock/recommendations?budget={budget}")
            assert response.status_code == 200

            data = response.json()
            assert data["total_cost"] <= budget + 0.01
            assert abs(data["remaining_budget"] - (budget - data["total_cost"])) < 0.01

    def test_zero_budget_recommends_nothing(self, client):
        """Test that a zero budget funds no items but still reports the shortfalls."""
        response = client.get("/api/restock/recommendations?budget=0")
        assert response.status_code == 200

        data = response.json()
        assert data["items"] == []
        assert data["total_cost"] == 0
        assert data["total_units"] == 0
        assert data["max_lead_time_days"] == 0
        assert len(data["unfunded_items"]) > 0

    def test_negative_budget_rejected(self, client):
        """Test that a negative budget fails validation."""
        response = client.get("/api/restock/recommendations?budget=-100")
        assert response.status_code == 422

    def test_recommendations_sorted_by_shortfall(self, client):
        """Test that items are ranked by shortfall, largest gap first."""
        response = client.get("/api/restock/recommendations?budget=500000")
        data = response.json()

        shortfalls = [item["shortfall"] for item in data["items"]]
        assert shortfalls == sorted(shortfalls, reverse=True)

    def test_line_totals_and_aggregates(self, client):
        """Test that line totals and response aggregates are internally consistent."""
        response = client.get("/api/restock/recommendations?budget=100000")
        data = response.json()

        for item in data["items"]:
            expected = item["recommended_quantity"] * item["unit_cost"]
            assert abs(item["line_total"] - expected) < 0.01
            assert 0 < item["recommended_quantity"] <= item["shortfall"]
            assert item["fully_funded"] == (item["recommended_quantity"] == item["shortfall"])
            assert item["lead_time_days"] > 0

        assert abs(data["total_cost"] - sum(i["line_total"] for i in data["items"])) < 0.01
        assert data["total_units"] == sum(i["recommended_quantity"] for i in data["items"])
        assert data["max_lead_time_days"] == max(i["lead_time_days"] for i in data["items"])

    def test_only_items_with_a_shortfall_are_recommended(self, client):
        """Test that items already stocked above forecast demand are excluded."""
        response = client.get("/api/restock/recommendations?budget=500000")
        data = response.json()

        recommended_and_unfunded = (
            [i["item_sku"] for i in data["items"]] +
            [i["item_sku"] for i in data["unfunded_items"]]
        )

        inventory = client.get("/api/inventory").json()
        for forecast in client.get("/api/demand").json():
            on_hand = sum(
                item["quantity_on_hand"] for item in inventory
                if item["sku"] == forecast["item_sku"]
            )
            if forecast["forecasted_demand"] - on_hand <= 0:
                assert forecast["item_sku"] not in recommended_and_unfunded

    def test_larger_budget_never_funds_less(self, client):
        """Test that raising the budget never reduces the units ordered."""
        small = client.get("/api/restock/recommendations?budget=25000").json()
        large = client.get("/api/restock/recommendations?budget=250000").json()

        assert large["total_units"] >= small["total_units"]
        assert large["total_cost"] >= small["total_cost"]

    def test_demand_forecast_exposes_cost_and_category(self, client):
        """Test that the demand endpoint carries the fields the recommender relies on."""
        response = client.get("/api/demand")
        assert response.status_code == 200

        for forecast in response.json():
            assert isinstance(forecast["unit_cost"], (int, float))
            assert forecast["unit_cost"] > 0
            assert isinstance(forecast["category"], str)
            assert forecast["category"]


class TestSubmittedRestockOrderEndpoints:
    """Test suite for GET/POST /api/restock-orders."""

    @staticmethod
    def _submit(client, budget=100000):
        """Build a recommendation for a budget and submit it as an order."""
        recommendation = client.get(f"/api/restock/recommendations?budget={budget}").json()
        return client.post("/api/restock-orders", json={
            "budget": recommendation["budget"],
            "items": recommendation["items"]
        })

    def test_no_orders_initially(self, client):
        """Test that no restock orders exist before any are submitted."""
        response = client.get("/api/restock-orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_restock_order(self, client):
        """Test submitting a restocking order built from recommendations."""
        response = self._submit(client)
        assert response.status_code == 201

        order = response.json()
        assert order["order_number"].startswith("RST-")
        assert order["status"] == "Submitted"
        assert order["budget"] == 100000
        assert order["total_value"] <= 100000 + 0.01
        assert order["lead_time_days"] > 0
        assert "T" in order["order_date"]
        assert "T" in order["expected_delivery"]
        assert order["expected_delivery"] > order["order_date"]

    def test_created_order_items_structure(self, client):
        """Test that submitted order items use the same shape as regular order items."""
        order = self._submit(client).json()
        assert len(order["items"]) > 0

        for item in order["items"]:
            for field in ["sku", "name", "category", "quantity", "unit_price",
                          "line_total", "lead_time_days", "expected_delivery"]:
                assert field in item
            assert item["quantity"] > 0
            assert abs(item["line_total"] - item["quantity"] * item["unit_price"]) < 0.01

        assert order["total_units"] == sum(i["quantity"] for i in order["items"])
        assert abs(order["total_value"] - sum(i["line_total"] for i in order["items"])) < 0.01

    def test_order_lead_time_is_slowest_item(self, client):
        """Test that the order-level lead time is the slowest line item's lead time."""
        order = self._submit(client).json()
        assert order["lead_time_days"] == max(i["lead_time_days"] for i in order["items"])

    def test_submitted_orders_returned_newest_first(self, client):
        """Test that the list endpoint returns the most recent order first."""
        first = self._submit(client, budget=50000).json()
        second = self._submit(client, budget=100000).json()

        response = client.get("/api/restock-orders")
        assert response.status_code == 200

        orders = response.json()
        assert [o["order_number"] for o in orders] == [second["order_number"], first["order_number"]]

    def test_order_numbers_increment(self, client):
        """Test that order numbers are sequential per submission."""
        first = self._submit(client).json()
        second = self._submit(client).json()

        assert first["order_number"] != second["order_number"]
        assert first["order_number"].endswith("0001")
        assert second["order_number"].endswith("0002")

    def test_create_order_with_no_items_rejected(self, client):
        """Test that submitting an empty restocking order returns 400."""
        response = client.post("/api/restock-orders", json={"budget": 1000, "items": []})
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert "no items" in data["detail"].lower()

    def test_create_order_with_malformed_item_rejected(self, client):
        """Test that an item missing required fields fails validation."""
        response = client.post("/api/restock-orders", json={
            "budget": 1000,
            "items": [{"item_sku": "WDG-001"}]
        })
        assert response.status_code == 422
