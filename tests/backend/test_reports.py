"""
Tests for report endpoints (quarterly, monthly trends), including global filter support.
"""


class TestReportsFilters:
    """Report endpoints must honor the same filters as /api/orders."""

    def test_quarterly_unfiltered(self, client):
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        for q in data:
            assert {"quarter", "total_orders", "total_revenue", "avg_order_value", "fulfillment_rate"} <= q.keys()

    def test_monthly_trends_match_filtered_orders(self, client):
        params = {"warehouse": "Tokyo", "category": "sensors", "status": "Delivered"}
        orders = client.get("/api/orders", params=params).json()
        trends = client.get("/api/reports/monthly-trends", params=params).json()

        assert sum(m["order_count"] for m in trends) == len(orders)
        assert round(sum(m["revenue"] for m in trends), 2) == round(sum(o["total_value"] for o in orders), 2)

    def test_quarterly_matches_filtered_orders(self, client):
        params = {"warehouse": "London", "category": "actuators"}
        orders = client.get("/api/orders", params=params).json()
        quarterly = client.get("/api/reports/quarterly", params=params).json()

        assert sum(q["total_orders"] for q in quarterly) == len(orders)

    def test_month_filter_limits_trends(self, client):
        trends = client.get("/api/reports/monthly-trends", params={"month": "2025-03"}).json()
        assert [m["month"] for m in trends] == ["2025-03"]

    def test_quarter_filter_limits_quarterly(self, client):
        quarterly = client.get("/api/reports/quarterly", params={"month": "Q2-2025"}).json()
        assert [q["quarter"] for q in quarterly] == ["Q2-2025"]

    def test_filters_reduce_totals(self, client):
        all_trends = client.get("/api/reports/monthly-trends").json()
        filtered = client.get("/api/reports/monthly-trends", params={"warehouse": "Tokyo"}).json()
        assert sum(m["order_count"] for m in filtered) < sum(m["order_count"] for m in all_trends)
