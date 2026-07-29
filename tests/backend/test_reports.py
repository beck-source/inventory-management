"""
Tests for reports API endpoints.
"""
import pytest


class TestQuarterlyReportsEndpoint:
    """Test suite for quarterly reports endpoint."""

    def test_get_quarterly_reports(self, client):
        """Test getting quarterly reports."""
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        first = data[0]
        assert "quarter" in first
        assert "total_orders" in first
        assert "total_revenue" in first
        assert "avg_order_value" in first
        assert "fulfillment_rate" in first

    def test_quarterly_reports_by_warehouse(self, client):
        """Test filtering quarterly reports by warehouse narrows the totals."""
        all_response = client.get("/api/reports/quarterly")
        filtered_response = client.get("/api/reports/quarterly?warehouse=Tokyo")
        assert filtered_response.status_code == 200

        all_data = all_response.json()
        filtered_data = filtered_response.json()

        all_total = sum(q["total_orders"] for q in all_data)
        filtered_total = sum(q["total_orders"] for q in filtered_data)
        assert filtered_total < all_total
        assert filtered_total > 0

    def test_quarterly_reports_by_month(self, client):
        """Test filtering quarterly reports by a single month only reflects that month."""
        response = client.get("/api/reports/quarterly?month=2025-01")
        assert response.status_code == 200

        data = response.json()
        # January 2025 orders should only ever roll up into Q1-2025
        for q in data:
            assert q["quarter"] == "Q1-2025"

    def test_quarterly_reports_all_filter(self, client):
        """Test that 'all' filter values return the same result as no filters."""
        response_all = client.get("/api/reports/quarterly?warehouse=all&status=all")
        response_no_filter = client.get("/api/reports/quarterly")

        assert response_all.status_code == 200
        assert response_all.json() == response_no_filter.json()

    def test_quarterly_reports_fulfillment_rate_range(self, client):
        """Test that fulfillment rate is a sane percentage."""
        response = client.get("/api/reports/quarterly")
        data = response.json()

        for q in data:
            assert 0 <= q["fulfillment_rate"] <= 100


class TestMonthlyTrendsEndpoint:
    """Test suite for monthly trends endpoint."""

    def test_get_monthly_trends(self, client):
        """Test getting monthly trends."""
        response = client.get("/api/reports/monthly-trends")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        first = data[0]
        assert "month" in first
        assert "order_count" in first
        assert "revenue" in first
        assert "delivered_count" in first

    def test_monthly_trends_by_month_filter(self, client):
        """Test filtering monthly trends down to a single month."""
        response = client.get("/api/reports/monthly-trends?month=2025-01")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["month"] == "2025-01"

    def test_monthly_trends_by_warehouse(self, client):
        """Test filtering monthly trends by warehouse narrows revenue."""
        all_response = client.get("/api/reports/monthly-trends")
        filtered_response = client.get("/api/reports/monthly-trends?warehouse=London")
        assert filtered_response.status_code == 200

        all_revenue = sum(m["revenue"] for m in all_response.json())
        filtered_revenue = sum(m["revenue"] for m in filtered_response.json())
        assert filtered_revenue < all_revenue
        assert filtered_revenue > 0

    def test_monthly_trends_multiple_filters(self, client):
        """Test combining warehouse and status filters."""
        response = client.get("/api/reports/monthly-trends?warehouse=San Francisco&status=Delivered")
        assert response.status_code == 200

        data = response.json()
        for m in data:
            # order_count should equal delivered_count since status is fully filtered to Delivered
            assert m["order_count"] == m["delivered_count"]

    def test_monthly_trends_sorted_chronologically(self, client):
        """Test that monthly trends are returned sorted by month ascending."""
        response = client.get("/api/reports/monthly-trends")
        data = response.json()

        months = [m["month"] for m in data]
        assert months == sorted(months)
