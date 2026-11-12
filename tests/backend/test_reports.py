"""
Tests for reports API endpoints (quarterly and monthly trends).
"""
import pytest


def _orders(client, query=""):
    return client.get(f"/api/orders{query}").json()


class TestQuarterlyReportsEndpoints:
    """Test suite for /api/reports/quarterly."""

    def test_get_quarterly_reports(self, client):
        """Test getting unfiltered quarterly reports."""
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        for q in data:
            for field in ["quarter", "total_orders", "total_revenue",
                          "avg_order_value", "fulfillment_rate"]:
                assert field in q

    def test_quarterly_totals_match_orders(self, client):
        """Test that quarterly order counts sum to the total order count."""
        data = client.get("/api/reports/quarterly").json()
        assert sum(q["total_orders"] for q in data) == len(_orders(client))

    def test_get_quarterly_reports_by_warehouse(self, client):
        """Test that the warehouse filter changes quarterly totals."""
        data = client.get("/api/reports/quarterly?warehouse=San Francisco").json()
        expected = _orders(client, "?warehouse=San Francisco")

        assert sum(q["total_orders"] for q in data) == len(expected)
        assert abs(
            sum(q["total_revenue"] for q in data)
            - sum(o["total_value"] for o in expected)
        ) < 0.01

    def test_get_quarterly_reports_by_month(self, client):
        """Test that a single-month filter yields only that month's quarter."""
        data = client.get("/api/reports/quarterly?month=2025-01").json()

        assert [q["quarter"] for q in data] == ["Q1-2025"]
        assert data[0]["total_orders"] == len(_orders(client, "?month=2025-01"))

    def test_get_quarterly_reports_by_quarter(self, client):
        """Test filtering quarterly reports by quarter."""
        data = client.get("/api/reports/quarterly?month=Q2-2025").json()
        assert all(q["quarter"] == "Q2-2025" for q in data)

    def test_get_quarterly_reports_multiple_filters(self, client):
        """Test quarterly reports with combined filters."""
        query = "?warehouse=Tokyo&category=Sensors&status=Delivered"
        data = client.get(f"/api/reports/quarterly{query}").json()

        assert sum(q["total_orders"] for q in data) == len(_orders(client, query))
        # Every remaining order is Delivered, so fulfillment must be 100%
        for q in data:
            assert q["fulfillment_rate"] == 100.0

    def test_get_quarterly_reports_no_matches(self, client):
        """Test that a filter matching nothing returns an empty list."""
        response = client.get("/api/reports/quarterly?warehouse=Nowhere")
        assert response.status_code == 200
        assert response.json() == []


class TestMonthlyTrendsEndpoints:
    """Test suite for /api/reports/monthly-trends."""

    def test_get_monthly_trends(self, client):
        """Test getting unfiltered monthly trends, sorted by month."""
        response = client.get("/api/reports/monthly-trends")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        months = [m["month"] for m in data]
        assert months == sorted(months)
        for m in data:
            assert "order_count" in m
            assert "revenue" in m
            assert isinstance(m["order_count"], int)

    def test_get_monthly_trends_by_warehouse(self, client):
        """Test that the warehouse filter applies to monthly trends."""
        data = client.get("/api/reports/monthly-trends?warehouse=London").json()
        expected = _orders(client, "?warehouse=London")

        assert sum(m["order_count"] for m in data) == len(expected)

    def test_get_monthly_trends_by_month(self, client):
        """Test that a month filter returns only that month."""
        data = client.get("/api/reports/monthly-trends?month=2025-03").json()
        assert [m["month"] for m in data] == ["2025-03"]

    def test_get_monthly_trends_by_quarter(self, client):
        """Test that a quarter filter returns only that quarter's months."""
        data = client.get("/api/reports/monthly-trends?month=Q1-2025").json()
        assert len(data) > 0
        assert all(m["month"] in ["2025-01", "2025-02", "2025-03"] for m in data)

    def test_get_monthly_trends_by_category_and_status(self, client):
        """Test monthly trends with category and status filters."""
        query = "?category=Circuit Boards&status=Shipped"
        data = client.get(f"/api/reports/monthly-trends{query}").json()
        assert sum(m["order_count"] for m in data) == len(_orders(client, query))

    @pytest.mark.parametrize("value", ["all"])
    def test_all_filter_values_are_ignored(self, client, value):
        """Test that 'all' behaves like no filter."""
        unfiltered = client.get("/api/reports/monthly-trends").json()
        filtered = client.get(
            f"/api/reports/monthly-trends?warehouse={value}&category={value}"
            f"&status={value}&month={value}"
        ).json()
        assert filtered == unfiltered
