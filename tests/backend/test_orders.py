# ABOUTME: Tests for the orders API endpoints including GET filters and POST creation.
# ABOUTME: Covers happy path, filter combinations, 404 handling, and restocking order submission.
import pytest


class TestGetOrdersEndpoints:
    """Test suite for GET /api/orders endpoints."""

    def test_get_all_orders(self, client):
        """Test getting all orders returns a non-empty list."""
        response = client.get("/api/orders")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_order_structure(self, client):
        """Test that orders have all required fields."""
        response = client.get("/api/orders")
        data = response.json()

        first = data[0]
        assert "id" in first
        assert "order_number" in first
        assert "customer" in first
        assert "items" in first
        assert "status" in first
        assert "order_date" in first
        assert "expected_delivery" in first
        assert "total_value" in first

    def test_order_items_structure(self, client):
        """Test that order items have required fields."""
        response = client.get("/api/orders")
        data = response.json()

        for order in data:
            assert isinstance(order["items"], list)
            for item in order["items"]:
                assert "sku" in item
                assert "name" in item
                assert "quantity" in item
                assert "unit_price" in item

    def test_order_total_value_matches_items(self, client):
        """Test that total_value matches the sum of item quantities times unit price."""
        response = client.get("/api/orders")
        data = response.json()

        for order in data:
            calculated = sum(i["quantity"] * i["unit_price"] for i in order["items"])
            assert abs(order["total_value"] - calculated) < 0.01, (
                f"Order {order['order_number']} total_value mismatch: "
                f"stored={order['total_value']}, calculated={calculated}"
            )

    def test_order_status_values(self, client):
        """Test that all orders have recognised status values."""
        response = client.get("/api/orders")
        data = response.json()

        valid_statuses = {"delivered", "shipped", "processing", "backordered"}
        for order in data:
            assert order["status"].lower() in valid_statuses

    def test_filter_by_warehouse(self, client):
        """Test filtering orders by warehouse."""
        response = client.get("/api/orders?warehouse=Tokyo")
        assert response.status_code == 200

        data = response.json()
        for order in data:
            assert order["warehouse"] == "Tokyo"

    def test_filter_by_status(self, client):
        """Test filtering orders by status."""
        response = client.get("/api/orders?status=Processing")
        assert response.status_code == 200

        data = response.json()
        for order in data:
            assert order["status"].lower() == "processing"

    def test_filter_by_month(self, client):
        """Test filtering orders by month."""
        response = client.get("/api/orders?month=2025-01")
        assert response.status_code == 200

        data = response.json()
        for order in data:
            assert "2025-01" in order["order_date"]

    def test_filter_returns_empty_for_unknown_warehouse(self, client):
        """Test that an unknown warehouse returns an empty list."""
        response = client.get("/api/orders?warehouse=Atlantis")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_order_by_id(self, client):
        """Test fetching a single order by ID."""
        all_orders = client.get("/api/orders").json()
        order_id = all_orders[0]["id"]

        response = client.get(f"/api/orders/{order_id}")
        assert response.status_code == 200
        assert response.json()["id"] == order_id

    def test_get_nonexistent_order_returns_404(self, client):
        """Test that fetching a non-existent order returns 404."""
        response = client.get("/api/orders/nonexistent-999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestCreateOrderEndpoint:
    """Test suite for POST /api/orders (restocking order submission)."""

    def _restocking_payload(self):
        return {
            "customer": "Internal Restocking",
            "items": [
                {"sku": "FLT-405", "name": "Oil Filter Cartridge", "quantity": 350, "unit_price": 12.50},
                {"sku": "MTR-304", "name": "Electric Motor 5HP", "quantity": 10, "unit_price": 450.00},
            ],
            "warehouse": "San Francisco",
            "category": "Mechanical Components",
        }

    def test_create_order_returns_201(self, client):
        """Test that creating an order returns HTTP 201."""
        response = client.post("/api/orders", json=self._restocking_payload())
        assert response.status_code == 201

    def test_create_order_response_structure(self, client):
        """Test that the created order has all required fields."""
        response = client.post("/api/orders", json=self._restocking_payload())
        order = response.json()

        assert "id" in order
        assert "order_number" in order
        assert "status" in order
        assert "order_date" in order
        assert "expected_delivery" in order
        assert "total_value" in order
        assert "items" in order

    def test_create_order_has_rst_prefix(self, client):
        """Test that restocking orders are assigned an RST- order number."""
        response = client.post("/api/orders", json=self._restocking_payload())
        order = response.json()
        assert order["order_number"].startswith("RST-")

    def test_create_order_status_is_processing(self, client):
        """Test that new orders start in Processing status."""
        response = client.post("/api/orders", json=self._restocking_payload())
        assert response.json()["status"] == "Processing"

    def test_create_order_total_value_calculated(self, client):
        """Test that total_value is correctly calculated from submitted items."""
        payload = self._restocking_payload()
        response = client.post("/api/orders", json=payload)
        order = response.json()

        expected_total = sum(i["quantity"] * i["unit_price"] for i in payload["items"])
        assert abs(order["total_value"] - expected_total) < 0.01

    def test_create_order_expected_delivery_is_future(self, client):
        """Test that expected_delivery is after order_date."""
        response = client.post("/api/orders", json=self._restocking_payload())
        order = response.json()

        assert order["expected_delivery"] > order["order_date"]

    def test_created_order_appears_in_get_orders(self, client):
        """Test that a submitted order is visible in GET /api/orders."""
        post_response = client.post("/api/orders", json=self._restocking_payload())
        new_order_number = post_response.json()["order_number"]

        get_response = client.get("/api/orders")
        order_numbers = [o["order_number"] for o in get_response.json()]
        assert new_order_number in order_numbers

    def test_create_order_missing_customer_returns_422(self, client):
        """Test that omitting required fields returns a validation error."""
        payload = {"items": [{"sku": "X", "name": "Y", "quantity": 1, "unit_price": 1.0}]}
        response = client.post("/api/orders", json=payload)
        assert response.status_code == 422

    def test_create_order_empty_items_list(self, client):
        """Test that an order with no items still processes (total_value = 0)."""
        payload = {"customer": "Internal Restocking", "items": []}
        response = client.post("/api/orders", json=payload)
        assert response.status_code == 201
        assert response.json()["total_value"] == 0.0
