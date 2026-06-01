"""
Tests for the restock-orders API endpoint (POST /api/restock-orders).
"""
from datetime import datetime

import pytest


class TestRestockOrdersEndpoint:
    """Test suite for submitting restocking orders."""

    def _sample_payload(self):
        """A valid restock order request payload."""
        return {
            "budget": 50000,
            "items": [
                {
                    "item_sku": "WDG-001",
                    "item_name": "Industrial Widget Type A",
                    "quantity": 150,
                    "unit_price": 42.5,
                },
                {
                    "item_sku": "GSK-203",
                    "item_name": "High-Temperature Gasket",
                    "quantity": 100,
                    "unit_price": 12.0,
                },
            ],
        }

    def test_place_restock_order_success(self, client):
        """Test submitting a valid restock order returns a Submitted order."""
        response = client.post("/api/restock-orders", json=self._sample_payload())
        assert response.status_code == 200

        order = response.json()
        # Core order shape (matches the Order model)
        for field in (
            "id",
            "order_number",
            "customer",
            "items",
            "status",
            "order_date",
            "expected_delivery",
            "total_value",
        ):
            assert field in order

        assert order["status"] == "Submitted"
        assert order["customer"] == "Internal Restock"
        assert order["order_number"].startswith("ORD-2025-")

    def test_restock_order_items_mapped_to_order_shape(self, client):
        """Items must be stored in the order-item dict shape (sku/name/...)."""
        response = client.post("/api/restock-orders", json=self._sample_payload())
        order = response.json()

        assert len(order["items"]) == 2
        for item in order["items"]:
            # Stored as sku/name, NOT item_sku/item_name
            assert "sku" in item
            assert "name" in item
            assert "quantity" in item
            assert "unit_price" in item
            assert "item_sku" not in item
            assert "item_name" not in item

    def test_restock_order_total_value_calculation(self, client):
        """total_value should be computed server-side from items."""
        payload = self._sample_payload()
        response = client.post("/api/restock-orders", json=payload)
        order = response.json()

        expected = sum(i["quantity"] * i["unit_price"] for i in payload["items"])
        assert abs(order["total_value"] - expected) < 0.01

    def test_restock_order_lead_time_is_14_days(self, client):
        """expected_delivery should be exactly 14 days after order_date."""
        response = client.post("/api/restock-orders", json=self._sample_payload())
        order = response.json()

        order_date = datetime.fromisoformat(order["order_date"])
        expected_delivery = datetime.fromisoformat(order["expected_delivery"])
        assert (expected_delivery - order_date).days == 14

    def test_restock_order_appears_in_submitted_filter(self, client):
        """A placed order is retrievable via GET /api/orders?status=submitted."""
        response = client.post("/api/restock-orders", json=self._sample_payload())
        placed = response.json()

        listing = client.get("/api/orders?status=submitted")
        assert listing.status_code == 200
        data = listing.json()
        numbers = [o["order_number"] for o in data]
        assert placed["order_number"] in numbers
        for o in data:
            assert o["status"].lower() == "submitted"

    def test_restock_order_number_is_unique_and_increments(self, client):
        """Two successive orders get distinct, sequential order numbers."""
        first = client.post("/api/restock-orders", json=self._sample_payload()).json()
        second = client.post("/api/restock-orders", json=self._sample_payload()).json()

        assert first["order_number"] != second["order_number"]
        first_num = int(first["order_number"].split("-")[-1])
        second_num = int(second["order_number"].split("-")[-1])
        assert second_num == first_num + 1

    def test_restock_order_empty_items_rejected(self, client):
        """Submitting with no items returns 400."""
        response = client.post(
            "/api/restock-orders", json={"budget": 1000, "items": []}
        )
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_restock_order_missing_fields_validation(self, client):
        """Malformed item (missing required fields) returns 422."""
        response = client.post(
            "/api/restock-orders",
            json={"budget": 1000, "items": [{"item_sku": "WDG-001"}]},
        )
        assert response.status_code == 422
