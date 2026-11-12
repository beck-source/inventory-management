"""LLM-assisted restocking recommendations.

The server computes per-SKU stock and sales metrics; Claude ranks items,
proposes quantities and explains each choice; the server then re-validates
every number so the model can never invent SKUs or prices.
"""
import json
import math
import os
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Literal, Optional

import anthropic
from pydantic import BaseModel

MODEL = "claude-haiku-5-5"
WINDOW_DAYS = 90
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}

SYSTEM_PROMPT = """You are a restocking analyst for a factory warehouse. You help an operator decide what to reorder.

You receive one JSON row per inventory SKU with current stock and sales history:
- quantity_on_hand, reorder_point, unit_cost
- units_last_90d / units_prev_90d: units ordered by customers in the last 90 days and the 90 days before that
- avg_monthly_units, daily_velocity (units/day over the last 90 days)
- days_of_cover: how many days current stock lasts at daily_velocity (null when there were no recent sales)

Recommend only SKUs that need restocking: stock at or below reorder point, low days of cover, or rising demand that will exhaust stock soon. Skip SKUs with ample cover.
For each recommended SKU give:
- quantity: whole units, enough to cover roughly 60 days of demand plus bring stock back above the reorder point
- priority: high (stockout risk within ~2 weeks or already below reorder point), medium, or low
- reason: one or two plain sentences for the operator that cite the specific numbers you relied on

Use only SKUs present in the input. If a budget is given, keep the total cost (quantity x unit_cost) within it, favoring higher-priority items.
Also write a two- or three-sentence summary of the overall restocking situation."""


class AIRestockItem(BaseModel):
    sku: str
    quantity: int
    priority: Literal["high", "medium", "low"]
    reason: str


class AIRestockPlan(BaseModel):
    summary: str
    items: List[AIRestockItem]


class AINotConfiguredError(Exception):
    """Credentials are missing or incomplete, so the feature is disabled."""

    def __init__(self, detail: str = "AI recommendations are not configured: set ANTHROPIC_AWS_API_KEY "
                                     "(Claude Platform on AWS) or ANTHROPIC_API_KEY in .env and restart the server"):
        super().__init__(detail)
        self.detail = detail


class AIUpstreamError(Exception):
    """The model call failed; carries the HTTP status the API should return."""

    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def _parse_date(value: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def build_sku_metrics(inventory_items: list, orders: list) -> List[dict]:
    """One row per inventory SKU combining current stock with order history."""
    dated_orders = [(d, o) for o in orders if (d := _parse_date(o.get("order_date")))]
    if dated_orders:
        # Anchor windows on the newest order rather than today(): the mock data
        # ends in Dec 2025, so wall-clock windows would report zero recent sales.
        reference = max(d for d, _ in dated_orders)
        first = min(d for d, _ in dated_orders)
    else:
        reference = first = datetime.now()
    recent_start = reference - timedelta(days=WINDOW_DAYS)
    prev_start = recent_start - timedelta(days=WINDOW_DAYS)
    months_spanned = max(1, (reference.year - first.year) * 12 + reference.month - first.month + 1)

    total = defaultdict(int)
    recent = defaultdict(int)
    previous = defaultdict(int)
    for order_date, order in dated_orders:
        for line in order.get("items", []):
            sku, qty = line.get("sku"), line.get("quantity", 0)
            total[sku] += qty
            if order_date > recent_start:
                recent[sku] += qty
            elif order_date > prev_start:
                previous[sku] += qty

    rows = []
    for item in sorted(inventory_items, key=lambda i: i["sku"]):
        sku = item["sku"]
        daily_velocity = round(recent[sku] / WINDOW_DAYS, 2)
        rows.append({
            "sku": sku,
            "name": item["name"],
            "category": item["category"],
            "warehouse": item["warehouse"],
            "quantity_on_hand": item["quantity_on_hand"],
            "reorder_point": item["reorder_point"],
            "unit_cost": item["unit_cost"],
            "units_last_90d": recent[sku],
            "units_prev_90d": previous[sku],
            "avg_monthly_units": round(total[sku] / months_spanned, 1),
            "daily_velocity": daily_velocity,
            "days_of_cover": round(item["quantity_on_hand"] / daily_velocity, 1) if daily_velocity > 0 else None,
        })
    return rows


def _get_client():
    """Pick the client from whichever credentials are configured.

    Claude Platform on AWS keys only work against the AWS endpoint, so sending
    one to api.anthropic.com via Anthropic() fails with 401 - the AWS client
    must be chosen explicitly. Built per call so credentials added to the
    environment are picked up; construction is cheap next to the model call.
    """
    if os.environ.get("ANTHROPIC_AWS_API_KEY"):
        missing = [name for name, ok in (
            ("AWS_REGION", os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")),
            ("ANTHROPIC_AWS_WORKSPACE_ID", os.environ.get("ANTHROPIC_AWS_WORKSPACE_ID")),
        ) if not ok]
        if missing:
            raise AINotConfiguredError(
                f"AI recommendations are not configured: Claude Platform on AWS also needs {', '.join(missing)} in .env"
            )
        # Reads ANTHROPIC_AWS_API_KEY, AWS_REGION and ANTHROPIC_AWS_WORKSPACE_ID itself.
        return anthropic.AnthropicAWS(timeout=60.0, max_retries=2)
    if os.environ.get("ANTHROPIC_API_KEY"):
        return anthropic.Anthropic(timeout=60.0, max_retries=2)
    raise AINotConfiguredError()


def call_model(metrics: List[dict], budget: Optional[float]) -> AIRestockPlan:
    """Ask Claude for a restocking plan. Raises AINotConfiguredError / AIUpstreamError."""
    client = _get_client()
    payload = {"budget": budget, "skus": metrics}
    budget_note = f"Budget: {budget:.2f}." if budget is not None else "No budget limit was given."
    try:
        response = client.messages.parse(
            model=MODEL,
            # Thinking is on by default on Haiku 5.5 and counts toward max_tokens.
            max_tokens=16000,
            output_config={"effort": "medium"},
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                # sort_keys keeps the prompt byte-identical for identical data.
                "content": f"{budget_note}\n\nInventory and sales metrics:\n{json.dumps(payload, sort_keys=True)}",
            }],
            output_format=AIRestockPlan,
        )
    except anthropic.AuthenticationError:
        # Claude Platform on AWS short-term keys expire after at most 12 hours.
        raise AIUpstreamError(503, "AI recommendations are not available: the API key was rejected or has expired")
    except anthropic.PermissionDeniedError:
        # On Claude Platform on AWS a 403 usually means a wrong workspace ID or a missing IAM permission.
        raise AIUpstreamError(503, "AI recommendations are not available: access denied (check the workspace ID and permissions)")
    except anthropic.RateLimitError:
        raise AIUpstreamError(429, "AI service is rate limited; try again shortly")
    except anthropic.APIStatusError as e:
        raise AIUpstreamError(502, f"AI service error ({e.status_code})")
    except (anthropic.APIConnectionError, anthropic.APITimeoutError):
        raise AIUpstreamError(502, "Could not reach the AI service")

    # Haiku has no server-side refusal fallback, so a decline ends the request.
    if response.stop_reason == "refusal":
        raise AIUpstreamError(502, "The AI service declined to produce a recommendation")
    if response.parsed_output is None:
        raise AIUpstreamError(502, "The AI service returned an unusable response")
    return response.parsed_output


def _to_cents(amount: float) -> int:
    return round(amount * 100)


def validate_plan(plan: AIRestockPlan, metrics: List[dict], budget: Optional[float]) -> List[dict]:
    """Turn the model's plan into order lines using only server-side numbers."""
    by_sku = {m["sku"]: m for m in metrics}
    seen = set()
    lines = []
    for item in plan.items:
        metric = by_sku.get(item.sku)
        # Drop hallucinated SKUs and repeats (duplicates would also break UI keys).
        if metric is None or item.sku in seen:
            continue
        seen.add(item.sku)
        # Cap at whichever is larger: 3x the reorder point or ~6 months of sales,
        # so a bad model output can't produce an absurd order.
        cap = max(1, metric["reorder_point"] * 3, math.ceil(metric["daily_velocity"] * 180))
        quantity = min(max(item.quantity, 1), cap)
        lines.append({
            **{k: metric[k] for k in ("sku", "name", "quantity_on_hand", "reorder_point", "daily_velocity", "days_of_cover", "unit_cost")},
            "quantity": quantity,
            "line_total": round(quantity * metric["unit_cost"], 2),
            "priority": item.priority,
            "reason": item.reason,
        })

    # Stable sort: priority first, model's own ordering within a priority.
    lines.sort(key=lambda l: PRIORITY_RANK[l["priority"]])
    if budget is None:
        return lines

    # The model's arithmetic isn't trusted: re-apply the budget in integer cents,
    # keeping higher-priority lines and skipping any line that no longer fits.
    remaining = _to_cents(budget)
    kept = []
    for line in lines:
        cost = _to_cents(line["line_total"])
        if cost <= remaining:
            kept.append(line)
            remaining -= cost
    return kept
