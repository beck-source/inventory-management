"""
Tests for the reports endpoints (quarterly performance, monthly trends).
"""
import pytest


class TestReportsFiltering:
    """Reports endpoints must honor the same filters as /api/orders."""

    def test_quarterly_reports_unfiltered(self, client):
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_quarterly_reports_status_filter_narrows_results(self, client):
        unfiltered = client.get("/api/reports/quarterly").json()
        filtered = client.get("/api/reports/quarterly?status=Delivered").json()

        total_unfiltered = sum(q["total_orders"] for q in unfiltered)
        total_filtered = sum(q["total_orders"] for q in filtered)
        assert total_filtered <= total_unfiltered

    def test_quarterly_reports_warehouse_filter_matches_orders_count(self, client):
        orders = client.get("/api/orders?warehouse=Tokyo").json()
        quarterly = client.get("/api/reports/quarterly?warehouse=Tokyo").json()

        assert sum(q["total_orders"] for q in quarterly) == len(orders)

    def test_monthly_trends_unfiltered(self, client):
        response = client.get("/api/reports/monthly-trends")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_monthly_trends_month_filter(self, client):
        orders = client.get("/api/orders?month=2025-01").json()
        monthly = client.get("/api/reports/monthly-trends?month=2025-01").json()

        assert sum(m["order_count"] for m in monthly) == len(orders)
        assert all(m["month"] == "2025-01" for m in monthly)

    def test_monthly_trends_category_filter_matches_orders_count(self, client):
        orders = client.get("/api/orders?category=sensors").json()
        monthly = client.get("/api/reports/monthly-trends?category=sensors").json()

        assert sum(m["order_count"] for m in monthly) == len(orders)
