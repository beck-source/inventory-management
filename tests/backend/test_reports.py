"""
Tests for reports API endpoints.
"""
import pytest


QUARTERLY_FIELDS = [
    "quarter", "total_orders", "total_revenue",
    "delivered_orders", "avg_order_value", "fulfillment_rate"
]

MONTHLY_FIELDS = ["month", "order_count", "revenue", "delivered_count"]


def order_count(client, query=""):
    """Number of orders the /api/orders endpoint returns for the same filters."""
    response = client.get(f"/api/orders{query}")
    assert response.status_code == 200
    return len(response.json())


class TestQuarterlyReports:
    """Test suite for /api/reports/quarterly."""

    def test_get_all_quarterly(self, client):
        """Test getting quarterly reports without filters."""
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        for field in QUARTERLY_FIELDS:
            assert field in data[0]

    def test_quarterly_field_types(self, client):
        """Test that quarterly fields have proper numeric types."""
        data = client.get("/api/reports/quarterly").json()

        for quarter in data:
            assert isinstance(quarter["quarter"], str)
            assert isinstance(quarter["total_orders"], int)
            assert isinstance(quarter["total_revenue"], (int, float))
            assert isinstance(quarter["delivered_orders"], int)
            assert isinstance(quarter["avg_order_value"], (int, float))
            assert isinstance(quarter["fulfillment_rate"], (int, float))

            assert quarter["total_orders"] >= 0
            assert quarter["total_revenue"] >= 0
            assert quarter["delivered_orders"] <= quarter["total_orders"]

    def test_quarterly_quarter_format(self, client):
        """Test that quarter labels use the Qn-YYYY format the client parses."""
        data = client.get("/api/reports/quarterly").json()

        for quarter in data:
            label = quarter["quarter"]
            assert label.startswith("Q")
            number, year = label.split("-")
            assert number in ["Q1", "Q2", "Q3", "Q4"]
            assert year.isdigit()
            assert len(year) == 4

    def test_quarterly_avg_order_value_calculation(self, client):
        """Test that avg_order_value equals revenue divided by order count."""
        data = client.get("/api/reports/quarterly").json()

        for quarter in data:
            if quarter["total_orders"] > 0:
                expected = quarter["total_revenue"] / quarter["total_orders"]
                assert abs(quarter["avg_order_value"] - expected) < 0.01

    def test_quarterly_fulfillment_rate_calculation(self, client):
        """Test that fulfillment_rate is the delivered share as a percentage."""
        data = client.get("/api/reports/quarterly").json()

        for quarter in data:
            if quarter["total_orders"] > 0:
                expected = (quarter["delivered_orders"] / quarter["total_orders"]) * 100
                assert abs(quarter["fulfillment_rate"] - expected) < 0.1
                assert 0 <= quarter["fulfillment_rate"] <= 100

    def test_quarterly_sorted_by_quarter(self, client):
        """Test that quarters come back in ascending order."""
        data = client.get("/api/reports/quarterly").json()
        labels = [q["quarter"] for q in data]
        assert labels == sorted(labels)

    def test_quarterly_filter_by_warehouse(self, client):
        """Test filtering quarterly reports by warehouse."""
        response = client.get("/api/reports/quarterly?warehouse=Tokyo")
        assert response.status_code == 200

        data = response.json()
        total = sum(q["total_orders"] for q in data)
        assert total == order_count(client, "?warehouse=Tokyo")
        assert total < order_count(client)

    def test_quarterly_filter_by_category(self, client):
        """Test filtering quarterly reports by category."""
        response = client.get("/api/reports/quarterly?category=Power Supplies")
        assert response.status_code == 200

        data = response.json()
        total = sum(q["total_orders"] for q in data)
        assert total == order_count(client, "?category=Power Supplies")

    def test_quarterly_filter_by_status(self, client):
        """Test that filtering to Delivered leaves every quarter fully fulfilled."""
        response = client.get("/api/reports/quarterly?status=Delivered")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0

        for quarter in data:
            assert quarter["delivered_orders"] == quarter["total_orders"]
            assert quarter["fulfillment_rate"] == 100.0

    def test_quarterly_filter_by_month(self, client):
        """Test that a single-month filter narrows the result to that month's quarter."""
        response = client.get("/api/reports/quarterly?month=2025-01")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["quarter"] == "Q1-2025"
        assert data[0]["total_orders"] == order_count(client, "?month=2025-01")

    def test_quarterly_filter_by_quarter(self, client):
        """Test that a quarter filter returns only that quarter."""
        response = client.get("/api/reports/quarterly?month=Q3-2025")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["quarter"] == "Q3-2025"

    def test_quarterly_multiple_filters(self, client):
        """Test combining several filters on quarterly reports."""
        query = "?warehouse=London&category=Power Supplies&status=Delivered"
        response = client.get(f"/api/reports/quarterly{query}")
        assert response.status_code == 200

        data = response.json()
        total = sum(q["total_orders"] for q in data)
        assert total == order_count(client, query)

    def test_quarterly_filter_all_is_noop(self, client):
        """Test that explicit 'all' values behave the same as no filters."""
        unfiltered = client.get("/api/reports/quarterly").json()
        with_all = client.get(
            "/api/reports/quarterly?warehouse=all&category=all&status=all&month=all"
        ).json()
        assert unfiltered == with_all

    def test_quarterly_unmatched_filter_returns_empty(self, client):
        """Test that a filter matching no orders yields an empty report."""
        response = client.get("/api/reports/quarterly?warehouse=Atlantis")
        assert response.status_code == 200
        assert response.json() == []


class TestMonthlyTrends:
    """Test suite for /api/reports/monthly-trends."""

    def test_get_all_monthly(self, client):
        """Test getting monthly trends without filters."""
        response = client.get("/api/reports/monthly-trends")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        for field in MONTHLY_FIELDS:
            assert field in data[0]

    def test_monthly_field_types(self, client):
        """Test that monthly fields have proper numeric types."""
        data = client.get("/api/reports/monthly-trends").json()

        for month in data:
            assert isinstance(month["month"], str)
            assert isinstance(month["order_count"], int)
            assert isinstance(month["revenue"], (int, float))
            assert isinstance(month["delivered_count"], int)

            assert month["order_count"] >= 0
            assert month["revenue"] >= 0
            assert month["delivered_count"] <= month["order_count"]

    def test_monthly_month_format(self, client):
        """Test that month keys use YYYY-MM, which the client splits on."""
        data = client.get("/api/reports/monthly-trends").json()

        for month in data:
            year, month_number = month["month"].split("-")
            assert len(year) == 4 and year.isdigit()
            assert len(month_number) == 2 and month_number.isdigit()
            assert 1 <= int(month_number) <= 12

    def test_monthly_sorted_by_month(self, client):
        """Test that months come back in ascending order.

        The client's month-over-month comparison reads the previous array element,
        so ordering is a correctness requirement, not a presentation detail.
        """
        data = client.get("/api/reports/monthly-trends").json()
        months = [m["month"] for m in data]
        assert months == sorted(months)

    def test_monthly_filter_by_warehouse(self, client):
        """Test filtering monthly trends by warehouse."""
        response = client.get("/api/reports/monthly-trends?warehouse=Tokyo")
        assert response.status_code == 200

        data = response.json()
        total = sum(m["order_count"] for m in data)
        assert total == order_count(client, "?warehouse=Tokyo")
        assert total < order_count(client)

    def test_monthly_filter_by_category(self, client):
        """Test filtering monthly trends by category."""
        response = client.get("/api/reports/monthly-trends?category=Sensors")
        assert response.status_code == 200

        data = response.json()
        total = sum(m["order_count"] for m in data)
        assert total == order_count(client, "?category=Sensors")

    def test_monthly_filter_by_status(self, client):
        """Test that filtering to Delivered leaves every month fully delivered."""
        data = client.get("/api/reports/monthly-trends?status=Delivered").json()
        assert len(data) > 0

        for month in data:
            assert month["delivered_count"] == month["order_count"]

    def test_monthly_filter_by_month(self, client):
        """Test that a single-month filter returns exactly that month."""
        response = client.get("/api/reports/monthly-trends?month=2025-05")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["month"] == "2025-05"
        assert data[0]["order_count"] == order_count(client, "?month=2025-05")

    def test_monthly_filter_by_quarter(self, client):
        """Test that a quarter filter returns at most that quarter's three months."""
        response = client.get("/api/reports/monthly-trends?month=Q2-2025")
        assert response.status_code == 200

        data = response.json()
        assert len(data) <= 3
        for month in data:
            assert month["month"] in ["2025-04", "2025-05", "2025-06"]

    def test_monthly_multiple_filters(self, client):
        """Test combining several filters on monthly trends."""
        query = "?warehouse=San Francisco&status=Shipped"
        response = client.get(f"/api/reports/monthly-trends{query}")
        assert response.status_code == 200

        data = response.json()
        total = sum(m["order_count"] for m in data)
        assert total == order_count(client, query)

    def test_monthly_filter_all_is_noop(self, client):
        """Test that explicit 'all' values behave the same as no filters."""
        unfiltered = client.get("/api/reports/monthly-trends").json()
        with_all = client.get(
            "/api/reports/monthly-trends?warehouse=all&category=all&status=all&month=all"
        ).json()
        assert unfiltered == with_all

    def test_monthly_unmatched_filter_returns_empty(self, client):
        """Test that a filter matching no orders yields an empty trend list."""
        response = client.get("/api/reports/monthly-trends?category=Nonexistent")
        assert response.status_code == 200
        assert response.json() == []


class TestReportsConsistency:
    """Both report endpoints and /api/orders must agree on the same filters."""

    def test_quarterly_and_monthly_agree_unfiltered(self, client):
        """Test that quarterly and monthly totals reconcile with no filters."""
        quarterly = client.get("/api/reports/quarterly").json()
        monthly = client.get("/api/reports/monthly-trends").json()

        assert sum(q["total_orders"] for q in quarterly) == \
            sum(m["order_count"] for m in monthly)
        assert abs(sum(q["total_revenue"] for q in quarterly) -
                   sum(m["revenue"] for m in monthly)) < 0.01

    def test_quarterly_and_monthly_agree_filtered(self, client):
        """Test that the two reports stay reconciled once filtered."""
        query = "?warehouse=Tokyo&status=Delivered"
        quarterly = client.get(f"/api/reports/quarterly{query}").json()
        monthly = client.get(f"/api/reports/monthly-trends{query}").json()

        assert sum(q["total_orders"] for q in quarterly) == \
            sum(m["order_count"] for m in monthly)

    def test_reports_agree_with_dashboard_summary(self, client):
        """Test that report revenue matches the dashboard for identical filters.

        Reports previously ignored the global filters while the dashboard honoured them,
        so the same metric could differ between the two screens. This pins them together.
        """
        query = "?warehouse=London&category=Power Supplies"
        monthly = client.get(f"/api/reports/monthly-trends{query}").json()
        summary = client.get(f"/api/dashboard/summary{query}").json()

        report_revenue = sum(m["revenue"] for m in monthly)
        assert abs(report_revenue - summary["total_orders_value"]) < 0.01

    def test_reports_revenue_matches_orders_endpoint(self, client):
        """Test that report revenue equals the sum of the matching orders' values."""
        query = "?warehouse=Tokyo&category=Sensors"
        monthly = client.get(f"/api/reports/monthly-trends{query}").json()
        orders = client.get(f"/api/orders{query}").json()

        report_revenue = sum(m["revenue"] for m in monthly)
        orders_revenue = sum(o["total_value"] for o in orders)
        assert abs(report_revenue - orders_revenue) < 0.01
