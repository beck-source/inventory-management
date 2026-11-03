"""
Tests for report endpoints (quarterly and monthly trends) including filters.
"""
import pytest


class TestQuarterlyReports:
    def test_unfiltered(self, client):
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        for quarter in data:
            assert 0 <= quarter["fulfillment_rate"] <= 100

    def test_warehouse_filter_reduces_orders(self, client):
        all_total = sum(q["total_orders"] for q in client.get("/api/reports/quarterly").json())
        orders = client.get("/api/orders").json()
        warehouse = orders[0]["warehouse"]
        expected = len([o for o in orders if o["warehouse"] == warehouse])

        data = client.get("/api/reports/quarterly", params={"warehouse": warehouse}).json()
        filtered_total = sum(q["total_orders"] for q in data)
        assert filtered_total <= all_total
        assert filtered_total <= expected

    def test_all_values_match_unfiltered(self, client):
        base = client.get("/api/reports/quarterly").json()
        data = client.get(
            "/api/reports/quarterly",
            params={"warehouse": "all", "category": "all", "status": "all", "month": "all"},
        ).json()
        assert data == base

    def test_invalid_month(self, client):
        assert client.get("/api/reports/quarterly?month=bogus").status_code == 400


class TestMonthlyTrends:
    def test_unfiltered(self, client):
        response = client.get("/api/reports/monthly-trends")
        assert response.status_code == 200
        months = [m["month"] for m in response.json()]
        assert months == sorted(months)

    def test_month_filter(self, client):
        base = client.get("/api/reports/monthly-trends").json()
        month = base[0]["month"]
        data = client.get("/api/reports/monthly-trends", params={"month": month}).json()
        assert [m["month"] for m in data] == [month]

    def test_status_filter(self, client):
        data = client.get("/api/reports/monthly-trends", params={"status": "Delivered"}).json()
        for m in data:
            assert m["order_count"] == m["delivered_count"]

    def test_invalid_month(self, client):
        assert client.get("/api/reports/monthly-trends?month=bogus").status_code == 400
