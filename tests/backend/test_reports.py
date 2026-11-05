"""
Tests for reports API endpoints.
"""
import pytest


class TestReportsEndpoints:
    """Test suite for quarterly and monthly-trend report endpoints."""

    def test_get_quarterly_reports(self, client):
        """Test getting quarterly reports without filters."""
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        first = data[0]
        assert "quarter" in first
        assert "total_orders" in first
        assert "total_revenue" in first
        assert "delivered_orders" in first
        assert "avg_order_value" in first
        assert "fulfillment_rate" in first

    def test_quarterly_reports_sorted_and_valid(self, client):
        """Test that quarters are sorted and fulfillment rate is a valid percentage."""
        data = client.get("/api/reports/quarterly").json()

        quarters = [q["quarter"] for q in data]
        assert quarters == sorted(quarters)

        for q in data:
            assert q["total_orders"] > 0
            assert 0 <= q["fulfillment_rate"] <= 100
            assert abs(q["avg_order_value"] - q["total_revenue"] / q["total_orders"]) < 0.01

    def test_get_monthly_trends(self, client):
        """Test getting monthly trends without filters."""
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

        months = [m["month"] for m in data]
        assert months == sorted(months)

    def test_reports_match_orders_totals(self, client):
        """Test that report totals agree with the raw orders data."""
        all_orders = client.get("/api/orders").json()
        quarterly = client.get("/api/reports/quarterly").json()
        monthly = client.get("/api/reports/monthly-trends").json()

        assert sum(m["order_count"] for m in monthly) == len(all_orders)
        assert abs(
            sum(m["revenue"] for m in monthly) - sum(o["total_value"] for o in all_orders)
        ) < 0.01
        # Quarterly only covers dates inside a known quarter
        assert sum(q["total_orders"] for q in quarterly) <= len(all_orders)

    @pytest.mark.parametrize("endpoint", ["quarterly", "monthly-trends"])
    def test_reports_by_warehouse(self, client, endpoint):
        """Test that the warehouse filter narrows report results."""
        all_orders = client.get("/api/orders?warehouse=Tokyo").json()
        response = client.get(f"/api/reports/{endpoint}?warehouse=Tokyo")
        assert response.status_code == 200

        data = response.json()
        count_key = "total_orders" if endpoint == "quarterly" else "order_count"
        assert sum(row[count_key] for row in data) <= len(all_orders)
        assert sum(row[count_key] for row in data) > 0

    def test_monthly_trends_by_warehouse_matches_orders(self, client):
        """Test that filtered monthly trends equal the filtered orders."""
        filtered_orders = client.get("/api/orders?warehouse=London").json()
        monthly = client.get("/api/reports/monthly-trends?warehouse=London").json()

        assert sum(m["order_count"] for m in monthly) == len(filtered_orders)

    def test_reports_by_category(self, client):
        """Test filtering monthly trends by category."""
        filtered_orders = client.get("/api/orders?category=Sensors").json()
        monthly = client.get("/api/reports/monthly-trends?category=Sensors").json()

        assert sum(m["order_count"] for m in monthly) == len(filtered_orders)

    def test_reports_by_status(self, client):
        """Test that filtering by Delivered gives a 100% fulfillment rate."""
        response = client.get("/api/reports/quarterly?status=Delivered")
        assert response.status_code == 200

        for q in response.json():
            assert q["fulfillment_rate"] == 100

    def test_reports_by_month(self, client):
        """Test filtering by a single month returns only that month."""
        response = client.get("/api/reports/monthly-trends?month=2025-03")
        assert response.status_code == 200

        data = response.json()
        assert all(m["month"] == "2025-03" for m in data)

    def test_reports_by_quarter(self, client):
        """Test filtering by quarter returns only months in that quarter."""
        monthly = client.get("/api/reports/monthly-trends?month=Q2-2025").json()
        assert all(m["month"] in ("2025-04", "2025-05", "2025-06") for m in monthly)

        quarterly = client.get("/api/reports/quarterly?month=Q2-2025").json()
        assert all(q["quarter"] == "Q2-2025" for q in quarterly)

    def test_reports_multiple_filters(self, client):
        """Test combining filters stays consistent with the orders endpoint."""
        query = "warehouse=San Francisco&category=Power Supplies&status=Delivered"
        filtered_orders = client.get(f"/api/orders?{query}").json()
        monthly = client.get(f"/api/reports/monthly-trends?{query}").json()

        assert sum(m["order_count"] for m in monthly) == len(filtered_orders)

    def test_reports_all_filter_values_ignored(self, client):
        """Test that 'all' behaves like no filter."""
        unfiltered = client.get("/api/reports/monthly-trends").json()
        with_all = client.get(
            "/api/reports/monthly-trends?warehouse=all&category=all&status=all&month=all"
        ).json()

        assert unfiltered == with_all

    def test_reports_no_matching_orders(self, client):
        """Test that a filter with no matches returns an empty list, not an error."""
        for endpoint in ("quarterly", "monthly-trends"):
            response = client.get(f"/api/reports/{endpoint}?warehouse=Nowhere")
            assert response.status_code == 200
            assert response.json() == []
