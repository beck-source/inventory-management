"""
Tests for report endpoints (quarterly and monthly trends) and their filters.
"""


class TestReportsEndpoints:
    def test_unfiltered_totals_match_orders(self, client):
        orders = client.get("/api/orders").json()
        monthly = client.get("/api/reports/monthly-trends").json()
        quarterly = client.get("/api/reports/quarterly").json()

        assert sum(m["order_count"] for m in monthly) == len(orders)
        assert sum(q["total_orders"] for q in quarterly) == len(orders)

    def test_month_filter(self, client):
        monthly = client.get("/api/reports/monthly-trends", params={"month": "2025-03"}).json()
        assert [m["month"] for m in monthly] == ["2025-03"]

        quarterly = client.get("/api/reports/quarterly", params={"month": "2025-03"}).json()
        assert [q["quarter"] for q in quarterly] == ["Q1-2025"]

    def test_quarter_filter(self, client):
        monthly = client.get("/api/reports/monthly-trends", params={"month": "Q2-2025"}).json()
        assert {m["month"] for m in monthly} <= {"2025-04", "2025-05", "2025-06"}

    def test_status_filter(self, client):
        expected = client.get("/api/orders", params={"status": "delivered"}).json()
        monthly = client.get("/api/reports/monthly-trends", params={"status": "delivered"}).json()
        quarterly = client.get("/api/reports/quarterly", params={"status": "delivered"}).json()

        assert sum(m["order_count"] for m in monthly) == len(expected)
        assert all(q["fulfillment_rate"] == 100 for q in quarterly)

    def test_warehouse_and_category_filters_match_orders(self, client):
        params = {"warehouse": "Tokyo", "category": "sensors"}
        expected = client.get("/api/orders", params=params).json()
        monthly = client.get("/api/reports/monthly-trends", params=params).json()
        quarterly = client.get("/api/reports/quarterly", params=params).json()

        assert sum(m["order_count"] for m in monthly) == len(expected)
        assert sum(q["total_orders"] for q in quarterly) == len(expected)
        assert round(sum(m["revenue"] for m in monthly), 2) == round(sum(o["total_value"] for o in expected), 2)
