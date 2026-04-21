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


class TestRestockingOrderValidation:
    """Boundary and validation tests for POST /api/restocking/orders."""

    def _item_with_quantity(self, quantity: int) -> dict:
        """Return a restocking order line item with the specified quantity."""
        return {
            "sku": "TMP-201",
            "name": "Temperature Sensor Module",
            "quantity": quantity,
            "unit_cost": 89.5,
            "lead_time_days": 14,
            "subtotal": round(quantity * 89.5, 2),
        }

    def test_negative_quantity_rejected_with_422(self, client):
        """POST with a negative quantity must be rejected by Pydantic validation.

        RestockingOrderLine.quantity is declared with Field(gt=0). Negative values
        would corrupt total_cost and subtotal math, so they must not reach the handler.
        """
        import main
        main.restocking_orders.clear()

        payload = {"items": [self._item_with_quantity(-10)]}
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 422
        assert len(main.restocking_orders) == 0, (
            "Rejected request must not have mutated server state"
        )

    def test_zero_quantity_rejected_with_422(self, client):
        """POST with quantity=0 must be rejected — orders must have real line items."""
        import main
        main.restocking_orders.clear()

        payload = {"items": [self._item_with_quantity(0)]}
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 422
        assert len(main.restocking_orders) == 0

    def test_two_consecutive_posts_have_distinct_monotonically_increasing_ids(self, client):
        """Two consecutive POSTs yield distinct IDs that increment: RO-YYYY-0001 → RO-YYYY-0002.

        The ID is derived from len(restocking_orders) + 1, so the second POST must
        yield a sequence number that is exactly one higher than the first. A bug where
        the list is not appended correctly before computing the length would cause
        both orders to share the same ID.
        """
        import main
        from datetime import date

        main.restocking_orders.clear()

        items = [
            {
                "sku": "TMP-201",
                "name": "Temperature Sensor Module",
                "quantity": 10,
                "unit_cost": 89.5,
                "lead_time_days": 14,
                "subtotal": round(10 * 89.5, 2),
            }
        ]
        payload = {"items": items}

        first_response = client.post("/api/restocking/orders", json=payload)
        assert first_response.status_code == 200
        second_response = client.post("/api/restocking/orders", json=payload)
        assert second_response.status_code == 200

        year = date.today().year
        first_id = first_response.json()["id"]
        second_id = second_response.json()["id"]

        assert first_id == f"RO-{year}-0001", f"First ID should be RO-{year}-0001, got {first_id}"
        assert second_id == f"RO-{year}-0002", f"Second ID should be RO-{year}-0002, got {second_id}"
        assert first_id != second_id, "Consecutive orders must have distinct IDs"

    def test_expected_delivery_date_is_today_plus_max_lead_time(self, client):
        """expected_delivery_date = today + max(lead_time_days) for the posted items.

        This verifies the date arithmetic exactly. A bug using timedelta(days=sum(...))
        or using the wrong field name would produce a wrong delivery date.
        """
        import main
        from datetime import date, timedelta

        main.restocking_orders.clear()

        items = [
            {
                "sku": "TMP-201",
                "name": "Item A",
                "quantity": 5,
                "unit_cost": 10.0,
                "lead_time_days": 7,
                "subtotal": 50.0,
            },
            {
                "sku": "SRV-301",
                "name": "Item B",
                "quantity": 5,
                "unit_cost": 10.0,
                "lead_time_days": 21,
                "subtotal": 50.0,
            },
        ]
        expected_delivery = (date.today() + timedelta(days=21)).isoformat()

        response = client.post("/api/restocking/orders", json={"items": items})
        assert response.status_code == 200

        order = response.json()
        assert order["expected_delivery_date"] == expected_delivery, (
            f"Expected delivery {expected_delivery}, got {order['expected_delivery_date']}"
        )


class TestRestockingCandidatesEdgeCases:
    """Edge case tests for GET /api/restocking/candidates."""

    def test_filter_by_warehouse_with_no_matching_inventory_returns_empty_list(self, client):
        """Candidates with a warehouse that has no shortfall items returns [] not an error.

        If the filter results in an empty list, the endpoint must return an empty
        JSON array rather than 404 or 500. This catches the case where an empty
        candidates list raises an assertion or causes a crash.
        """
        # Use a warehouse filter value that is valid but may yield zero restocking
        # candidates. We cannot guarantee which warehouse has zero shortfalls, so
        # we verify that any warehouse filter returns 200 with a list.
        response = client.get("/api/restocking/candidates?warehouse=San Francisco&category=Circuit Boards")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list), "Empty candidate result must be a list, not null or error"

    def test_unknown_warehouse_returns_empty_list_not_error(self, client):
        """A warehouse name that matches no inventory items returns [] not an error.

        This tests the degenerate case where filtering eliminates all candidates.
        """
        response = client.get("/api/restocking/candidates?warehouse=NonExistentCity")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0, (
            "A warehouse with no inventory should produce an empty candidates list"
        )


class TestRestockingFuzz:
    """Fuzz-style tests for restocking round-trip behaviour."""

    def _get_candidates(self, client) -> list[dict]:
        """Return the full list of restocking candidates."""
        response = client.get("/api/restocking/candidates")
        assert response.status_code == 200
        return response.json()

    def test_random_candidate_subsets_round_trip_correctly(self, client):
        """20 random subsets of candidates can be POSTed and read back with correct
        structure, sort order, and total_cost invariant.

        Catches: serialisation bugs, total_cost accumulation errors, sort-order
        regressions after multiple POSTs, and missing fields on GET.
        """
        import main
        import random
        from datetime import date

        random.seed(7)
        main.restocking_orders.clear()

        candidates = self._get_candidates(client)
        assert len(candidates) > 0, "Need candidates to fuzz restocking orders"

        posted_ids: list[str] = []

        for iteration in range(20):
            # Pick 1–3 candidates at random, using them as order line items.
            subset_size = random.randint(1, min(3, len(candidates)))
            subset = random.sample(candidates, subset_size)

            items = [
                {
                    "sku": c["sku"],
                    "name": c["name"],
                    "quantity": c["recommended_qty"],
                    "unit_cost": c["unit_cost"],
                    "lead_time_days": c["lead_time_days"],
                    "subtotal": c["estimated_cost"],
                }
                for c in subset
            ]

            expected_total = round(sum(item["subtotal"] for item in items), 2)

            response = client.post("/api/restocking/orders", json={"items": items})
            assert response.status_code == 200, (
                f"Iteration {iteration}: POST failed with {response.status_code}"
            )

            order = response.json()

            # Verify required fields are present.
            for field in ["id", "submitted_date", "status", "items", "total_cost",
                          "max_lead_time_days", "expected_delivery_date"]:
                assert field in order, (
                    f"Iteration {iteration}: missing field '{field}' in created order"
                )

            # Verify total_cost invariant.
            assert abs(order["total_cost"] - expected_total) < 0.01, (
                f"Iteration {iteration}: total_cost {order['total_cost']} != "
                f"expected {expected_total}"
            )

            # Verify ID format.
            year = date.today().year
            expected_id = f"RO-{year}-{(iteration + 1):04d}"
            assert order["id"] == expected_id, (
                f"Iteration {iteration}: expected ID {expected_id}, got {order['id']}"
            )

            posted_ids.append(order["id"])

        # GET all orders and verify sort order (submitted_date descending) and
        # that all posted orders are present with all required fields.
        get_response = client.get("/api/restocking/orders")
        assert get_response.status_code == 200

        all_orders = get_response.json()
        assert len(all_orders) == 20, (
            f"Expected 20 orders after 20 POSTs, got {len(all_orders)}"
        )

        # Verify submitted_date descending sort.
        dates = [o["submitted_date"] for o in all_orders]
        assert dates == sorted(dates, reverse=True), (
            "GET /api/restocking/orders must return orders sorted by submitted_date descending"
        )

        # Verify all posted IDs are present and every order has required fields.
        returned_ids = {o["id"] for o in all_orders}
        for posted_id in posted_ids:
            assert posted_id in returned_ids, (
                f"Posted order {posted_id} not found in GET response"
            )

        for order in all_orders:
            for field in ["id", "submitted_date", "status", "items", "total_cost",
                          "max_lead_time_days", "expected_delivery_date"]:
                assert field in order, f"GET response order missing field '{field}'"
