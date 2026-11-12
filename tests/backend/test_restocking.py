"""
Tests for restocking order API endpoints (POST/GET /api/restocking-orders).
"""
from datetime import datetime, timedelta

import pytest

import mock_data


@pytest.fixture(autouse=True)
def clean_restocking_orders():
    """Restocking orders live in a module-level list, so reset it around every test.

    Must clear in place (not reassign): main.py holds a reference to the same list object.
    """
    mock_data.restocking_orders.clear()
    yield
    mock_data.restocking_orders.clear()


def _forecasts_by_sku(client):
    return {f["item_sku"]: f for f in client.get("/api/demand").json()}


class TestDemandPricingFields:
    """The restocking feature depends on cost/lead-time fields on demand forecasts."""

    def test_demand_forecasts_have_cost_and_lead_time(self, client):
        data = client.get("/api/demand").json()
        assert len(data) > 0

        for forecast in data:
            assert isinstance(forecast["unit_cost"], (int, float))
            assert forecast["unit_cost"] > 0
            assert isinstance(forecast["lead_time_days"], int)
            assert forecast["lead_time_days"] > 0

    def test_demand_unit_cost_matches_inventory_when_sku_overlaps(self, client):
        """Where a forecast SKU also exists in inventory, the two prices must agree."""
        inventory = {i["sku"]: i for i in client.get("/api/inventory").json()}
        overlap = [f for f in client.get("/api/demand").json() if f["item_sku"] in inventory]
        assert overlap, "expected at least one SKU shared by forecasts and inventory"

        for forecast in overlap:
            assert abs(forecast["unit_cost"] - inventory[forecast["item_sku"]]["unit_cost"]) < 0.01


class TestCreateRestockingOrder:
    """Test suite for submitting restocking orders."""

    def test_create_order_returns_201_with_structure(self, client):
        response = client.post(
            "/api/restocking-orders",
            json={"items": [{"sku": "WDG-001", "quantity": 100}]},
        )
        assert response.status_code == 201

        order = response.json()
        for field in ["id", "order_number", "status", "submitted_date",
                      "estimated_delivery", "lead_time_days", "total_value", "items"]:
            assert field in order
        assert order["status"] == "Submitted"
        assert order["order_number"].startswith("RST-")

    def test_order_total_is_computed_from_server_prices(self, client):
        forecasts = _forecasts_by_sku(client)
        response = client.post(
            "/api/restocking-orders",
            json={"items": [
                {"sku": "WDG-001", "quantity": 100},
                {"sku": "FLT-405", "quantity": 250},
            ]},
        )
        order = response.json()

        expected = 100 * forecasts["WDG-001"]["unit_cost"] + 250 * forecasts["FLT-405"]["unit_cost"]
        assert abs(order["total_value"] - expected) < 0.01

        for line in order["items"]:
            assert line["unit_cost"] == forecasts[line["sku"]]["unit_cost"]
            assert line["name"] == forecasts[line["sku"]]["item_name"]
            assert abs(line["line_total"] - line["quantity"] * line["unit_cost"]) < 0.01

    def test_order_lead_time_is_max_of_items(self, client):
        forecasts = _forecasts_by_sku(client)
        skus = ["FLT-405", "MTR-304", "GSK-203"]  # fast, slowest, fast
        response = client.post(
            "/api/restocking-orders",
            json={"items": [{"sku": s, "quantity": 10} for s in skus]},
        )
        order = response.json()

        expected = max(forecasts[s]["lead_time_days"] for s in skus)
        assert order["lead_time_days"] == expected
        # Guard against the test passing trivially if all lead times were equal
        assert len({forecasts[s]["lead_time_days"] for s in skus}) > 1

    def test_estimated_delivery_is_submitted_plus_lead_time(self, client):
        order = client.post(
            "/api/restocking-orders",
            json={"items": [{"sku": "WDG-001", "quantity": 5}]},
        ).json()

        submitted = datetime.fromisoformat(order["submitted_date"])
        delivery = datetime.fromisoformat(order["estimated_delivery"])
        assert delivery - submitted == timedelta(days=order["lead_time_days"])

    def test_client_supplied_prices_are_ignored(self, client):
        """A tampered request must not be able to change what the order costs."""
        forecasts = _forecasts_by_sku(client)
        response = client.post(
            "/api/restocking-orders",
            json={"items": [{
                "sku": "WDG-001", "quantity": 10,
                "unit_cost": 0.01, "line_total": 0.1, "lead_time_days": 1,
            }]},
        )
        assert response.status_code == 201

        order = response.json()
        assert order["items"][0]["unit_cost"] == forecasts["WDG-001"]["unit_cost"]
        assert abs(order["total_value"] - 10 * forecasts["WDG-001"]["unit_cost"]) < 0.01
        assert order["lead_time_days"] == forecasts["WDG-001"]["lead_time_days"]

    def test_duplicate_skus_are_merged(self, client):
        response = client.post(
            "/api/restocking-orders",
            json={"items": [
                {"sku": "WDG-001", "quantity": 40},
                {"sku": "WDG-001", "quantity": 60},
            ]},
        )
        assert response.status_code == 201

        items = response.json()["items"]
        assert len(items) == 1
        assert items[0]["quantity"] == 100

    def test_order_numbers_increment(self, client):
        payload = {"items": [{"sku": "WDG-001", "quantity": 1}]}
        first = client.post("/api/restocking-orders", json=payload).json()
        second = client.post("/api/restocking-orders", json=payload).json()

        assert first["id"] != second["id"]
        assert first["order_number"] != second["order_number"]
        assert first["order_number"].endswith("0001")
        assert second["order_number"].endswith("0002")

    def test_concurrent_submits_get_unique_ids(self, client):
        """Parallel submits must not share an id/order number (lock around sequence + append)."""
        from concurrent.futures import ThreadPoolExecutor

        payload = {"items": [{"sku": "WDG-001", "quantity": 1}]}
        with ThreadPoolExecutor(max_workers=8) as pool:
            responses = list(pool.map(
                lambda _: client.post("/api/restocking-orders", json=payload), range(24)
            ))

        assert all(r.status_code == 201 for r in responses)
        ids = [r.json()["id"] for r in responses]
        numbers = [r.json()["order_number"] for r in responses]
        assert len(set(ids)) == 24
        assert len(set(numbers)) == 24

    def test_quantity_upper_bound_rejected(self, client):
        response = client.post(
            "/api/restocking-orders",
            json={"items": [{"sku": "WDG-001", "quantity": 1_000_001}]},
        )
        assert response.status_code == 422

    def test_unknown_sku_rejected(self, client):
        response = client.post(
            "/api/restocking-orders",
            json={"items": [{"sku": "NOPE-999", "quantity": 5}]},
        )
        assert response.status_code == 400
        assert "NOPE-999" in response.json()["detail"]
        assert client.get("/api/restocking-orders").json() == []

    def test_empty_items_rejected(self, client):
        response = client.post("/api/restocking-orders", json={"items": []})
        assert response.status_code == 422

    def test_missing_items_rejected(self, client):
        response = client.post("/api/restocking-orders", json={})
        assert response.status_code == 422

    @pytest.mark.parametrize("quantity", [0, -5])
    def test_non_positive_quantity_rejected(self, client, quantity):
        response = client.post(
            "/api/restocking-orders",
            json={"items": [{"sku": "WDG-001", "quantity": quantity}]},
        )
        assert response.status_code == 422

    def test_invalid_order_is_not_stored(self, client):
        """One bad line must reject the whole order, not store a partial one."""
        response = client.post(
            "/api/restocking-orders",
            json={"items": [
                {"sku": "WDG-001", "quantity": 10},
                {"sku": "NOPE-999", "quantity": 10},
            ]},
        )
        assert response.status_code == 400
        assert client.get("/api/restocking-orders").json() == []


class TestGetRestockingOrders:
    """Test suite for listing submitted restocking orders."""

    def test_get_orders_empty_initially(self, client):
        response = client.get("/api/restocking-orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_created_order_appears_in_list(self, client):
        created = client.post(
            "/api/restocking-orders",
            json={"items": [{"sku": "GSK-203", "quantity": 20}]},
        ).json()

        listed = client.get("/api/restocking-orders").json()
        assert len(listed) == 1
        assert listed[0] == created

    def test_orders_returned_newest_first(self, client):
        for sku in ["WDG-001", "BRG-102", "GSK-203"]:
            client.post("/api/restocking-orders", json={"items": [{"sku": sku, "quantity": 1}]})

        listed = client.get("/api/restocking-orders").json()
        assert [o["items"][0]["sku"] for o in listed] == ["GSK-203", "BRG-102", "WDG-001"]

    def test_listing_does_not_reorder_stored_orders(self, client):
        """GET must reverse a copy; mutating the shared list would flip order on every call."""
        for sku in ["WDG-001", "BRG-102"]:
            client.post("/api/restocking-orders", json={"items": [{"sku": sku, "quantity": 1}]})

        first = client.get("/api/restocking-orders").json()
        second = client.get("/api/restocking-orders").json()
        assert first == second
