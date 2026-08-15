"""
Tests for reports API endpoints.
"""
import pytest


class TestQuarterlyReportsEndpoint:
    """Test suite for GET /api/reports/quarterly."""

    def test_get_quarterly_reports_unfiltered(self, client):
        """Test getting all quarterly reports without filters."""
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_quarterly_reports_structure(self, client):
        """Test that quarterly reports have correct structure."""
        response = client.get("/api/reports/quarterly")
        data = response.json()

        for quarter in data:
            assert "quarter" in quarter
            assert "total_orders" in quarter
            assert "total_revenue" in quarter
            assert "avg_order_value" in quarter
            assert "fulfillment_rate" in quarter
            assert isinstance(quarter["total_orders"], int)
            assert isinstance(quarter["total_revenue"], (int, float))
            assert isinstance(quarter["avg_order_value"], (int, float))
            assert isinstance(quarter["fulfillment_rate"], (int, float))
            assert quarter["total_orders"] > 0
            assert quarter["total_revenue"] > 0

    def test_quarterly_reports_sorted_by_quarter(self, client):
        """Test that quarterly reports are sorted by quarter."""
        response = client.get("/api/reports/quarterly")
        data = response.json()

        quarters = [q["quarter"] for q in data]
        assert quarters == sorted(quarters)

    def test_quarterly_reports_filter_by_warehouse(self, client):
        """Test filtering quarterly reports by warehouse."""
        response = client.get("/api/reports/quarterly?warehouse=Tokyo")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        # Filtered results should have fewer or equal orders than unfiltered
        unfiltered = client.get("/api/reports/quarterly").json()
        total_filtered_orders = sum(q["total_orders"] for q in data)
        total_unfiltered_orders = sum(q["total_orders"] for q in unfiltered)
        assert total_filtered_orders <= total_unfiltered_orders

    def test_quarterly_reports_filter_by_category(self, client):
        """Test filtering quarterly reports by category."""
        response = client.get("/api/reports/quarterly?category=Sensors")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        unfiltered = client.get("/api/reports/quarterly").json()
        total_filtered_orders = sum(q["total_orders"] for q in data)
        total_unfiltered_orders = sum(q["total_orders"] for q in unfiltered)
        assert total_filtered_orders <= total_unfiltered_orders

    def test_quarterly_reports_filter_by_status(self, client):
        """Test filtering quarterly reports by status."""
        response = client.get("/api/reports/quarterly?status=Delivered")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_quarterly_reports_filter_by_month(self, client):
        """Test filtering quarterly reports by month."""
        response = client.get("/api/reports/quarterly?month=2025-01")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        # Only Q1-2025 should appear when filtering by January
        for quarter in data:
            assert quarter["quarter"] == "Q1-2025"

    def test_quarterly_reports_filter_all_passes_through(self, client):
        """Test that filter value 'all' returns same as unfiltered."""
        unfiltered = client.get("/api/reports/quarterly").json()
        filtered = client.get("/api/reports/quarterly?warehouse=all&category=all").json()

        assert len(unfiltered) == len(filtered)

    def test_quarterly_reports_avg_order_value_calculation(self, client):
        """Test that avg_order_value equals total_revenue / total_orders."""
        response = client.get("/api/reports/quarterly")
        data = response.json()

        for quarter in data:
            expected_avg = round(quarter["total_revenue"] / quarter["total_orders"], 2)
            assert abs(quarter["avg_order_value"] - expected_avg) < 0.01

    def test_quarterly_reports_fulfillment_rate_range(self, client):
        """Test that fulfillment rate is between 0 and 100."""
        response = client.get("/api/reports/quarterly")
        data = response.json()

        for quarter in data:
            assert 0 <= quarter["fulfillment_rate"] <= 100


class TestMonthlyTrendsEndpoint:
    """Test suite for GET /api/reports/monthly-trends."""

    def test_get_monthly_trends_unfiltered(self, client):
        """Test getting all monthly trends without filters."""
        response = client.get("/api/reports/monthly-trends")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_monthly_trends_structure(self, client):
        """Test that monthly trends have correct structure."""
        response = client.get("/api/reports/monthly-trends")
        data = response.json()

        for month in data:
            assert "month" in month
            assert "order_count" in month
            assert "revenue" in month
            assert "delivered_count" in month
            assert isinstance(month["order_count"], int)
            assert isinstance(month["revenue"], (int, float))
            assert isinstance(month["delivered_count"], int)
            assert month["order_count"] > 0
            assert month["revenue"] > 0

    def test_monthly_trends_month_format(self, client):
        """Test that month field is in YYYY-MM format."""
        response = client.get("/api/reports/monthly-trends")
        data = response.json()

        for month in data:
            assert len(month["month"]) == 7
            assert month["month"][4] == "-"
            assert month["month"][:4].isdigit()
            assert month["month"][5:].isdigit()

    def test_monthly_trends_sorted_by_month(self, client):
        """Test that monthly trends are sorted chronologically."""
        response = client.get("/api/reports/monthly-trends")
        data = response.json()

        months = [m["month"] for m in data]
        assert months == sorted(months)

    def test_monthly_trends_filter_by_warehouse(self, client):
        """Test filtering monthly trends by warehouse."""
        response = client.get("/api/reports/monthly-trends?warehouse=Tokyo")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        unfiltered = client.get("/api/reports/monthly-trends").json()
        total_filtered_orders = sum(m["order_count"] for m in data)
        total_unfiltered_orders = sum(m["order_count"] for m in unfiltered)
        assert total_filtered_orders <= total_unfiltered_orders

    def test_monthly_trends_filter_by_category(self, client):
        """Test filtering monthly trends by category."""
        response = client.get("/api/reports/monthly-trends?category=Power Supplies")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        unfiltered = client.get("/api/reports/monthly-trends").json()
        total_filtered = sum(m["order_count"] for m in data)
        total_unfiltered = sum(m["order_count"] for m in unfiltered)
        assert total_filtered <= total_unfiltered

    def test_monthly_trends_filter_by_status(self, client):
        """Test filtering monthly trends by status."""
        response = client.get("/api/reports/monthly-trends?status=Delivered")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        # When filtered to delivered only, delivered_count should equal order_count
        for month in data:
            assert month["delivered_count"] == month["order_count"]

    def test_monthly_trends_filter_by_month(self, client):
        """Test filtering monthly trends by specific month."""
        response = client.get("/api/reports/monthly-trends?month=2025-03")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        # Should only contain March 2025
        for month in data:
            assert month["month"] == "2025-03"

    def test_monthly_trends_filter_all_passes_through(self, client):
        """Test that filter value 'all' returns same as unfiltered."""
        unfiltered = client.get("/api/reports/monthly-trends").json()
        filtered = client.get("/api/reports/monthly-trends?warehouse=all&category=all").json()

        assert len(unfiltered) == len(filtered)

    def test_monthly_trends_delivered_count_not_exceeds_total(self, client):
        """Test that delivered_count never exceeds order_count."""
        response = client.get("/api/reports/monthly-trends")
        data = response.json()

        for month in data:
            assert month["delivered_count"] <= month["order_count"]

    def test_monthly_trends_multiple_filters(self, client):
        """Test filtering monthly trends with multiple filters."""
        response = client.get(
            "/api/reports/monthly-trends?warehouse=San Francisco&category=Sensors"
        )
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        # Combined filters should produce fewer results
        warehouse_only = client.get(
            "/api/reports/monthly-trends?warehouse=San Francisco"
        ).json()
        total_combined = sum(m["order_count"] for m in data)
        total_warehouse = sum(m["order_count"] for m in warehouse_only)
        assert total_combined <= total_warehouse
