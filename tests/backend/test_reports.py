"""
Tests for the report endpoints' new query-param filtering:
  - GET /api/reports/quarterly
  - GET /api/reports/monthly-trends

Both endpoints accept optional ``warehouse``, ``category``, ``status`` and
``month`` params, apply ``apply_filters(...)`` then ``filter_by_month(...)``,
and aggregate the surviving orders.

Test-isolation note: the module-global ``orders`` list is shared and mutated
across the whole pytest session (POST /api/orders in test_orders_create.py runs
first alphabetically and appends "Submitted" orders dated in the current year,
not 2025). These tests therefore avoid hardcoded counts/totals. Instead they
cross-validate each report against GET /api/orders using the *same* query
params -- that endpoint applies the identical apply_filters + filter_by_month
pipeline, so it returns exactly the set of orders the report aggregates over.
"""
import pytest


# Quarter bucketing mirrors the endpoint's order_date substring logic so the
# expected aggregation is derived from the same raw orders the report sees.
_QUARTER_MONTHS = {
    "Q1-2025": ("2025-01", "2025-02", "2025-03"),
    "Q2-2025": ("2025-04", "2025-05", "2025-06"),
    "Q3-2025": ("2025-07", "2025-08", "2025-09"),
    "Q4-2025": ("2025-10", "2025-11", "2025-12"),
}


def _quarter_of(order_date):
    """Return the quarter key for an order_date, or None if it maps to none
    (mirrors the endpoint's final `else: continue`)."""
    for quarter, months in _QUARTER_MONTHS.items():
        if any(m in order_date for m in months):
            return quarter
    return None


def _expected_quarterly(orders):
    """Aggregate a list of orders into the quarterly report shape."""
    quarters = {}
    for order in orders:
        quarter = _quarter_of(order.get("order_date", ""))
        if quarter is None:
            continue
        bucket = quarters.setdefault(
            quarter, {"total_orders": 0, "total_revenue": 0.0, "delivered_orders": 0}
        )
        bucket["total_orders"] += 1
        bucket["total_revenue"] += order.get("total_value", 0)
        if order.get("status") == "Delivered":
            bucket["delivered_orders"] += 1
    return quarters


def _expected_monthly(orders):
    """Aggregate a list of orders into the monthly-trends report shape."""
    months = {}
    for order in orders:
        order_date = order.get("order_date", "")
        if not order_date:
            continue
        key = order_date[:7]
        bucket = months.setdefault(
            key, {"order_count": 0, "revenue": 0.0, "delivered_count": 0}
        )
        bucket["order_count"] += 1
        bucket["revenue"] += order.get("total_value", 0)
        if order.get("status") == "Delivered":
            bucket["delivered_count"] += 1
    return months


QUARTERLY_KEYS = {
    "quarter",
    "total_orders",
    "total_revenue",
    "avg_order_value",
    "fulfillment_rate",
}
MONTHLY_KEYS = {"month", "order_count", "revenue"}


class TestQuarterlyReport:
    """Test suite for GET /api/reports/quarterly filtering."""

    def test_quarterly_no_filters_returns_full_aggregation(self, client):
        """No filters -> list of quarter dicts with the expected keys."""
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        for entry in data:
            assert isinstance(entry, dict)
            assert QUARTERLY_KEYS.issubset(entry.keys()), (
                f"Missing keys: {QUARTERLY_KEYS - set(entry.keys())}"
            )
            assert entry["quarter"] in _QUARTER_MONTHS
            assert isinstance(entry["total_orders"], int)
            assert isinstance(entry["total_revenue"], (int, float))
            assert isinstance(entry["avg_order_value"], (int, float))
            assert isinstance(entry["fulfillment_rate"], (int, float))

        # Sorted ascending by quarter.
        quarters = [entry["quarter"] for entry in data]
        assert quarters == sorted(quarters)

    def test_quarterly_matches_raw_orders_aggregation(self, client):
        """Unfiltered quarterly numbers match an aggregation of GET /api/orders."""
        report = {q["quarter"]: q for q in client.get("/api/reports/quarterly").json()}
        raw_orders = client.get("/api/orders").json()
        expected = _expected_quarterly(raw_orders)

        assert set(report.keys()) == set(expected.keys())
        for quarter, exp in expected.items():
            got = report[quarter]
            assert got["total_orders"] == exp["total_orders"]
            assert abs(got["total_revenue"] - exp["total_revenue"]) < 0.01
            expected_avg = round(exp["total_revenue"] / exp["total_orders"], 2)
            assert abs(got["avg_order_value"] - expected_avg) < 0.01
            expected_rate = round(
                (exp["delivered_orders"] / exp["total_orders"]) * 100, 1
            )
            assert abs(got["fulfillment_rate"] - expected_rate) < 0.01

    def test_quarterly_warehouse_filter_is_strict_subset(self, client):
        """warehouse=Tokyo -> only Tokyo orders contribute and totals drop below the
        unfiltered totals (Tokyo is a strict subset of the data)."""
        all_report = client.get("/api/reports/quarterly").json()
        tokyo_report = client.get("/api/reports/quarterly?warehouse=Tokyo").json()

        # Every contributing order is from Tokyo (verified via the raw endpoint
        # that feeds the same pipeline).
        tokyo_orders = client.get("/api/orders?warehouse=Tokyo").json()
        assert len(tokyo_orders) > 0
        for order in tokyo_orders:
            assert order["warehouse"] == "Tokyo"

        # Aggregation matches the Tokyo-only orders.
        expected = _expected_quarterly(tokyo_orders)
        report = {q["quarter"]: q for q in tokyo_report}
        assert set(report.keys()) == set(expected.keys())
        for quarter, exp in expected.items():
            assert report[quarter]["total_orders"] == exp["total_orders"]
            assert abs(report[quarter]["total_revenue"] - exp["total_revenue"]) < 0.01

        # Strictly less than the unfiltered totals.
        all_orders_total = sum(q["total_orders"] for q in all_report)
        tokyo_orders_total = sum(q["total_orders"] for q in tokyo_report)
        all_revenue_total = sum(q["total_revenue"] for q in all_report)
        tokyo_revenue_total = sum(q["total_revenue"] for q in tokyo_report)
        assert tokyo_orders_total < all_orders_total
        assert tokyo_revenue_total < all_revenue_total

    def test_quarterly_category_filter_case_insensitive(self, client):
        """category=sensors (lowercase) filters correctly and case-insensitively."""
        report = client.get("/api/reports/quarterly?category=sensors").json()

        raw = client.get("/api/orders?category=sensors").json()
        assert len(raw) > 0
        for order in raw:
            assert order["category"].lower() == "sensors"

        expected = _expected_quarterly(raw)
        report_by_q = {q["quarter"]: q for q in report}
        assert set(report_by_q.keys()) == set(expected.keys())
        for quarter, exp in expected.items():
            assert report_by_q[quarter]["total_orders"] == exp["total_orders"]

    def test_quarterly_status_delivered_full_fulfillment(self, client):
        """status=Delivered -> every bucket is 100% delivered (fulfillment_rate 100)."""
        report = client.get("/api/reports/quarterly?status=Delivered").json()
        assert len(report) > 0

        raw = client.get("/api/orders?status=Delivered").json()
        for order in raw:
            assert order["status"] == "Delivered"

        for entry in report:
            assert entry["delivered_orders"] == entry["total_orders"]
            assert entry["fulfillment_rate"] == 100.0

    def test_quarterly_month_direct_returns_single_quarter(self, client):
        """month=2025-01 -> only the Q1-2025 quarter is returned."""
        report = client.get("/api/reports/quarterly?month=2025-01").json()
        assert [entry["quarter"] for entry in report] == ["Q1-2025"]

    def test_quarterly_month_quarter_returns_single_quarter(self, client):
        """month=Q1-2025 -> only the Q1-2025 quarter is returned."""
        report = client.get("/api/reports/quarterly?month=Q1-2025").json()
        assert [entry["quarter"] for entry in report] == ["Q1-2025"]

    def test_quarterly_nonexistent_warehouse_returns_empty_list(self, client):
        """A filter matching nothing returns [] (not an error)."""
        response = client.get("/api/reports/quarterly?warehouse=Nonexistent")
        assert response.status_code == 200
        assert response.json() == []


class TestMonthlyTrendsReport:
    """Test suite for GET /api/reports/monthly-trends filtering."""

    def test_monthly_no_filters_returns_full_aggregation(self, client):
        """No filters -> list of month dicts with the expected keys, sorted."""
        response = client.get("/api/reports/monthly-trends")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        for entry in data:
            assert isinstance(entry, dict)
            assert MONTHLY_KEYS.issubset(entry.keys()), (
                f"Missing keys: {MONTHLY_KEYS - set(entry.keys())}"
            )
            assert isinstance(entry["month"], str)
            assert isinstance(entry["order_count"], int)
            assert isinstance(entry["revenue"], (int, float))

        months = [entry["month"] for entry in data]
        assert months == sorted(months)

    def test_monthly_matches_raw_orders_aggregation(self, client):
        """Unfiltered monthly numbers match an aggregation of GET /api/orders."""
        report = {m["month"]: m for m in client.get("/api/reports/monthly-trends").json()}
        raw_orders = client.get("/api/orders").json()
        expected = _expected_monthly(raw_orders)

        assert set(report.keys()) == set(expected.keys())
        for month, exp in expected.items():
            got = report[month]
            assert got["order_count"] == exp["order_count"]
            assert abs(got["revenue"] - exp["revenue"]) < 0.01

    def test_monthly_warehouse_filter_is_strict_subset(self, client):
        """warehouse=Tokyo -> only Tokyo orders contribute and the total order count
        drops below the unfiltered total."""
        all_report = client.get("/api/reports/monthly-trends").json()
        tokyo_report = client.get("/api/reports/monthly-trends?warehouse=Tokyo").json()

        tokyo_orders = client.get("/api/orders?warehouse=Tokyo").json()
        assert len(tokyo_orders) > 0
        for order in tokyo_orders:
            assert order["warehouse"] == "Tokyo"

        expected = _expected_monthly(tokyo_orders)
        report = {m["month"]: m for m in tokyo_report}
        assert set(report.keys()) == set(expected.keys())
        for month, exp in expected.items():
            assert report[month]["order_count"] == exp["order_count"]
            assert abs(report[month]["revenue"] - exp["revenue"]) < 0.01

        all_count = sum(m["order_count"] for m in all_report)
        tokyo_count = sum(m["order_count"] for m in tokyo_report)
        assert tokyo_count < all_count

    def test_monthly_category_filter_case_insensitive(self, client):
        """category=sensors (lowercase) filters correctly and case-insensitively."""
        report = client.get("/api/reports/monthly-trends?category=sensors").json()

        raw = client.get("/api/orders?category=sensors").json()
        assert len(raw) > 0
        for order in raw:
            assert order["category"].lower() == "sensors"

        expected = _expected_monthly(raw)
        report_by_month = {m["month"]: m for m in report}
        assert set(report_by_month.keys()) == set(expected.keys())
        for month, exp in expected.items():
            assert report_by_month[month]["order_count"] == exp["order_count"]

    def test_monthly_status_delivered_full_fulfillment(self, client):
        """status=Delivered -> every bucket is entirely delivered orders."""
        report = client.get("/api/reports/monthly-trends?status=Delivered").json()
        assert len(report) > 0

        raw = client.get("/api/orders?status=Delivered").json()
        for order in raw:
            assert order["status"] == "Delivered"

        for entry in report:
            assert entry["delivered_count"] == entry["order_count"]

    def test_monthly_month_direct_returns_single_month(self, client):
        """month=2025-01 -> only the 2025-01 bucket is returned."""
        report = client.get("/api/reports/monthly-trends?month=2025-01").json()
        assert [entry["month"] for entry in report] == ["2025-01"]

    def test_monthly_month_quarter_returns_quarter_months(self, client):
        """month=Q1-2025 -> only the three Q1 month buckets are returned."""
        report = client.get("/api/reports/monthly-trends?month=Q1-2025").json()
        assert [entry["month"] for entry in report] == ["2025-01", "2025-02", "2025-03"]

    def test_monthly_nonexistent_warehouse_returns_empty_list(self, client):
        """A filter matching nothing returns [] (not an error)."""
        response = client.get("/api/reports/monthly-trends?warehouse=Nonexistent")
        assert response.status_code == 200
        assert response.json() == []

    def test_monthly_month_param_not_shadowed_by_loop_variable(self, client):
        """Regression guard: month=2025-03 returns ONLY the 2025-03 bucket.

        Proves the `month` query-param is honored end-to-end and is not clobbered
        by the per-order accumulator inside the aggregation loop."""
        response = client.get("/api/reports/monthly-trends?month=2025-03")
        assert response.status_code == 200

        report = response.json()
        assert [entry["month"] for entry in report] == ["2025-03"]

        # The single bucket's count matches the raw filtered orders for 2025-03.
        raw = client.get("/api/orders?month=2025-03").json()
        assert len(raw) > 0
        assert report[0]["order_count"] == len(raw)
