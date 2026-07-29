"""
Tests for restocking API endpoints.
"""
import pytest


class TestRestockRecommendationsEndpoint:
    """Test suite for GET /api/restocking/recommendations."""

    def test_get_recommendations_structure(self, client):
        """Test the recommendations response has the expected top-level structure."""
        response = client.get("/api/restocking/recommendations?budget=1000")
        assert response.status_code == 200

        data = response.json()
        assert "budget" in data
        assert "items" in data
        assert "total_cost" in data
        assert "remaining_budget" in data
        assert "max_possible_cost" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) > 0

    def test_decreasing_trend_item_excluded(self, client):
        """MTR-304 (decreasing trend, forecasted < current) must never be recommended."""
        for budget in [0, 1000, 100000]:
            response = client.get(f"/api/restocking/recommendations?budget={budget}")
            data = response.json()
            skus = [item["item_sku"] for item in data["items"]]
            assert "MTR-304" not in skus

    def test_zero_budget_includes_nothing(self, client):
        """A budget of 0 should fund no items at all."""
        response = client.get("/api/restocking/recommendations?budget=0")
        assert response.status_code == 200

        data = response.json()
        assert data["total_cost"] == 0
        assert data["remaining_budget"] == 0
        for item in data["items"]:
            assert item["quantity_included"] == 0
            assert item["fully_funded"] is False

    def test_negative_budget_rejected(self, client):
        """A negative budget is invalid input."""
        response = client.get("/api/restocking/recommendations?budget=-100")
        assert response.status_code == 400

    def test_budget_5000_worked_example(self, client):
        """At a $5000 budget: FLT-405 and WDG-001 fully fund, GSK-203 partially
        funds (1 of 100 units), and every lower-ranked item gets zero."""
        response = client.get("/api/restocking/recommendations?budget=5000")
        assert response.status_code == 200

        data = response.json()
        items_by_sku = {item["item_sku"]: item for item in data["items"]}

        flt = items_by_sku["FLT-405"]
        assert flt["quantity_included"] == 150
        assert flt["fully_funded"] is True
        assert flt["subtotal"] == pytest.approx(1237.50)

        wdg = items_by_sku["WDG-001"]
        assert wdg["quantity_included"] == 150
        assert wdg["fully_funded"] is True
        assert wdg["subtotal"] == pytest.approx(3748.50)

        gsk = items_by_sku["GSK-203"]
        assert gsk["quantity_included"] == 1
        assert gsk["fully_funded"] is False
        assert gsk["subtotal"] == pytest.approx(12.75)

        # Every item ranked after the first partial fill gets zero, even
        # PSU-501 which is cheap enough it would otherwise fit in the leftover.
        for sku in ["PSU-501", "BRG-102", "SNR-420", "CTL-330", "VLV-506"]:
            assert items_by_sku[sku]["quantity_included"] == 0
            assert items_by_sku[sku]["fully_funded"] is False

        assert data["total_cost"] == pytest.approx(4998.75)
        assert data["remaining_budget"] == pytest.approx(1.25)

    def test_max_possible_cost_independent_of_budget(self, client):
        """max_possible_cost is the full cost of every eligible item and
        shouldn't change based on the requested budget."""
        low = client.get("/api/restocking/recommendations?budget=0").json()
        high = client.get("/api/restocking/recommendations?budget=100000").json()
        assert low["max_possible_cost"] == high["max_possible_cost"]
        assert low["max_possible_cost"] == pytest.approx(6857.98)

    def test_budget_exhausted_stops_all_further_funding(self, client):
        """Once the first item only partially fits, every lower-ranked item
        must get zero - even a cheap one that would technically still fit in
        the leftover. Regression test: at $6348.98, FLT-405/WDG-001/GSK-203/
        PSU-501 fully fund (total $6298.98), leaving $50.00. BRG-102 and
        SNR-420 (higher-ranked, $89.50/unit) can't afford a unit and must get
        zero - and CTL-330 (lower-ranked, $45.00/unit, would otherwise fit in
        the $50.00 leftover) must ALSO get zero rather than jumping the queue."""
        response = client.get("/api/restocking/recommendations?budget=6348.98")
        assert response.status_code == 200

        data = response.json()
        items_by_sku = {item["item_sku"]: item for item in data["items"]}

        for sku in ["FLT-405", "WDG-001", "GSK-203", "PSU-501"]:
            assert items_by_sku[sku]["fully_funded"] is True

        for sku in ["BRG-102", "SNR-420", "CTL-330", "VLV-506"]:
            assert items_by_sku[sku]["quantity_included"] == 0, \
                f"{sku} should get zero once budget is exhausted, not sneak in a partial fill"

        assert data["total_cost"] == pytest.approx(6298.98)
        assert data["remaining_budget"] == pytest.approx(50.00)

    def test_item_structure(self, client):
        """Each recommendation item has the expected fields and types."""
        response = client.get("/api/restocking/recommendations?budget=2000")
        data = response.json()

        for item in data["items"]:
            assert "item_sku" in item
            assert "item_name" in item
            assert "category" in item
            assert "unit_cost" in item
            assert "trend" in item
            assert "recommended_quantity" in item
            assert "quantity_included" in item
            assert "subtotal" in item
            assert "fully_funded" in item
            assert isinstance(item["recommended_quantity"], int)
            assert isinstance(item["quantity_included"], int)
            assert item["quantity_included"] <= item["recommended_quantity"]


class TestRestockOrdersEndpoints:
    """Test suite for POST/GET /api/restocking/orders."""

    def test_submit_order_too_low_budget_rejected(self, client):
        """A budget too small to afford even the cheapest item's first unit is rejected."""
        response = client.post("/api/restocking/orders", json={"budget": 5})
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_negative_budget_rejected(self, client):
        response = client.post("/api/restocking/orders", json={"budget": -50})
        assert response.status_code == 400

    def test_submit_order_creates_order(self, client):
        """Submitting a sufficient budget creates a restock order with the
        expected shape, lead time, and expected delivery date."""
        response = client.post("/api/restocking/orders", json={"budget": 1300})
        assert response.status_code == 201

        order = response.json()
        assert order["id"]
        assert order["order_number"].startswith("RSO-")
        assert order["budget"] == 1300
        assert order["status"] == "Submitted"
        assert order["total_cost"] > 0
        assert len(order["items"]) > 0
        for item in order["items"]:
            assert item["quantity"] > 0

        assert 5 <= order["lead_time_days"] <= 14
        assert "T" in order["order_date"]
        assert "T" in order["expected_delivery"]
        assert order["expected_delivery"] > order["order_date"]

    def test_submitted_order_appears_in_order_list(self, client):
        """A submitted order shows up in GET /api/restocking/orders."""
        submit_response = client.post("/api/restocking/orders", json={"budget": 1300})
        assert submit_response.status_code == 201
        created_order = submit_response.json()

        list_response = client.get("/api/restocking/orders")
        assert list_response.status_code == 200

        orders = list_response.json()
        assert isinstance(orders, list)
        order_ids = [o["id"] for o in orders]
        assert created_order["id"] in order_ids

    def test_order_numbers_are_unique(self, client):
        """Each submitted order gets a distinct order_number."""
        first = client.post("/api/restocking/orders", json={"budget": 1300}).json()
        second = client.post("/api/restocking/orders", json={"budget": 1300}).json()
        assert first["order_number"] != second["order_number"]
