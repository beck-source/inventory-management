"""
Tests for the Restocking feature:
  - GET /api/demand returns the new unit_cost / lead_time_days fields
  - POST /api/orders submits a restock order, appends to the orders list,
    sets expected_delivery based on the max lead time, and surfaces in subsequent GET /api/orders calls
"""


class TestDemandForecastSchema:
    def test_demand_includes_unit_cost_and_lead_time(self, client):
        response = client.get("/api/demand")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        for forecast in data:
            assert "unit_cost" in forecast
            assert "lead_time_days" in forecast
            assert isinstance(forecast["unit_cost"], (int, float))
            assert isinstance(forecast["lead_time_days"], int)
            assert forecast["unit_cost"] > 0
            assert forecast["lead_time_days"] > 0


class TestSubmitRestockOrder:
    def _payload(self, items=None):
        return {
            "items": items or [
                {"sku": "WDG-001", "name": "Industrial Widget Type A",
                 "quantity": 10, "unit_price": 45.0, "lead_time_days": 14},
                {"sku": "MTR-304", "name": "Electric Motor 5HP",
                 "quantity": 2, "unit_price": 620.0, "lead_time_days": 28},
            ],
            "customer": "Internal Restock",
        }

    def test_submit_returns_201_and_well_formed_order(self, client):
        response = client.post("/api/orders", json=self._payload())
        assert response.status_code == 201
        order = response.json()
        # Sequential ID + canonical order number format
        assert order["order_number"].startswith("ORD-2025-")
        assert order["status"] == "Submitted"
        assert order["customer"] == "Internal Restock"
        # 10 * 45 + 2 * 620 = 1690
        assert order["total_value"] == 1690.0
        assert order["actual_delivery"] is None
        # Each item carries its lead_time forward
        assert all("lead_time_days" in item for item in order["items"])

    def test_submitted_order_appears_in_list(self, client):
        before = client.get("/api/orders").json()
        client.post("/api/orders", json=self._payload()).raise_for_status()
        after = client.get("/api/orders").json()
        assert len(after) == len(before) + 1
        assert after[-1]["status"] == "Submitted"

    def test_expected_delivery_uses_max_lead_time(self, client):
        # Item lead times: 7 and 21 — expected_delivery should be ~21 days after order_date
        items = [
            {"sku": "FLT-405", "name": "Oil Filter Cartridge",
             "quantity": 5, "unit_price": 12.0, "lead_time_days": 7},
            {"sku": "BRG-102", "name": "Steel Bearing Assembly",
             "quantity": 3, "unit_price": 85.0, "lead_time_days": 21},
        ]
        response = client.post("/api/orders", json={"items": items})
        assert response.status_code == 201
        order = response.json()
        # Parse ISO timestamps and confirm the gap is 21 days, not 7
        from datetime import datetime
        order_date = datetime.fromisoformat(order["order_date"])
        expected = datetime.fromisoformat(order["expected_delivery"])
        assert (expected - order_date).days == 21

    def test_empty_items_returns_400(self, client):
        response = client.post("/api/orders", json={"items": []})
        assert response.status_code == 400
