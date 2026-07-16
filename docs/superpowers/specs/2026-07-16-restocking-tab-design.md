# Restocking Tab — Design Spec

**Date:** 2026-07-16
**Branch:** `new_features`
**Status:** Approved (Option A — fix bad decisions as we go)

## Goal

Add a "Restocking" tab that lets the user set an available budget with a slider,
recommends demand-forecast items to restock ranked by ROI within that budget,
and submits a restocking order that then appears in a new "Submitted Restocking
Orders" section at the top of the Orders tab, showing delivery lead time.

## Decisions (from brainstorming)

| Question | Decision |
|----------|----------|
| Recommendation logic | **ROI-first** — rank by `forecasted_demand / unit_cost`, greedy fill within budget |
| Lead time | **Fixed by category** — backend-owned `CATEGORY_LEAD_TIMES` constant |
| Orders tab layout | **New section at top** — "Submitted Restocking Orders" above the main table |
| Approach | **Option A** — implement real backend endpoints (fixes the silent-404 bad decision) |
| Missing cost data | **Add `unit_cost` to forecasts** — enrich `demand_forecasts.json` |

## Data enrichment

The demand forecast had no `unit_cost` and no `category`, and 8 of its 9 SKUs
don't exist in inventory (can't join). We add both fields to each of the 9 items
in `server/data/demand_forecasts.json`:

| SKU | Category | unit_cost |
|-----|----------|-----------|
| WDG-001 | Mechanical Components | 12.50 |
| BRG-102 | Mechanical Components | 45.00 |
| GSK-203 | Mechanical Components | 8.75 |
| MTR-304 | Actuators | 320.00 |
| FLT-405 | Mechanical Components | 15.25 |
| VLV-506 | Actuators | 78.00 |
| PSU-501 | Power Supplies | 42.00 |
| SNR-420 | Sensors | 28.50 |
| CTL-330 | Controllers | 95.00 |

## Lead times (`CATEGORY_LEAD_TIMES`, days)

Circuit Boards 14 · Sensors 7 · Controllers 10 · Power Supplies 12 ·
Actuators 21 · Mechanical Components 18 · **default 14** (unknown category)

## Recommendation algorithm (frontend, reactive to slider)

Computed property, recalculated on every budget change:

1. Map each forecast item to `{ sku, name, category, unit_cost, forecasted_demand, roi }`
   where `roi = forecasted_demand / unit_cost`.
2. Sort by `roi` descending.
3. Greedy fill: walk the sorted list, for each item take
   `qty = min(forecasted_demand, floor(remaining_budget / unit_cost))`.
   If `qty === 0`, stop. Subtract `qty * unit_cost` from remaining budget.
4. Result: an ordered list of recommended line items + running total spend.

Lives on the frontend so the slider gives instant feedback with no API round-trip.

## Backend

### New model
```
RestockingOrder:
  id: str                # "RO-0001"
  created_at: str        # ISO datetime
  items: List[dict]      # {sku, name, category, quantity, unit_cost, line_total}
  total_cost: float
  budget: float
  warehouse: Optional[str]
  lead_time_days: int    # max lead time across item categories (slowest item gates the order)
  expected_delivery: str # created date + lead_time_days
  status: str            # "Submitted"

CreateRestockingOrderRequest:
  items: List[dict]      # {sku, name, category, quantity, unit_cost}
  budget: float
  warehouse: Optional[str]
```

### New endpoints (fixes the silent-404 bad decision)
- `POST /api/restocking-orders` — validate, compute line totals, total cost,
  `lead_time_days` (max across item categories), `expected_delivery`, assign id,
  append to in-memory `restocking_orders` list, return the created order.
- `GET /api/restocking-orders` — return the list (optional `warehouse` filter).

In-memory `restocking_orders = []` in `main.py` (runtime state; no disk
persistence, consistent with the demo's in-memory approach — documented with a comment).

## Frontend

### api.js (2 functions)
- `postRestockingOrder(payload)` → `POST /api/restocking-orders`
- `getRestockingOrders(filters)` → `GET /api/restocking-orders`

### Restocking.vue (new view, Composition API — consistent with all views except Reports)
- Budget slider (range input) bound to a `budget` ref, plus a numeric readout.
- `recommendations` computed property (algorithm above).
- Table of recommended items: name, category, ROI, unit cost, recommended qty, line total.
- Running total spend vs budget, remaining budget.
- "Place Order" button → `postRestockingOrder`, success toast, disabled when no recommendations.
- Uses `useFilters` for `warehouse` (location) to stamp the order; follows the
  standard `loadData` + try/catch/finally + loading/error-state pattern.

### Orders.vue
- Add a "Submitted Restocking Orders" section above the main table.
- Fetch via `getRestockingOrders()` in the existing `loadData`.
- Columns: order id, submitted date, items (count / summary), total cost,
  lead time (days), expected delivery, status.
- Empty state when none submitted.

### Routing / nav
- Register `/restocking` route in `main.js`.
- Add nav link in `App.vue` (matches existing nav styling).

## Testing

- `tests/backend/test_restocking.py` (backend-api-test skill): POST creates order,
  computed fields correct (line totals, total cost, lead time = max category, expected
  delivery), GET returns submitted orders, warehouse filter works, validation errors.
- Run full backend suite (should stay green).
- Manual browser verification end-to-end via the running dev servers.

## Conventions honored

- All `.vue` create/modify delegated to the `vue-expert` subagent (CLAUDE.md mandate).
- `code-reviewer` after significant code.
- Composition API throughout (does NOT repeat the Reports.vue outlier mistake).
- Real backend endpoints (does NOT repeat the silent-404 mistake).
- Non-obvious logic documented with comments.
