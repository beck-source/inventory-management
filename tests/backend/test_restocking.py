"""
Tests for restocking order API endpoints.
"""
import pytest


# Lead times are derived from the warehouse, not stored in any fixture.
# Mirrors WAREHOUSE_LEAD_TIME_DAYS in server/main.py.
EXPECTED_LEAD_TIMES = {
    "San Francisco": 5,
    "London": 10,
    "Tokyo": 14
}


def build_order(warehouse="Tokyo", items=None):
    """Build a valid restocking order payload."""
    if items is None:
        items = [
            {
                "sku": "SRV-301",
                "name": "Micro Servo Motor",
                "quantity": 10,
                "unit_price": 445.00
            }
        ]
    return {"warehouse": warehouse, "items": items}


class TestRestockingEndpoints:
    """Test suite for restocking-order endpoints.

    Note: the server stores submitted orders in a module-level list that is
    shared across the whole test session, so these tests assert on the returned
    object and on membership rather than on absolute list length.
    """

    def test_get_all_restocking_orders(self, client):
        """Test getting all restocking orders."""
        response = client.get("/api/restocking-orders")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_create_restocking_order(self, client):
        """Test submitting a restocking order."""
        response = client.post("/api/restocking-orders", json=build_order())
        assert response.status_code == 201

        order = response.json()
        assert "id" in order
        assert "order_number" in order
        assert order["warehouse"] == "Tokyo"
        assert order["status"] == "Submitted"
        assert isinstance(order["items"], list)
        assert len(order["items"]) == 1

    def test_restocking_order_number_format(self, client):
        """Test that restocking orders get an RST-prefixed order number."""
        response = client.post("/api/restocking-orders", json=build_order())
        order = response.json()

        assert order["order_number"].startswith("RST-2025-")
        # Sequence is zero-padded to 4 digits
        assert len(order["order_number"].split("-")[-1]) == 4

    def test_restocking_order_items_structure(self, client):
        """Test that restocking order items have proper structure."""
        response = client.post("/api/restocking-orders", json=build_order())
        order = response.json()

        for item in order["items"]:
            assert "sku" in item
            assert "name" in item
            assert "quantity" in item
            assert "unit_price" in item
            assert isinstance(item["quantity"], int)
            assert isinstance(item["unit_price"], (int, float))

    def test_restocking_order_total_value_calculation(self, client):
        """Test that total value is the sum of quantity * unit_price."""
        items = [
            {"sku": "SRV-301", "name": "Micro Servo Motor", "quantity": 10, "unit_price": 445.00},
            {"sku": "PSU-508", "name": "Battery Backup Power Supply", "quantity": 4, "unit_price": 185.50}
        ]
        response = client.post("/api/restocking-orders", json=build_order(items=items))
        order = response.json()

        calculated_total = sum(i["quantity"] * i["unit_price"] for i in items)
        assert abs(order["total_value"] - calculated_total) < 0.01

    def test_restocking_order_lead_time_by_warehouse(self, client):
        """Test that lead time is derived correctly for each warehouse."""
        for warehouse, expected_days in EXPECTED_LEAD_TIMES.items():
            response = client.post(
                "/api/restocking-orders",
                json=build_order(warehouse=warehouse)
            )
            assert response.status_code == 201

            order = response.json()
            assert order["warehouse"] == warehouse
            assert order["lead_time_days"] == expected_days

    def test_restocking_order_unknown_warehouse_uses_default(self, client):
        """Test that an unrecognized warehouse falls back to the default lead time."""
        response = client.post(
            "/api/restocking-orders",
            json=build_order(warehouse="Berlin")
        )
        assert response.status_code == 201

        order = response.json()
        assert order["lead_time_days"] == 7

    def test_restocking_order_dates_format(self, client):
        """Test that restocking order dates are in ISO format with a time component."""
        response = client.post("/api/restocking-orders", json=build_order())
        order = response.json()

        assert "T" in order["order_date"]
        assert "T" in order["expected_delivery"]
        assert "-" in order["order_date"]

    def test_restocking_order_expected_delivery_offset(self, client):
        """Test that expected delivery is order date plus the lead time."""
        from datetime import datetime

        response = client.post("/api/restocking-orders", json=build_order(warehouse="London"))
        order = response.json()

        ordered = datetime.fromisoformat(order["order_date"])
        delivery = datetime.fromisoformat(order["expected_delivery"])

        assert (delivery - ordered).days == EXPECTED_LEAD_TIMES["London"]
        assert order["lead_time_days"] == EXPECTED_LEAD_TIMES["London"]

    def test_create_restocking_order_empty_items(self, client):
        """Test that submitting an order with no items is rejected."""
        response = client.post(
            "/api/restocking-orders",
            json={"warehouse": "Tokyo", "items": []}
        )
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert "at least one item" in data["detail"].lower()

    def test_create_restocking_order_missing_warehouse(self, client):
        """Test that a missing required field returns a validation error."""
        response = client.post(
            "/api/restocking-orders",
            json={"items": [
                {"sku": "SRV-301", "name": "Micro Servo Motor", "quantity": 10, "unit_price": 445.00}
            ]}
        )
        assert response.status_code == 422

    def test_create_restocking_order_invalid_item(self, client):
        """Test that a malformed item line returns a validation error."""
        response = client.post(
            "/api/restocking-orders",
            json={"warehouse": "Tokyo", "items": [{"sku": "SRV-301"}]}
        )
        assert response.status_code == 422

    def test_submitted_order_appears_in_list(self, client):
        """Test that a submitted order is retrievable from the list endpoint."""
        created = client.post("/api/restocking-orders", json=build_order()).json()

        response = client.get("/api/restocking-orders")
        assert response.status_code == 200

        order_numbers = [o["order_number"] for o in response.json()]
        assert created["order_number"] in order_numbers

    def test_restocking_orders_newest_first(self, client):
        """Test that the list returns the most recently submitted order first."""
        client.post("/api/restocking-orders", json=build_order(warehouse="London"))
        latest = client.post("/api/restocking-orders", json=build_order(warehouse="Tokyo")).json()

        data = client.get("/api/restocking-orders").json()
        assert data[0]["order_number"] == latest["order_number"]

    def test_restocking_orders_excluded_from_customer_orders(self, client):
        """Test that restocking orders do not leak into the customer orders list."""
        client.post("/api/restocking-orders", json=build_order())

        orders = client.get("/api/orders").json()
        order_numbers = [o["order_number"] for o in orders]

        assert not any(num.startswith("RST-") for num in order_numbers)


class TestDemandForecastAlignment:
    """Test suite verifying demand forecasts join to real inventory items."""

    def test_forecast_skus_exist_in_inventory(self, client):
        """Test that every forecast SKU references a real inventory item.

        Restocking recommendations join demand forecasts to inventory to get
        unit cost and stock level, so an unjoinable forecast is unusable.
        """
        forecasts = client.get("/api/demand").json()
        inventory = client.get("/api/inventory").json()

        inventory_skus = {item["sku"] for item in inventory}

        for forecast in forecasts:
            assert forecast["item_sku"] in inventory_skus, (
                f"Forecast SKU {forecast['item_sku']} has no inventory item"
            )

    def test_forecasts_produce_restockable_shortfall(self, client):
        """Test that at least one forecast exceeds current stock.

        If no forecast has a positive shortfall, the restocking view would
        recommend nothing at any budget.
        """
        forecasts = client.get("/api/demand").json()
        inventory = {item["sku"]: item for item in client.get("/api/inventory").json()}

        shortfalls = [
            f["forecasted_demand"] - inventory[f["item_sku"]]["quantity_on_hand"]
            for f in forecasts
            if f["item_sku"] in inventory
        ]

        assert any(gap > 0 for gap in shortfalls)

    def test_forecasts_span_multiple_warehouses(self, client):
        """Test that forecast items cover more than one warehouse.

        Place Order groups the cart by warehouse, so multi-warehouse coverage
        is what exercises that path.
        """
        forecasts = client.get("/api/demand").json()
        inventory = {item["sku"]: item for item in client.get("/api/inventory").json()}

        warehouses = {
            inventory[f["item_sku"]]["warehouse"]
            for f in forecasts
            if f["item_sku"] in inventory
        }

        assert len(warehouses) > 1
