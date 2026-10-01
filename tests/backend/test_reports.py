"""
Tests for report endpoints (quarterly and monthly trends).
"""
import pytest


class TestQuarterlyReports:
    """Test suite for /api/reports/quarterly."""

    def test_get_quarterly_reports(self, client):
        """Test getting quarterly reports without filters."""
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200

        data = response.json()
        assert [q["quarter"] for q in data] == ["Q1-2025", "Q2-2025", "Q3-2025", "Q4-2025"]
        for quarter in data:
            assert "total_orders" in quarter
            assert "total_revenue" in quarter
            assert "avg_order_value" in quarter
            assert 0 <= quarter["fulfillment_rate"] <= 100

    def test_quarterly_totals_match_orders(self, client):
        """Test that quarterly order counts add up to all orders."""
        orders = client.get("/api/orders").json()
        quarters = client.get("/api/reports/quarterly").json()
        assert sum(q["total_orders"] for q in quarters) == len(orders)

    def test_quarterly_filter_by_warehouse(self, client):
        """Test that warehouse filter narrows quarterly totals."""
        orders = client.get("/api/orders?warehouse=Tokyo").json()
        quarters = client.get("/api/reports/quarterly?warehouse=Tokyo").json()
        assert sum(q["total_orders"] for q in quarters) == len(orders)
        assert sum(q["total_revenue"] for q in quarters) == pytest.approx(
            sum(o["total_value"] for o in orders)
        )

    def test_quarterly_filter_by_quarter(self, client):
        """Test that a quarter period filter returns only that quarter."""
        response = client.get("/api/reports/quarterly?month=Q2-2025")
        assert response.status_code == 200
        assert [q["quarter"] for q in response.json()] == ["Q2-2025"]

    def test_quarterly_all_means_no_filter(self, client):
        """Test that 'all' filter values behave like no filter."""
        unfiltered = client.get("/api/reports/quarterly").json()
        with_all = client.get(
            "/api/reports/quarterly?warehouse=all&category=all&status=all&month=all"
        ).json()
        assert with_all == unfiltered


class TestMonthlyTrends:
    """Test suite for /api/reports/monthly-trends."""

    def test_get_monthly_trends(self, client):
        """Test getting monthly trends without filters."""
        response = client.get("/api/reports/monthly-trends")
        assert response.status_code == 200

        data = response.json()
        months = [m["month"] for m in data]
        assert months == sorted(months)
        assert months[0] == "2025-01"
        assert months[-1] == "2025-12"
        for month in data:
            assert "order_count" in month
            assert "revenue" in month

    def test_monthly_filter_by_category_and_status(self, client):
        """Test that category and status filters narrow monthly totals."""
        params = "category=Sensors&status=Delivered"
        orders = client.get(f"/api/orders?{params}").json()
        months = client.get(f"/api/reports/monthly-trends?{params}").json()
        assert sum(m["order_count"] for m in months) == len(orders)
        assert all(m["delivered_count"] == m["order_count"] for m in months)

    def test_monthly_filter_by_month(self, client):
        """Test that a single month filter returns only that month."""
        response = client.get("/api/reports/monthly-trends?month=2025-03")
        assert response.status_code == 200
        assert [m["month"] for m in response.json()] == ["2025-03"]

    def test_monthly_unknown_warehouse_returns_empty(self, client):
        """Test that a warehouse with no orders returns an empty list."""
        response = client.get("/api/reports/monthly-trends?warehouse=Nowhere")
        assert response.status_code == 200
        assert response.json() == []
