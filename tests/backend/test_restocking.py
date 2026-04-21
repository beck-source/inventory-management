"""
Tests for restocking API endpoints.

Covers:
  - GET /api/restocking/candidates — candidate list, filtering, ordering
  - POST /api/restocking/orders — order creation, validation
  - GET /api/restocking/orders — order list after creation
"""
import pytest

import sys
from pathlib import Path

# Ensure module-level restocking_orders list is reset between test sessions
# by importing the module reference directly.
server_path = Path(__file__).parent.parent.parent / "server"
sys.path.insert(0, str(server_path))


class TestRestockingCandidates:
    """Test suite for GET /api/restocking/candidates."""

    def test_get_candidates_returns_non_empty_list(self, client):
        """Test that the candidates endpoint returns a non-empty list."""
        response = client.get("/api/restocking/candidates")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_get_candidates_has_expected_keys(self, client):
        """Test that each candidate has all required fields."""
        response = client.get("/api/restocking/candidates")
        assert response.status_code == 200

        data = response.json()
        required_fields = [
            "sku",
            "name",
            "category",
            "warehouse",
            "quantity_on_hand",
            "forecasted_demand",
            "shortfall",
            "recommended_qty",
            "unit_cost",
            "estimated_cost",
            "lead_time_days",
            "trend",
        ]
        for candidate in data:
            for field in required_fields:
                assert field in candidate, f"Missing field '{field}' in candidate {candidate.get('sku')}"

    def test_get_candidates_shortfall_always_positive(self, client):
        """Test that shortfall is always a positive integer for every candidate."""
        response = client.get("/api/restocking/candidates")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0

        for candidate in data:
            assert candidate["shortfall"] > 0, (
                f"Expected positive shortfall for {candidate['sku']}, got {candidate['shortfall']}"
            )

    def test_get_candidates_sorted_by_shortfall_descending(self, client):
        """Test that candidates are sorted with highest shortfall first."""
        response = client.get("/api/restocking/candidates")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 1, "Need at least two candidates to verify sort order"

        shortfalls = [c["shortfall"] for c in data]
        assert shortfalls == sorted(shortfalls, reverse=True), (
            f"Candidates not sorted by shortfall descending: {shortfalls}"
        )

    def test_get_candidates_shortfall_matches_computation(self, client):
        """Test that shortfall equals forecasted_demand minus quantity_on_hand."""
        response = client.get("/api/restocking/candidates")
        assert response.status_code == 200

        for candidate in response.json():
            expected_shortfall = candidate["forecasted_demand"] - candidate["quantity_on_hand"]
            assert candidate["shortfall"] == expected_shortfall, (
                f"Shortfall mismatch for {candidate['sku']}: "
                f"expected {expected_shortfall}, got {candidate['shortfall']}"
            )

    def test_get_candidates_recommended_qty_equals_shortfall(self, client):
        """Test that recommended_qty equals the shortfall for each candidate."""
        response = client.get("/api/restocking/candidates")
        assert response.status_code == 200

        for candidate in response.json():
            assert candidate["recommended_qty"] == candidate["shortfall"], (
                f"recommended_qty {candidate['recommended_qty']} != "
                f"shortfall {candidate['shortfall']} for {candidate['sku']}"
            )

    def test_get_candidates_estimated_cost_matches_computation(self, client):
        """Test that estimated_cost equals recommended_qty * unit_cost rounded to 2dp."""
        response = client.get("/api/restocking/candidates")
        assert response.status_code == 200

        for candidate in response.json():
            expected_cost = round(candidate["recommended_qty"] * candidate["unit_cost"], 2)
            assert abs(candidate["estimated_cost"] - expected_cost) < 0.01, (
                f"estimated_cost mismatch for {candidate['sku']}: "
                f"expected {expected_cost}, got {candidate['estimated_cost']}"
            )

    def test_get_candidates_filter_by_warehouse(self, client):
        """Test that warehouse filter restricts candidates to that warehouse."""
        # Use Tokyo — it contains Actuators items with shortfall in test data.
        response = client.get("/api/restocking/candidates?warehouse=Tokyo")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        for candidate in data:
            assert candidate["warehouse"] == "Tokyo", (
                f"Expected Tokyo warehouse, got {candidate['warehouse']}"
            )

    def test_get_candidates_filter_by_category(self, client):
        """Test that category filter restricts candidates to that category."""
        response = client.get("/api/restocking/candidates?category=Actuators")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        for candidate in data:
            assert candidate["category"].lower() == "actuators", (
                f"Expected Actuators category, got {candidate['category']}"
            )

    def test_get_candidates_filter_by_warehouse_and_category(self, client):
        """Test that combined warehouse and category filters both apply."""
        response = client.get("/api/restocking/candidates?warehouse=Tokyo&category=Actuators")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        for candidate in data:
            assert candidate["warehouse"] == "Tokyo"
            assert candidate["category"].lower() == "actuators"

    def test_get_candidates_lead_time_days_is_positive_int(self, client):
        """Test that lead_time_days is a positive integer for each candidate."""
        response = client.get("/api/restocking/candidates")
        assert response.status_code == 200

        for candidate in response.json():
            assert isinstance(candidate["lead_time_days"], int)
            assert candidate["lead_time_days"] > 0

    def test_get_candidates_trend_is_valid_string(self, client):
        """Test that trend field is a non-empty string."""
        response = client.get("/api/restocking/candidates")
        assert response.status_code == 200

        valid_trends = {"increasing", "decreasing", "stable"}
        for candidate in response.json():
            assert isinstance(candidate["trend"], str)
            assert candidate["trend"] in valid_trends, (
                f"Unexpected trend value '{candidate['trend']}' for {candidate['sku']}"
            )


class TestRestockingOrders:
    """Test suite for POST /api/restocking/orders and GET /api/restocking/orders."""

    def _sample_order_items(self) -> list[dict]:
        """Return a minimal valid list of restocking order line items."""
        return [
            {
                "sku": "TMP-201",
                "name": "Temperature Sensor Module",
                "quantity": 75,
                "unit_cost": 89.5,
                "lead_time_days": 14,
                "subtotal": round(75 * 89.5, 2),
            },
            {
                "sku": "SRV-301",
                "name": "Micro Servo Motor",
                "quantity": 45,
                "unit_cost": 445.0,
                "lead_time_days": 15,
                "subtotal": round(45 * 445.0, 2),
            },
        ]

    def test_post_order_with_valid_items_returns_200(self, client):
        """Test that posting a valid restocking order returns HTTP 200."""
        import main
        main.restocking_orders.clear()

        payload = {"items": self._sample_order_items()}
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 200

    def test_post_order_response_has_expected_fields(self, client):
        """Test that the created order response contains all required fields."""
        import main
        main.restocking_orders.clear()

        payload = {"items": self._sample_order_items()}
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 200

        order = response.json()
        required_fields = [
            "id",
            "submitted_date",
            "status",
            "items",
            "total_cost",
            "max_lead_time_days",
            "expected_delivery_date",
        ]
        for field in required_fields:
            assert field in order, f"Missing field '{field}' in order response"

    def test_post_order_id_format(self, client):
        """Test that the generated order ID follows RO-YYYY-NNNN format."""
        import main
        from datetime import date

        main.restocking_orders.clear()

        payload = {"items": self._sample_order_items()}
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 200

        order = response.json()
        current_year = date.today().year
        # ID should be RO-YYYY-NNNN where NNNN is zero-padded to 4 digits.
        assert order["id"] == f"RO-{current_year}-0001", (
            f"Unexpected order ID format: {order['id']}"
        )

    def test_post_order_status_is_submitted(self, client):
        """Test that newly created orders have status 'Submitted'."""
        import main
        main.restocking_orders.clear()

        payload = {"items": self._sample_order_items()}
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 200

        order = response.json()
        assert order["status"] == "Submitted"

    def test_post_order_total_cost_computed_correctly(self, client):
        """Test that total_cost equals the sum of all line item subtotals."""
        import main
        main.restocking_orders.clear()

        items = self._sample_order_items()
        expected_total = round(sum(item["subtotal"] for item in items), 2)

        payload = {"items": items}
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 200

        order = response.json()
        assert abs(order["total_cost"] - expected_total) < 0.01, (
            f"Expected total_cost {expected_total}, got {order['total_cost']}"
        )

    def test_post_order_max_lead_time_is_maximum_of_items(self, client):
        """Test that max_lead_time_days is the maximum lead_time_days across items."""
        import main
        main.restocking_orders.clear()

        items = self._sample_order_items()
        expected_max = max(item["lead_time_days"] for item in items)

        payload = {"items": items}
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 200

        order = response.json()
        assert order["max_lead_time_days"] == expected_max, (
            f"Expected max_lead_time_days {expected_max}, got {order['max_lead_time_days']}"
        )

    def test_post_order_expected_delivery_date_format(self, client):
        """Test that expected_delivery_date is a valid YYYY-MM-DD date string."""
        import main
        from datetime import date, timedelta

        main.restocking_orders.clear()

        items = self._sample_order_items()
        max_lead = max(item["lead_time_days"] for item in items)
        expected_delivery = (date.today() + timedelta(days=max_lead)).isoformat()

        payload = {"items": items}
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 200

        order = response.json()
        # Verify format is YYYY-MM-DD (no time component).
        delivery = order["expected_delivery_date"]
        assert len(delivery) == 10, f"Expected YYYY-MM-DD format, got '{delivery}'"
        assert delivery.count("-") == 2, f"Expected YYYY-MM-DD format, got '{delivery}'"
        assert delivery == expected_delivery, (
            f"Expected delivery date {expected_delivery}, got {delivery}"
        )

    def test_post_order_with_empty_items_returns_400(self, client):
        """Test that posting an order with no items returns HTTP 400."""
        import main
        main.restocking_orders.clear()

        payload = {"items": []}
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data

    def test_get_orders_includes_newly_posted_order(self, client):
        """Test that GET /api/restocking/orders returns orders created via POST."""
        import main
        main.restocking_orders.clear()

        # Create an order first.
        payload = {"items": self._sample_order_items()}
        post_response = client.post("/api/restocking/orders", json=payload)
        assert post_response.status_code == 200

        created_order = post_response.json()
        created_id = created_order["id"]

        # Now fetch all orders and verify ours is present.
        get_response = client.get("/api/restocking/orders")
        assert get_response.status_code == 200

        orders = get_response.json()
        assert isinstance(orders, list)
        assert len(orders) > 0

        order_ids = [o["id"] for o in orders]
        assert created_id in order_ids, (
            f"Created order {created_id} not found in GET /api/restocking/orders"
        )

    def test_get_orders_returns_empty_list_when_no_orders(self, client):
        """Test that GET /api/restocking/orders returns an empty list initially."""
        import main
        main.restocking_orders.clear()

        response = client.get("/api/restocking/orders")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_orders_sorted_by_submitted_date_descending(self, client):
        """Test that GET /api/restocking/orders is sorted newest-first."""
        import main
        main.restocking_orders.clear()

        # Create two orders in sequence.
        payload = {"items": self._sample_order_items()}
        client.post("/api/restocking/orders", json=payload)
        client.post("/api/restocking/orders", json=payload)

        response = client.get("/api/restocking/orders")
        assert response.status_code == 200

        orders = response.json()
        assert len(orders) == 2

        # Most recent order (second posted) should have a later or equal submitted_date.
        assert orders[0]["submitted_date"] >= orders[1]["submitted_date"], (
            "Orders are not sorted by submitted_date descending"
        )
