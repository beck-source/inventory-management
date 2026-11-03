"""
Tests for restocking API endpoints (recommendations, submitted orders, vendor details).
"""
import json
from datetime import datetime

import pytest

import mock_data


@pytest.fixture(autouse=True)
def isolated_restocking_orders(tmp_path, monkeypatch):
    """Keep restocking tests away from the real data file and from each other.

    The orders list is shared module state that is written back to a tracked JSON file,
    so each test gets an empty list and a temp file. main.py holds the same list object,
    so clearing it in place is enough; the original contents are restored afterwards.
    """
    original = list(mock_data.restocking_orders)
    mock_data.restocking_orders.clear()
    temp_file = tmp_path / "restocking_orders.json"
    monkeypatch.setattr(mock_data, "RESTOCKING_ORDERS_FILE", str(temp_file))
    yield temp_file
    mock_data.restocking_orders.clear()
    mock_data.restocking_orders.extend(original)


def place_order(client, items=None):
    """Helper: submit an order and return the response."""
    items = items if items is not None else [{"sku": "WDG-001", "quantity": 10}]
    return client.post("/api/restocking/orders", json={"items": items})


class TestRestockingRecommendations:
    """Test suite for the recommendation endpoint."""

    def test_recommendations_structure(self, client):
        """Test the response shape and item fields."""
        response = client.get("/api/restocking/recommendations?budget=100000")
        assert response.status_code == 200

        data = response.json()
        for key in ["budget", "items", "total", "remaining_budget", "max_budget"]:
            assert key in data
        assert len(data["items"]) > 0

        item = data["items"][0]
        for key in ["item_sku", "item_name", "trend", "quantity_on_hand", "reorder_point",
                    "is_low_stock", "unit_cost", "demand_gap", "suggested_quantity", "line_total"]:
            assert key in item

    def test_recommendations_respect_budget(self, client):
        """Test that the recommended total never exceeds the budget."""
        for budget in [0, 50, 500, 2500, 10000, 1000000]:
            data = client.get(f"/api/restocking/recommendations?budget={budget}").json()
            assert data["total"] <= budget + 0.001
            assert abs(data["remaining_budget"] - (budget - data["total"])) < 0.01

    def test_recommendations_zero_budget_is_empty(self, client):
        """Test that a zero budget recommends nothing."""
        data = client.get("/api/restocking/recommendations?budget=0").json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_recommendations_line_totals(self, client):
        """Test that line totals match quantity times unit cost and sum to the total."""
        data = client.get("/api/restocking/recommendations?budget=5000").json()
        for item in data["items"]:
            assert abs(item["line_total"] - item["suggested_quantity"] * item["unit_cost"]) < 0.01
            assert 0 < item["suggested_quantity"] <= item["demand_gap"]
        assert abs(sum(i["line_total"] for i in data["items"]) - data["total"]) < 0.01

    def test_recommendations_default_sort_is_demand_gap(self, client):
        """Test that the highest demand gap comes first by default."""
        data = client.get("/api/restocking/recommendations?budget=1000000").json()
        gaps = [i["demand_gap"] for i in data["items"]]
        assert gaps == sorted(gaps, reverse=True)

    def test_recommendations_low_stock_sort(self, client):
        """Test that low-stock items are listed before the others."""
        data = client.get("/api/restocking/recommendations?budget=1000000&sort=low_stock").json()
        flags = [i["is_low_stock"] for i in data["items"]]
        assert any(flags) and not all(flags)
        # Once a non-low-stock item appears, no low-stock item may follow
        assert flags == sorted(flags, reverse=True)

    def test_recommendations_low_stock_flag(self, client):
        """Test that the flag matches stock at or below the reorder point."""
        data = client.get("/api/restocking/recommendations?budget=1000000").json()
        for item in data["items"]:
            assert item["is_low_stock"] == (item["quantity_on_hand"] <= item["reorder_point"])

    def test_recommendations_skip_items_without_gap(self, client):
        """Test that forecasts already covered by stock are not recommended."""
        data = client.get("/api/restocking/recommendations?budget=1000000").json()
        assert all(i["demand_gap"] > 0 for i in data["items"])

    def test_recommendations_max_budget_covers_everything(self, client):
        """Test that the max budget funds every gap in full."""
        max_budget = client.get("/api/restocking/recommendations?budget=0").json()["max_budget"]
        assert max_budget > 0
        data = client.get(f"/api/restocking/recommendations?budget={max_budget}").json()
        for item in data["items"]:
            assert item["suggested_quantity"] == item["demand_gap"]

    def test_recommendations_partial_fill_with_small_budget(self, client):
        """Test that a small budget partly fills an item instead of skipping it."""
        data = client.get("/api/restocking/recommendations?budget=100").json()
        assert len(data["items"]) > 0
        assert any(i["suggested_quantity"] < i["demand_gap"] for i in data["items"])

    def test_recommendations_invalid_params(self, client):
        """Test validation of budget and sort parameters."""
        assert client.get("/api/restocking/recommendations").status_code == 422
        assert client.get("/api/restocking/recommendations?budget=-5").status_code == 422
        assert client.get("/api/restocking/recommendations?budget=abc").status_code == 422
        assert client.get("/api/restocking/recommendations?budget=100&sort=bogus").status_code == 422


class TestRestockingOrders:
    """Test suite for submitting and listing restocking orders."""

    def test_orders_start_empty(self, client):
        """Test listing orders when none were submitted."""
        response = client.get("/api/restocking/orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_order(self, client):
        """Test submitting an order returns the stored order."""
        response = place_order(client, [{"sku": "WDG-001", "quantity": 10}, {"sku": "GSK-203", "quantity": 5}])
        assert response.status_code == 201

        order = response.json()
        assert order["status"] == "Submitted"
        assert order["order_number"].startswith("RST-")
        assert len(order["items"]) == 2
        assert order["vendor"] is None
        assert order["delivery_number"] is None
        assert order["tracking_url"] is None

    def test_create_order_lead_time(self, client):
        """Test the standard 7 day lead time and expected delivery date."""
        order = place_order(client).json()
        assert order["lead_time_days"] == 7

        placed = datetime.fromisoformat(order["order_date"])
        expected = datetime.fromisoformat(order["expected_delivery"])
        assert (expected - placed).days == 7

    def test_create_order_uses_server_side_prices(self, client):
        """Test that client-supplied prices are ignored."""
        inventory = {i["sku"]: i for i in client.get("/api/inventory").json()}
        response = client.post("/api/restocking/orders", json={
            "items": [{"sku": "WDG-001", "quantity": 10, "unit_cost": 0.01, "line_total": 0.1}]
        })
        assert response.status_code == 201

        order = response.json()
        expected_cost = inventory["WDG-001"]["unit_cost"]
        assert order["items"][0]["unit_cost"] == expected_cost
        assert abs(order["total_value"] - 10 * expected_cost) < 0.01

    def test_create_order_total_value(self, client):
        """Test that the total equals the sum of line totals."""
        order = place_order(client, [{"sku": "WDG-001", "quantity": 3}, {"sku": "MTR-304", "quantity": 2}]).json()
        assert abs(order["total_value"] - sum(i["line_total"] for i in order["items"])) < 0.01

    def test_create_order_empty_items(self, client):
        """Test that an order without items is rejected."""
        response = place_order(client, [])
        assert response.status_code == 400
        assert "detail" in response.json()

    @pytest.mark.parametrize("quantity", [0, -3])
    def test_create_order_invalid_quantity(self, client, quantity):
        """Test that zero and negative quantities are rejected."""
        assert place_order(client, [{"sku": "WDG-001", "quantity": quantity}]).status_code == 400

    def test_create_order_unknown_sku(self, client):
        """Test that an unknown SKU returns 404."""
        response = place_order(client, [{"sku": "NOPE-999", "quantity": 1}])
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_order_duplicate_sku(self, client):
        """Test that the same SKU twice in one order is rejected."""
        response = place_order(client, [{"sku": "WDG-001", "quantity": 1}, {"sku": "WDG-001", "quantity": 2}])
        assert response.status_code == 400

    def test_failed_order_is_not_stored(self, client):
        """Test that a rejected order leaves nothing behind."""
        place_order(client, [{"sku": "NOPE-999", "quantity": 1}])
        assert client.get("/api/restocking/orders").json() == []

    def test_order_ids_increment(self, client):
        """Test that ids and order numbers are unique and increasing."""
        first = place_order(client).json()
        second = place_order(client).json()
        assert int(second["id"]) == int(first["id"]) + 1
        assert first["order_number"] != second["order_number"]

    def test_orders_listed_newest_first(self, client):
        """Test that the newest order is returned first."""
        first = place_order(client).json()
        second = place_order(client).json()
        ids = [o["id"] for o in client.get("/api/restocking/orders").json()]
        assert ids == [second["id"], first["id"]]

    def test_order_is_persisted_to_file(self, client, isolated_restocking_orders):
        """Test that a submitted order is written to the JSON file."""
        order = place_order(client).json()
        saved = json.loads(isolated_restocking_orders.read_text(encoding="utf-8"))
        assert [o["id"] for o in saved] == [order["id"]]
        # The tracking link is derived on read and must not be stored
        assert "tracking_url" not in saved[0]

    def test_save_failure_rolls_back(self, client, monkeypatch):
        """Test that an order that could not be saved is not kept in memory."""
        def broken_save():
            raise OSError("disk full")
        import main
        monkeypatch.setattr(main, "save_restocking_orders", broken_save)

        response = place_order(client)
        assert response.status_code == 500
        assert client.get("/api/restocking/orders").json() == []


class TestRestockingOrderDetails:
    """Test suite for vendor and delivery number updates."""

    def test_vendors_endpoint(self, client):
        """Test listing vendors and the standard lead time."""
        data = client.get("/api/restocking/vendors").json()
        assert len(data["vendors"]) > 0
        assert data["lead_time_days"] == 7

    def test_update_vendor_and_delivery_number_builds_tracking_url(self, client):
        """Test that vendor plus delivery number produce a tracking link."""
        order = place_order(client).json()
        vendor = client.get("/api/restocking/vendors").json()["vendors"][0]

        response = client.patch(f"/api/restocking/orders/{order['id']}",
                                json={"vendor": vendor, "delivery_number": "DN-12345"})
        assert response.status_code == 200

        updated = response.json()
        assert updated["vendor"] == vendor
        assert updated["delivery_number"] == "DN-12345"
        assert updated["tracking_url"].startswith("https://")
        assert updated["tracking_url"].endswith("DN-12345")

    def test_tracking_url_needs_both_fields(self, client):
        """Test that no link is built with only one of vendor or delivery number."""
        order = place_order(client).json()
        vendor = client.get("/api/restocking/vendors").json()["vendors"][0]

        only_vendor = client.patch(f"/api/restocking/orders/{order['id']}", json={"vendor": vendor}).json()
        assert only_vendor["tracking_url"] is None

        only_number = client.patch(f"/api/restocking/orders/{order['id']}",
                                   json={"vendor": "", "delivery_number": "DN-1"}).json()
        assert only_number["vendor"] is None
        assert only_number["tracking_url"] is None

    def test_partial_update_keeps_other_field(self, client):
        """Test that sending one field does not wipe the other."""
        order = place_order(client).json()
        vendor = client.get("/api/restocking/vendors").json()["vendors"][0]
        client.patch(f"/api/restocking/orders/{order['id']}", json={"vendor": vendor})

        updated = client.patch(f"/api/restocking/orders/{order['id']}", json={"delivery_number": "DN-9"}).json()
        assert updated["vendor"] == vendor
        assert updated["delivery_number"] == "DN-9"

    def test_empty_value_clears_field(self, client):
        """Test that an empty delivery number clears it."""
        order = place_order(client).json()
        client.patch(f"/api/restocking/orders/{order['id']}", json={"delivery_number": "DN-9"})
        cleared = client.patch(f"/api/restocking/orders/{order['id']}", json={"delivery_number": "  "}).json()
        assert cleared["delivery_number"] is None

    def test_delivery_number_is_url_encoded(self, client):
        """Test that special characters cannot change the tracking URL structure."""
        order = place_order(client).json()
        vendor = client.get("/api/restocking/vendors").json()["vendors"][0]
        updated = client.patch(f"/api/restocking/orders/{order['id']}",
                               json={"vendor": vendor, "delivery_number": "a/b?x=1#frag"}).json()
        url = updated["tracking_url"]
        assert url.endswith("a%2Fb%3Fx%3D1%23frag")
        assert "?" not in url and "#" not in url

    def test_update_unknown_vendor(self, client):
        """Test that a vendor outside the list is rejected."""
        order = place_order(client).json()
        response = client.patch(f"/api/restocking/orders/{order['id']}", json={"vendor": "Evil Corp"})
        assert response.status_code == 400
        assert "vendor" in response.json()["detail"].lower()

    def test_update_delivery_number_too_long(self, client):
        """Test that an over-long delivery number is rejected."""
        order = place_order(client).json()
        response = client.patch(f"/api/restocking/orders/{order['id']}", json={"delivery_number": "x" * 65})
        assert response.status_code == 400

    def test_update_nonexistent_order(self, client):
        """Test updating an order that doesn't exist."""
        response = client.patch("/api/restocking/orders/nonexistent-999", json={"delivery_number": "DN-1"})
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_is_persisted_to_file(self, client, isolated_restocking_orders):
        """Test that an update is written to the JSON file."""
        order = place_order(client).json()
        client.patch(f"/api/restocking/orders/{order['id']}", json={"delivery_number": "DN-77"})
        saved = json.loads(isolated_restocking_orders.read_text(encoding="utf-8"))
        assert saved[0]["delivery_number"] == "DN-77"
