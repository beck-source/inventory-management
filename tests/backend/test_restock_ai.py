"""
Tests for AI restocking recommendation endpoints.

The model call (restock_ai.call_model) is always stubbed: these tests never
hit the network or spend API credits.
"""
from datetime import datetime, timedelta

import anthropic
import pytest

import main
import restock_ai
from restock_ai import AIRestockItem, AIRestockPlan


@pytest.fixture(autouse=True)
def clear_restock_orders():
    """Restock orders are stored in module-level memory; reset between tests."""
    main.restock_orders.clear()
    yield
    main.restock_orders.clear()


@pytest.fixture
def metrics():
    return restock_ai.build_sku_metrics(main.inventory_items, main.orders)


def _stub_plan(monkeypatch, items, summary="Two SKUs need attention."):
    plan = AIRestockPlan(summary=summary, items=[AIRestockItem(**i) for i in items])
    calls = []

    def fake_call_model(metrics, budget):
        calls.append((metrics, budget))
        return plan

    monkeypatch.setattr(restock_ai, "call_model", fake_call_model)
    return calls


AI_ENV_VARS = ("ANTHROPIC_API_KEY", "ANTHROPIC_AWS_API_KEY", "AWS_REGION",
               "AWS_DEFAULT_REGION", "ANTHROPIC_AWS_WORKSPACE_ID")


def _inventory(sku):
    return next(i for i in main.inventory_items if i["sku"] == sku)


class TestSkuMetrics:
    """Test suite for metric computation from stock and order history."""

    def test_one_row_per_inventory_sku_sorted(self, metrics):
        """Test every inventory SKU appears once, sorted for a stable prompt."""
        skus = [m["sku"] for m in metrics]
        assert skus == sorted(i["sku"] for i in main.inventory_items)

    def test_velocity_matches_order_history(self, metrics):
        """Test 90-day units and velocity are computed from the newest order date."""
        reference = max(datetime.fromisoformat(o["order_date"]) for o in main.orders)
        start = reference - timedelta(days=restock_ai.WINDOW_DAYS)
        row = metrics[0]

        expected_units = sum(
            line["quantity"]
            for o in main.orders
            if datetime.fromisoformat(o["order_date"]) > start
            for line in o["items"]
            if line["sku"] == row["sku"]
        )
        assert row["units_last_90d"] == expected_units
        assert abs(row["daily_velocity"] - expected_units / restock_ai.WINDOW_DAYS) < 0.01

    def test_days_of_cover(self, metrics):
        """Test days of cover is stock divided by velocity, or None without sales."""
        for row in metrics:
            if row["daily_velocity"] > 0:
                expected = row["quantity_on_hand"] / row["daily_velocity"]
                assert abs(row["days_of_cover"] - expected) < 0.1
            else:
                assert row["days_of_cover"] is None

    def test_no_orders_gives_zero_velocity(self):
        """Test SKUs with no order history get zero velocity and no cover estimate."""
        rows = restock_ai.build_sku_metrics(main.inventory_items[:1], [])
        assert rows[0]["daily_velocity"] == 0
        assert rows[0]["days_of_cover"] is None


class TestValidatePlan:
    """Test suite for server-side validation of model output."""

    def test_unknown_and_duplicate_skus_dropped(self, metrics):
        """Test hallucinated and repeated SKUs never reach the response."""
        sku = metrics[0]["sku"]
        plan = AIRestockPlan(summary="s", items=[
            AIRestockItem(sku=sku, quantity=10, priority="high", reason="r"),
            AIRestockItem(sku="FAKE-999", quantity=10, priority="high", reason="r"),
            AIRestockItem(sku=sku, quantity=99, priority="low", reason="dup"),
        ])
        lines = restock_ai.validate_plan(plan, metrics, None)
        assert [l["sku"] for l in lines] == [sku]
        assert lines[0]["quantity"] == 10

    def test_prices_come_from_server_data(self, metrics):
        """Test unit cost and line totals use inventory prices."""
        row = metrics[0]
        plan = AIRestockPlan(summary="s", items=[
            AIRestockItem(sku=row["sku"], quantity=4, priority="medium", reason="r"),
        ])
        line = restock_ai.validate_plan(plan, metrics, None)[0]
        assert line["unit_cost"] == row["unit_cost"]
        assert abs(line["line_total"] - 4 * row["unit_cost"]) < 0.01

    def test_quantity_clamped(self, metrics):
        """Test absurd or non-positive quantities are bounded."""
        row = metrics[0]
        plan = AIRestockPlan(summary="s", items=[
            AIRestockItem(sku=row["sku"], quantity=10_000_000, priority="high", reason="r"),
            AIRestockItem(sku=metrics[1]["sku"], quantity=-5, priority="high", reason="r"),
        ])
        big, small = restock_ai.validate_plan(plan, metrics, None)
        assert big["quantity"] < 10_000_000
        assert big["quantity"] >= row["reorder_point"] * 3
        assert small["quantity"] == 1

    def test_sorted_by_priority(self, metrics):
        """Test lines are ordered high, medium, low."""
        plan = AIRestockPlan(summary="s", items=[
            AIRestockItem(sku=metrics[0]["sku"], quantity=1, priority="low", reason="r"),
            AIRestockItem(sku=metrics[1]["sku"], quantity=1, priority="high", reason="r"),
            AIRestockItem(sku=metrics[2]["sku"], quantity=1, priority="medium", reason="r"),
        ])
        priorities = [l["priority"] for l in restock_ai.validate_plan(plan, metrics, None)]
        assert priorities == ["high", "medium", "low"]

    def test_budget_drops_low_priority_first(self, metrics):
        """Test the budget is re-enforced server-side, keeping high priority lines."""
        a, b = metrics[0], metrics[1]
        plan = AIRestockPlan(summary="s", items=[
            AIRestockItem(sku=b["sku"], quantity=1, priority="low", reason="r"),
            AIRestockItem(sku=a["sku"], quantity=1, priority="high", reason="r"),
        ])
        budget = a["unit_cost"]  # room for exactly the high-priority line
        lines = restock_ai.validate_plan(plan, metrics, budget)
        assert [l["sku"] for l in lines] == [a["sku"]]


class TestAIRecommendationsEndpoint:
    """Test suite for POST /api/restock/ai-recommendations."""

    def test_returns_validated_plan(self, client, monkeypatch, metrics):
        """Test the happy path response structure."""
        sku = metrics[0]["sku"]
        calls = _stub_plan(monkeypatch, [
            {"sku": sku, "quantity": 5, "priority": "high", "reason": "Below reorder point."},
            {"sku": "FAKE-1", "quantity": 5, "priority": "high", "reason": "x"},
        ])
        response = client.post("/api/restock/ai-recommendations", json={"budget": 100000})
        assert response.status_code == 200

        data = response.json()
        assert data["summary"] == "Two SKUs need attention."
        assert data["model"] == restock_ai.MODEL
        assert data["budget"] == 100000
        assert [i["sku"] for i in data["items"]] == [sku]
        item = data["items"][0]
        for field in ("name", "quantity_on_hand", "reorder_point", "daily_velocity",
                      "days_of_cover", "quantity", "unit_cost", "line_total", "priority", "reason"):
            assert field in item
        assert abs(data["total_cost"] - item["line_total"]) < 0.01
        assert calls[0][1] == 100000

    def test_budget_optional(self, client, monkeypatch):
        """Test the endpoint works without a budget."""
        calls = _stub_plan(monkeypatch, [])
        response = client.post("/api/restock/ai-recommendations", json={})
        assert response.status_code == 200
        assert response.json()["items"] == []
        assert calls[0][1] is None

    def test_negative_budget_rejected(self, client, monkeypatch):
        """Test a negative budget fails validation before any model call."""
        calls = _stub_plan(monkeypatch, [])
        response = client.post("/api/restock/ai-recommendations", json={"budget": -1})
        assert response.status_code == 422
        assert calls == []

    def test_missing_api_key_returns_503(self, client, monkeypatch):
        """Test a clear 503 when no key is configured (real call_model, no network)."""
        for var in AI_ENV_VARS:
            monkeypatch.delenv(var, raising=False)
        response = client.post("/api/restock/ai-recommendations", json={})
        assert response.status_code == 503
        detail = response.json()["detail"]
        assert "ANTHROPIC_AWS_API_KEY" in detail and "ANTHROPIC_API_KEY" in detail

    def test_aws_key_without_region_and_workspace_returns_503(self, client, monkeypatch):
        """Test the 503 names the Claude Platform on AWS settings that are missing."""
        for var in AI_ENV_VARS:
            monkeypatch.delenv(var, raising=False)
        monkeypatch.setenv("ANTHROPIC_AWS_API_KEY", "test-key")
        response = client.post("/api/restock/ai-recommendations", json={})
        assert response.status_code == 503
        detail = response.json()["detail"]
        assert "AWS_REGION" in detail and "ANTHROPIC_AWS_WORKSPACE_ID" in detail

    @pytest.mark.parametrize("status,detail", [(502, "declined"), (429, "rate limited"), (503, "rejected")])
    def test_upstream_errors_mapped(self, client, monkeypatch, status, detail):
        """Test model failures surface as the mapped HTTP status."""
        def failing(metrics, budget):
            raise restock_ai.AIUpstreamError(status, detail)

        monkeypatch.setattr(restock_ai, "call_model", failing)
        response = client.post("/api/restock/ai-recommendations", json={})
        assert response.status_code == status
        assert response.json()["detail"] == detail


class TestCallModelErrorHandling:
    """Test suite for SDK error translation inside call_model."""

    def _patch_client(self, monkeypatch, parse):
        class FakeMessages:
            def __init__(self):
                self.parse = parse

        class FakeClient:
            messages = FakeMessages()

        monkeypatch.setattr(restock_ai, "_get_client", lambda: FakeClient())

    def test_refusal_raises_502(self, monkeypatch):
        """Test a refusal stop reason becomes a 502."""
        class Resp:
            stop_reason = "refusal"
            parsed_output = None

        self._patch_client(monkeypatch, lambda **kw: Resp())
        with pytest.raises(restock_ai.AIUpstreamError) as exc:
            restock_ai.call_model([], None)
        assert exc.value.status_code == 502

    def test_unparsed_output_raises_502(self, monkeypatch):
        """Test a response without parsed output becomes a 502."""
        class Resp:
            stop_reason = "max_tokens"
            parsed_output = None

        self._patch_client(monkeypatch, lambda **kw: Resp())
        with pytest.raises(restock_ai.AIUpstreamError) as exc:
            restock_ai.call_model([], None)
        assert exc.value.status_code == 502

    def test_connection_error_raises_502(self, monkeypatch):
        """Test network failures become a 502 without leaking SDK details."""
        def parse(**kw):
            raise anthropic.APIConnectionError(request=None)

        self._patch_client(monkeypatch, parse)
        with pytest.raises(restock_ai.AIUpstreamError) as exc:
            restock_ai.call_model([], None)
        assert exc.value.status_code == 502

    def test_request_uses_haiku_with_structured_output(self, monkeypatch):
        """Test the request targets Haiku 5.5 with the plan schema and no sampling params."""
        captured = {}

        class Resp:
            stop_reason = "end_turn"
            parsed_output = AIRestockPlan(summary="ok", items=[])

        def parse(**kw):
            captured.update(kw)
            return Resp()

        self._patch_client(monkeypatch, parse)
        assert restock_ai.call_model([], 50.0).summary == "ok"
        assert captured["model"] == "claude-haiku-5-5"
        assert captured["output_format"] is AIRestockPlan
        assert "temperature" not in captured
        assert "Budget: 50.00" in captured["messages"][0]["content"]


class TestClientSelection:
    """Test suite for choosing the first-party vs Claude Platform on AWS client."""

    @pytest.fixture(autouse=True)
    def clean_env(self, monkeypatch):
        for var in AI_ENV_VARS:
            monkeypatch.delenv(var, raising=False)

    def test_aws_client_when_aws_key_configured(self, monkeypatch):
        """Test AWS credentials select AnthropicAWS with the configured region."""
        monkeypatch.setenv("ANTHROPIC_AWS_API_KEY", "test-key")
        monkeypatch.setenv("AWS_REGION", "us-west-2")
        monkeypatch.setenv("ANTHROPIC_AWS_WORKSPACE_ID", "wrkspc_test")
        client = restock_ai._get_client()
        assert isinstance(client, anthropic.AnthropicAWS)
        assert "us-west-2" in str(client.base_url)

    def test_aws_key_takes_precedence(self, monkeypatch):
        """Test an AWS key wins even if a first-party key is also present."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "first-party")
        monkeypatch.setenv("ANTHROPIC_AWS_API_KEY", "test-key")
        monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
        monkeypatch.setenv("ANTHROPIC_AWS_WORKSPACE_ID", "wrkspc_test")
        assert isinstance(restock_ai._get_client(), anthropic.AnthropicAWS)

    def test_first_party_client(self, monkeypatch):
        """Test a first-party key alone selects the standard client."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "first-party")
        client = restock_ai._get_client()
        assert type(client) is anthropic.Anthropic


class TestRestockOrderInventorySku:
    """Test suite for ordering AI-recommended (inventory-only) SKUs."""

    def test_inventory_only_sku_orderable(self, client):
        """Test SKUs absent from forecasts use inventory price and default lead time."""
        forecast_skus = {f["item_sku"] for f in main.demand_forecasts}
        inv = next(i for i in main.inventory_items if i["sku"] not in forecast_skus)

        response = client.post("/api/restock-orders", json={
            "budget": inv["unit_cost"] * 3,
            "items": [{"sku": inv["sku"], "quantity": 3}],
        })
        assert response.status_code == 201

        order = response.json()
        line = order["items"][0]
        assert line["unit_cost"] == inv["unit_cost"]
        assert line["lead_time_days"] == main.DEFAULT_LEAD_TIME_DAYS
        assert order["lead_time_days"] == main.DEFAULT_LEAD_TIME_DAYS
