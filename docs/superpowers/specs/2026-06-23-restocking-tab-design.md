# Restocking Tab — Design Spec

**Date:** 2026-06-23  
**Status:** Approved

---

## Overview

Add a new "Restocking" tab to the inventory management app. It lets a user set a budget via a slider, see which demand-forecast items can be restocked within that budget (prioritized by demand gap), and place a restocking order. Submitted orders appear in a new section at the top of the existing Orders tab.

---

## Data Layer

### Problem
`demand_forecasts.json` has no `unit_cost` field, but budget math requires a cost per item.

### Fix
Add a `unit_cost: float` field to every item in `server/data/demand_forecasts.json`. Values should be realistic for factory components. Update the `DemandForecast` Pydantic model in `server/main.py` to include `unit_cost: float`. The existing `GET /api/demand` endpoint will return it automatically — no endpoint changes needed for demand.

---

## Backend

### New in-memory store
Add a module-level list in `main.py`:
```python
restocking_orders: List[dict] = []
```

### New Pydantic models

```python
class RestockingOrderItem(BaseModel):
    sku: str
    name: str
    quantity: int
    unit_cost: float

class RestockingOrderCreate(BaseModel):
    items: List[RestockingOrderItem]

class RestockingOrder(BaseModel):
    id: str
    order_number: str
    items: List[RestockingOrderItem]
    total_cost: float
    status: str          # always "Submitted"
    submitted_date: str  # ISO 8601
    expected_delivery: str  # submitted_date + 14 days, ISO 8601
```

### New endpoints

**`POST /api/restocking-orders`**  
Body: `RestockingOrderCreate`  
- Generates an `id` (uuid4) and `order_number` (e.g. `RST-2026-0001`, auto-incrementing)  
- Sets `submitted_date` to current UTC datetime  
- Sets `expected_delivery` to `submitted_date + 14 days`  
- Computes `total_cost` as sum of `item.quantity * item.unit_cost`  
- Appends to in-memory `restocking_orders` list  
- Returns the full `RestockingOrder` object (HTTP 201)

**`GET /api/restocking-orders`**  
Returns `List[RestockingOrder]` — all submitted restocking orders, newest first.

---

## Frontend

### New file: `client/src/views/Restocking.vue`

**Layout (top to bottom):**

1. **Page header** — title "Restocking Planner" and a one-line description.

2. **Budget slider card**  
   - Range: $0 – $500,000, step $1,000  
   - Default: $100,000  
   - Displays formatted current value (e.g. `$100,000`)  
   - Reactive: recommendation table updates as slider moves (no button needed)

3. **Budget summary bar** (single row of 3 stat cards)  
   - Allocated budget (sum of all recommended items' costs)  
   - Items recommended (count)  
   - Remaining budget

4. **Recommended Items table**  
   Columns: SKU | Item Name | Demand Gap | Unit Cost | Restock Qty | Line Total  
   - Shows items that fit within budget, sorted by demand gap descending  
   - Each row has a remove button (X) to exclude an item from the order  
   - If no items fit, shows "No items can be restocked within this budget."

5. **Over Budget items** (collapsible section below the table)  
   - Items that would fit if budget were higher  
   - Read-only, no actions

6. **Place Order button**  
   - Disabled if no items are recommended  
   - On click: shows a simple confirmation (inline text or modal) → on confirm, calls `api.submitRestockingOrder(items)` → on success, shows a success message with the order number and expected delivery date  
   - On success, clears the recommendation (slider stays)

**Recommendation algorithm (computed property):**

```
1. Start with all demand forecasts where forecasted_demand > current_demand
2. Sort by (forecasted_demand - current_demand) descending
3. Walk the list; for each item:
     quantity = forecasted_demand - current_demand
     cost = quantity * unit_cost
     if running_total + cost <= budget → include it
     else → put it in "over budget" list
4. Return included list and over-budget list
```

Excluded items (user clicked X) are tracked in a local `excludedSkus` ref and filtered out before the algorithm runs.

### Modified file: `client/src/views/Orders.vue`

- On mount, also call `api.getRestockingOrders()`
- If the result is non-empty, render a "Submitted Restocking Orders" card **above** the stat-card row and the main orders table
- Card shows a table with columns: Order # | Items | Total Cost | Submitted | Expected Delivery | Status
- Status always shows a "Submitted" badge (use a distinct purple/indigo color to distinguish from existing statuses)
- If no restocking orders exist, the section is hidden entirely (no empty state shown)

### Modified file: `client/src/api.js`

Add two methods:

```js
async submitRestockingOrder(items) {
  const response = await axios.post(`${API_BASE_URL}/restocking-orders`, { items })
  return response.data
},

async getRestockingOrders() {
  const response = await axios.get(`${API_BASE_URL}/restocking-orders`)
  return response.data
}
```

### Modified file: `client/src/App.vue`

Add nav link between Demand Forecast and Reports:
```html
<router-link to="/restocking">Restocking</router-link>
```

### Modified file: `client/src/main.js` (or router file)

Add route:
```js
{ path: '/restocking', component: () => import('./views/Restocking.vue') }
```

---

## Error Handling

- If `/api/demand` fails on load, show an error message and disable the slider/button
- If `POST /api/restocking-orders` fails, show an inline error below the Place Order button; do not clear the recommendation
- If `GET /api/restocking-orders` fails in Orders.vue, silently skip the section (don't break the main orders table)

---

## What's out of scope

- Restocking orders do not persist across server restarts (consistent with all other data)
- Global filters (warehouse, category, period) do not apply to the Restocking tab
- No edit/cancel of submitted restocking orders
- No i18n keys added (use English strings directly, consistent with how "Reports" tab was added)

---

## Testing

- Backend: add `tests/backend/test_restocking.py` covering POST (happy path, empty items), GET (returns list, newest first), and total_cost calculation
- Manual browser test: move slider, verify recommendation updates; place order; verify it appears in Orders tab

---

## File Changelist

| File | Change |
|------|--------|
| `server/data/demand_forecasts.json` | Add `unit_cost` to every item |
| `server/main.py` | Add `unit_cost` to `DemandForecast` model; add `RestockingOrder*` models; add 2 endpoints |
| `client/src/views/Restocking.vue` | New file |
| `client/src/views/Orders.vue` | Add restocking orders section |
| `client/src/api.js` | Add `submitRestockingOrder`, `getRestockingOrders` |
| `client/src/App.vue` | Add nav link |
| `client/src/main.js` | Add route |
| `tests/backend/test_restocking.py` | New test file |
