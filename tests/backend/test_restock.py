"""
Tests for the restocking-order endpoints (POST/GET /api/restock-orders).
"""


def _payload():
    """Two restock lines with different trends to exercise lead-time selection."""
    return {
        "budget": 5000,
        "items": [
            {"sku": "WDG-001", "name": "Industrial Widget Type A",
             "quantity": 150, "unit_price": 12.50, "trend": "increasing"},
            {"sku": "GSK-203", "name": "High-Temperature Gasket",
             "quantity": 100, "unit_price": 8.75, "trend": "stable"},
        ],
    }


def test_demand_forecast_includes_unit_cost(client):
    """Forecast items now carry unit_cost so the frontend can budget against them."""
    resp = client.get("/api/demand")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    assert all("unit_cost" in item for item in data)


def test_submit_restock_order(client):
    resp = client.post("/api/restock-orders", json=_payload())
    assert resp.status_code == 200
    order = resp.json()

    assert order["status"] == "Submitted"
    assert order["order_number"].startswith("RST-")
    # total_value = sum(qty * unit_price): 150*12.50 + 100*8.75 = 1875 + 875 = 2750
    assert order["total_value"] == 2750.0
    # Order completes with the slowest line: stable (14d) beats increasing (7d).
    assert "lead_time_days" in order["items"][0]
    assert max(i["lead_time_days"] for i in order["items"]) == 14


def test_submitted_order_appears_in_orders(client):
    """A submitted order is appended to the in-memory orders list and shows in GET /api/orders."""
    created = client.post("/api/restock-orders", json=_payload()).json()
    all_orders = client.get("/api/orders").json()
    assert any(o["id"] == created["id"] and o["status"] == "Submitted" for o in all_orders)

    submitted = client.get("/api/restock-orders").json()
    assert any(o["id"] == created["id"] for o in submitted)


def test_submit_empty_order_rejected(client):
    resp = client.post("/api/restock-orders", json={"items": [], "budget": 1000})
    assert resp.status_code == 400
