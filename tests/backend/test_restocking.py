"""
Tests for restocking API endpoints.
"""
import pytest


@pytest.fixture(autouse=True)
def clear_restock_orders():
    """Submitted restock orders are stored in a module-level list, so reset it per test."""
    import main
    main.restock_orders.clear()
    yield
    main.restock_orders.clear()


class TestRestockRecommendations:
    """Test suite for the restocking recommendations endpoint."""

    def test_zero_budget_recommends_nothing(self, client):
        """Test that a zero budget yields no items."""
        response = client.get("/api/restocking/recommendations?budget=0")
        assert response.status_code == 200

        data = response.json()
        assert data["items"] == []
        assert data["total_cost"] == 0
        assert data["lead_time_days"] == 0

    def test_recommendation_structure(self, client):
        """Test that recommendations have the expected fields and types."""
        response = client.get("/api/restocking/recommendations?budget=500000")
        assert response.status_code == 200

        data = response.json()
        for field in ["budget", "total_cost", "remaining_budget", "lead_time_days", "items"]:
            assert field in data
        assert len(data["items"]) > 0

        for item in data["items"]:
            assert isinstance(item["sku"], str)
            assert isinstance(item["quantity"], int)
            assert isinstance(item["unit_cost"], (int, float))
            assert isinstance(item["fully_covered"], bool)
            assert 0 < item["quantity"] <= item["shortfall"]

    @pytest.mark.parametrize("budget", [1000, 5000, 20000, 100000, 500000])
    def test_total_never_exceeds_budget(self, client, budget):
        """Test that the plan always fits within the budget."""
        data = client.get(f"/api/restocking/recommendations?budget={budget}").json()

        assert data["total_cost"] <= budget
        assert abs(data["total_cost"] + data["remaining_budget"] - budget) < 0.01

    def test_total_cost_matches_line_items(self, client):
        """Test that the total equals the sum of quantity x unit cost."""
        data = client.get("/api/restocking/recommendations?budget=20000").json()

        calculated = sum(i["quantity"] * i["unit_cost"] for i in data["items"])
        assert abs(data["total_cost"] - calculated) < 0.01

    def test_increasing_trends_come_first(self, client):
        """Test that rising-demand items are ranked ahead of stable ones."""
        data = client.get("/api/restocking/recommendations?budget=500000").json()

        rank = {"increasing": 0, "stable": 1, "decreasing": 2}
        ranks = [rank[i["trend"]] for i in data["items"]]
        assert ranks == sorted(ranks)

    def test_lead_time_is_longest_item(self, client):
        """Test that the order lead time is the slowest item's lead time."""
        data = client.get("/api/restocking/recommendations?budget=500000").json()

        assert data["lead_time_days"] == max(i["lead_time_days"] for i in data["items"])

    def test_larger_budget_never_recommends_fewer_units(self, client):
        """Test that a bigger budget funds at least as many units overall."""
        small = client.get("/api/restocking/recommendations?budget=5000").json()
        large = client.get("/api/restocking/recommendations?budget=50000").json()

        assert sum(i["quantity"] for i in large["items"]) >= sum(i["quantity"] for i in small["items"])

    def test_negative_budget_rejected(self, client):
        """Test that a negative budget returns 400."""
        response = client.get("/api/restocking/recommendations?budget=-1")
        assert response.status_code == 400
        assert "detail" in response.json()


class TestRestockOrders:
    """Test suite for submitting and listing restocking orders."""

    def _first_recommendation(self, client, budget=20000):
        data = client.get(f"/api/restocking/recommendations?budget={budget}").json()
        return data, [{"sku": i["sku"], "quantity": i["quantity"]} for i in data["items"]]

    def test_no_orders_initially(self, client):
        """Test that the order list starts empty."""
        response = client.get("/api/restocking/orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_order(self, client):
        """Test submitting a recommended plan creates an order."""
        plan, lines = self._first_recommendation(client)

        response = client.post("/api/restocking/orders", json={"budget": 20000, "items": lines})
        assert response.status_code == 201

        order = response.json()
        assert order["id"].startswith("RST-")
        assert order["status"] == "Submitted"
        assert abs(order["total_cost"] - plan["total_cost"]) < 0.01
        assert order["lead_time_days"] == plan["lead_time_days"]
        assert "T" in order["submitted_date"]
        assert "T" in order["expected_delivery"]

    def test_created_order_appears_in_list(self, client):
        """Test that a submitted order is returned by the list endpoint."""
        _, lines = self._first_recommendation(client)
        created = client.post("/api/restocking/orders", json={"budget": 20000, "items": lines}).json()

        listed = client.get("/api/restocking/orders").json()
        assert [o["id"] for o in listed] == [created["id"]]

    def test_orders_listed_newest_first(self, client):
        """Test that the most recent order comes first."""
        _, lines = self._first_recommendation(client)
        first = client.post("/api/restocking/orders", json={"budget": 20000, "items": lines}).json()
        second = client.post("/api/restocking/orders", json={"budget": 20000, "items": lines}).json()

        listed = client.get("/api/restocking/orders").json()
        assert [o["id"] for o in listed] == [second["id"], first["id"]]

    def test_server_ignores_client_prices(self, client):
        """Test that line costs come from server data, not the request."""
        _, lines = self._first_recommendation(client)
        lines[0]["unit_cost"] = 0.01  # extra field a tampering client might send

        order = client.post("/api/restocking/orders", json={"budget": 20000, "items": lines}).json()
        assert order["items"][0]["unit_cost"] > 0.01

    def test_order_over_budget_rejected(self, client):
        """Test that an order exceeding the stated budget returns 400."""
        _, lines = self._first_recommendation(client)

        response = client.post("/api/restocking/orders", json={"budget": 1, "items": lines})
        assert response.status_code == 400
        assert "budget" in response.json()["detail"].lower()

    def test_unknown_sku_rejected(self, client):
        """Test that an unknown SKU returns 400."""
        response = client.post(
            "/api/restocking/orders",
            json={"budget": 1000, "items": [{"sku": "NOPE-000", "quantity": 1}]},
        )
        assert response.status_code == 400
        assert "unknown sku" in response.json()["detail"].lower()

    def test_empty_order_rejected(self, client):
        """Test that an order with no items returns 400."""
        response = client.post("/api/restocking/orders", json={"budget": 1000, "items": []})
        assert response.status_code == 400

    def test_non_positive_quantity_rejected(self, client):
        """Test that zero or negative quantities return 400."""
        sku = client.get("/api/restocking/recommendations?budget=500000").json()["items"][0]["sku"]

        for qty in (0, -5):
            response = client.post(
                "/api/restocking/orders",
                json={"budget": 1000, "items": [{"sku": sku, "quantity": qty}]},
            )
            assert response.status_code == 400

    def test_missing_fields_return_validation_error(self, client):
        """Test that a malformed body returns 422."""
        response = client.post("/api/restocking/orders", json={"items": []})
        assert response.status_code == 422
