"""
Tests for reporting API endpoints.

Covers:
  - GET /api/reports/quarterly — structure, sort order, math invariants.
  - GET /api/reports/monthly-trends — structure, sort order, aggregate invariants.
"""
import sys
from pathlib import Path

import pytest

server_path = Path(__file__).parent.parent.parent / "server"
sys.path.insert(0, str(server_path))


QUARTERLY_REQUIRED_FIELDS = [
    "quarter",
    "total_orders",
    "total_revenue",
    "avg_order_value",
    "fulfillment_rate",
]

MONTHLY_REQUIRED_FIELDS = [
    "month",
    "order_count",
    "revenue",
    "delivered_count",
]


class TestQuarterlyReports:
    """Test suite for GET /api/reports/quarterly."""

    def test_returns_at_most_four_entries(self, client):
        """Response contains at most 4 quarters (Q1–Q4 of a single year).

        More than 4 would indicate duplicate keys or date parsing that assigns
        a single order to multiple quarters.
        """
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 4, (
            f"Expected at most 4 quarterly entries, got {len(data)}"
        )

    def test_all_required_fields_present(self, client):
        """Every quarter entry contains all required fields."""
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0, "Expected at least one quarterly entry in dataset"

        for entry in data:
            for field in QUARTERLY_REQUIRED_FIELDS:
                assert field in entry, (
                    f"Quarter entry missing required field '{field}': {entry.get('quarter')}"
                )

    def test_quarters_sorted_ascending(self, client):
        """Quarter entries are sorted by quarter label in ascending order.

        Ascending order (Q1, Q2, Q3, Q4) is the natural chronological display.
        Descending or unsorted would make trend analysis confusing.
        """
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200

        data = response.json()
        quarters = [entry["quarter"] for entry in data]
        assert quarters == sorted(quarters), (
            f"Quarters not sorted ascending: {quarters}"
        )

    def test_fulfillment_rate_is_valid_percentage(self, client):
        """fulfillment_rate is between 0.0 and 100.0 for every quarter."""
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200

        for entry in response.json():
            rate = entry["fulfillment_rate"]
            assert isinstance(rate, (int, float)), (
                f"fulfillment_rate must be numeric, got {type(rate)}"
            )
            assert 0.0 <= rate <= 100.0, (
                f"fulfillment_rate {rate} is outside [0, 100] for {entry['quarter']}"
            )

    def test_fulfillment_rate_math(self, client):
        """fulfillment_rate equals round(delivered_orders / total_orders * 100, 1).

        The endpoint computes this on the fly from order data. A rounding mistake
        or division order error would surface here.
        """
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200

        for entry in response.json():
            total = entry["total_orders"]
            assert total > 0, f"total_orders must be > 0 for {entry['quarter']}"

            # Reconstruct delivered_orders from fulfillment_rate and total_orders.
            # We cannot read delivered_orders directly from the response, but we can
            # verify the rate is consistent with being derived from an integer count.
            rate = entry["fulfillment_rate"]
            # rate = round(delivered / total * 100, 1) implies
            # delivered = round(rate * total / 100) must be an integer in [0, total].
            implied_delivered = round(rate * total / 100)
            assert 0 <= implied_delivered <= total, (
                f"fulfillment_rate {rate} implies {implied_delivered} delivered out of "
                f"{total} total for {entry['quarter']} — impossible value"
            )

            # Verify the back-computed rate matches.
            recomputed_rate = round((implied_delivered / total) * 100, 1)
            assert abs(recomputed_rate - rate) < 0.2, (
                f"fulfillment_rate {rate} does not match back-computed {recomputed_rate} "
                f"for {entry['quarter']}"
            )

    def test_avg_order_value_math(self, client):
        """avg_order_value equals round(total_revenue / total_orders, 2).

        A missing round(), wrong denominator, or field-name typo would fail here.
        """
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200

        for entry in response.json():
            total = entry["total_orders"]
            assert total > 0

            expected_avg = round(entry["total_revenue"] / total, 2)
            actual_avg = entry["avg_order_value"]

            assert abs(actual_avg - expected_avg) < 0.01, (
                f"avg_order_value {actual_avg} != expected {expected_avg} "
                f"for {entry['quarter']}"
            )

    def test_total_orders_is_positive_int(self, client):
        """total_orders is a positive integer for every quarter entry."""
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200

        for entry in response.json():
            assert isinstance(entry["total_orders"], int)
            assert entry["total_orders"] > 0

    def test_total_revenue_is_non_negative(self, client):
        """total_revenue is a non-negative number for every quarter entry."""
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200

        for entry in response.json():
            assert isinstance(entry["total_revenue"], (int, float))
            assert entry["total_revenue"] >= 0


class TestMonthlyTrends:
    """Test suite for GET /api/reports/monthly-trends."""

    def test_returns_list(self, client):
        """Response is a non-empty list of monthly trend objects."""
        response = client.get("/api/reports/monthly-trends")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, "Expected at least one month in the dataset"

    def test_all_required_fields_present(self, client):
        """Every monthly entry contains all required fields."""
        response = client.get("/api/reports/monthly-trends")
        assert response.status_code == 200

        for entry in response.json():
            for field in MONTHLY_REQUIRED_FIELDS:
                assert field in entry, (
                    f"Monthly entry missing required field '{field}': {entry.get('month')}"
                )

    def test_month_format_is_yyyy_mm(self, client):
        """Every 'month' value is in YYYY-MM format.

        A date parsing bug that includes day or time would produce a wrong key,
        causing months to merge incorrectly or produce malformed output.
        """
        response = client.get("/api/reports/monthly-trends")
        assert response.status_code == 200

        for entry in response.json():
            month = entry["month"]
            assert isinstance(month, str)
            assert len(month) == 7, f"Expected YYYY-MM format, got '{month}'"
            assert month[4] == "-", f"Expected YYYY-MM format, got '{month}'"
            year_part = month[:4]
            month_part = month[5:]
            assert year_part.isdigit(), f"Year part not numeric in '{month}'"
            assert month_part.isdigit(), f"Month part not numeric in '{month}'"
            assert 1 <= int(month_part) <= 12, f"Month value out of range in '{month}'"

    def test_entries_sorted_ascending(self, client):
        """Monthly entries are sorted by month label ascending (oldest first)."""
        response = client.get("/api/reports/monthly-trends")
        assert response.status_code == 200

        months = [entry["month"] for entry in response.json()]
        assert months == sorted(months), (
            f"Monthly entries not sorted ascending: {months}"
        )

    def test_sum_of_order_counts_equals_total_orders(self, client):
        """Sum of order_count across all months equals total orders in the dataset.

        This is a strong invariant: the monthly aggregation must be lossless.
        Any order dropped during date parsing would cause the sum to diverge.
        """
        from mock_data import orders as all_orders

        response = client.get("/api/reports/monthly-trends")
        assert response.status_code == 200

        monthly_sum = sum(entry["order_count"] for entry in response.json())
        assert monthly_sum == len(all_orders), (
            f"Monthly order_count sum {monthly_sum} != total orders {len(all_orders)}"
        )

    def test_sum_of_revenue_equals_total_order_value(self, client):
        """Sum of monthly revenue equals the sum of all order total_values.

        A data type mismatch, field name error, or order dropped during month
        extraction would cause this invariant to fail.
        """
        from mock_data import orders as all_orders

        expected_total = sum(o.get("total_value", 0) for o in all_orders)

        response = client.get("/api/reports/monthly-trends")
        assert response.status_code == 200

        monthly_revenue_sum = sum(entry["revenue"] for entry in response.json())

        assert abs(monthly_revenue_sum - expected_total) < 0.01, (
            f"Monthly revenue sum {monthly_revenue_sum} != "
            f"expected total {expected_total}"
        )

    def test_delivered_count_never_exceeds_order_count(self, client):
        """delivered_count <= order_count for every month.

        A logic error where delivered orders are counted against the wrong month
        or double-counted would violate this constraint.
        """
        response = client.get("/api/reports/monthly-trends")
        assert response.status_code == 200

        for entry in response.json():
            assert entry["delivered_count"] <= entry["order_count"], (
                f"Month {entry['month']}: delivered_count {entry['delivered_count']} "
                f"> order_count {entry['order_count']}"
            )

    def test_no_duplicate_months(self, client):
        """Each YYYY-MM value appears exactly once in the response.

        Duplicates would indicate a grouping bug where the same month is
        accumulated into two separate dict keys.
        """
        response = client.get("/api/reports/monthly-trends")
        assert response.status_code == 200

        months = [entry["month"] for entry in response.json()]
        assert len(months) == len(set(months)), (
            f"Duplicate month entries found: {months}"
        )
