"""
Tests for the /api/submitted-orders endpoints (Restocking tab → Orders tab flow).
"""
from datetime import datetime, timedelta

import pytest

# submitted_orders is a module-level list in mock_data; tests share it across the
# pytest session, so we wipe it before each test to keep cases independent.
# Kept local to this file (not conftest.py) to avoid touching other test suites.
import mock_data


@pytest.fixture(autouse=True)
def clear_submitted_orders():
    mock_data.submitted_orders.clear()
    yield
    mock_data.submitted_orders.clear()


def _payload(items=None, budget=1000.0):
    """Build a minimal valid CreateSubmittedOrderRequest body."""
    return {
        "items": items or [
            {"sku": "PCB-001", "name": "Single Layer PCB", "quantity": 4,
             "unit_cost": 24.99, "lead_time_days": 21}
        ],
        "budget": budget,
    }


class TestSubmittedOrdersEndpoints:
    """Test suite for the submitted-orders endpoints used by the Restocking flow."""

    def test_get_submitted_orders_empty(self, client):
        """Fresh process / cleared list returns an empty array."""
        response = client.get("/api/submitted-orders")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert data == []

    def test_create_submitted_order_minimal(self, client):
        """POST with one item returns a fully-populated SubmittedOrder."""
        response = client.post("/api/submitted-orders", json=_payload())
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == "SUB-0001"
        assert data["budget"] == 1000.0
        assert data["total_value"] == pytest.approx(4 * 24.99)
        assert len(data["items"]) == 1
        assert data["items"][0]["sku"] == "PCB-001"

        # Created date is ISO-formatted; expected_delivery = created + lead_time_days.
        created = datetime.fromisoformat(data["created_date"])
        expected = datetime.fromisoformat(data["expected_delivery_date"])
        assert (expected - created) == timedelta(days=21)

    def test_create_then_list(self, client):
        """A submitted order shows up in the GET response, newest first."""
        client.post("/api/submitted-orders", json=_payload())
        client.post("/api/submitted-orders", json=_payload(budget=2000.0))

        response = client.get("/api/submitted-orders")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2
        # Newest first: SUB-0002 was created last so it should lead the list.
        assert data[0]["id"] == "SUB-0002"
        assert data[1]["id"] == "SUB-0001"

    def test_expected_delivery_uses_max_lead_time(self, client):
        """When a batch mixes lead times, the order's delivery uses the max."""
        items = [
            {"sku": "SEN-001", "name": "Sensor", "quantity": 5,
             "unit_cost": 10.0, "lead_time_days": 7},
            {"sku": "PCB-001", "name": "PCB", "quantity": 2,
             "unit_cost": 25.0, "lead_time_days": 21},
        ]
        response = client.post("/api/submitted-orders", json=_payload(items=items))
        assert response.status_code == 200

        data = response.json()
        created = datetime.fromisoformat(data["created_date"])
        expected = datetime.fromisoformat(data["expected_delivery_date"])
        assert (expected - created) == timedelta(days=21)

    def test_create_validation_rejects_bad_payload(self, client):
        """Missing the items field is a Pydantic 422; empty items is a 422 too."""
        # Missing required `items` field.
        response = client.post("/api/submitted-orders", json={"budget": 100.0})
        assert response.status_code == 422

        # Present but empty items list — handler raises HTTPException(422).
        response = client.post("/api/submitted-orders",
                               json={"items": [], "budget": 100.0})
        assert response.status_code == 422
