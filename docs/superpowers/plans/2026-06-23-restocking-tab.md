# Restocking Tab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Restocking tab that lets users set a budget, see demand-driven restock recommendations, place an order, and view submitted orders in the Orders tab.

**Architecture:** Budget recommendations are computed client-side from demand forecast data (greedy allocation by demand gap). Submitted orders are stored in-memory on the backend and surfaced as a card above the existing orders table.

**Tech Stack:** Vue 3 Composition API (Options API style with `setup()`), FastAPI, Python `datetime`/`uuid` stdlib, Axios.

## Global Constraints

- All Vue components use `export default { setup() {} }` Options API style — no `<script setup>` syntax
- No i18n keys added — use English string literals (consistent with how "Reports" tab was added)
- In-memory only — restocking orders clear on server restart; this is intentional and consistent with all other data
- Backend: construct item dicts manually (avoid `.dict()` / `.model_dump()` for Pydantic version safety)
- All dates ISO 8601 (`datetime.utcnow().isoformat()`)
- Tests must clear in-memory `restocking_orders` list between runs via `autouse` fixture

---

## File Changelist

| File | Change |
|------|--------|
| `server/data/demand_forecasts.json` | Add `unit_cost` field to every item |
| `server/main.py` | Add `unit_cost` to `DemandForecast` model; add 3 new models; add 2 new endpoints; import `uuid`, `datetime`, `timedelta` |
| `tests/backend/test_restocking.py` | New — tests for unit_cost on demand, POST/GET restocking-orders |
| `client/src/api.js` | Add `submitRestockingOrder(items)` and `getRestockingOrders()` |
| `client/src/views/Restocking.vue` | New — budget slider, recommendations table, place order flow |
| `client/src/views/Orders.vue` | Add restocking orders section above stats grid |
| `client/src/main.js` | Import `Restocking`; add `/restocking` route |
| `client/src/App.vue` | Add "Restocking" nav link between Demand Forecast and Reports |

---

### Task 1: Add `unit_cost` to demand forecasts (data + model)

**Files:**
- Modify: `server/data/demand_forecasts.json`
- Modify: `server/main.py` (lines ~84–91, `DemandForecast` model)
- Create: `tests/backend/test_restocking.py`

**Interfaces:**
- Produces: `GET /api/demand` returns items with `unit_cost: float` field

- [ ] **Step 1: Update `server/data/demand_forecasts.json`**

Replace the entire file with this content (adds `unit_cost` to each item):

```json
[
  {
    "id": "1",
    "item_sku": "WDG-001",
    "item_name": "Industrial Widget Type A",
    "current_demand": 300,
    "forecasted_demand": 450,
    "trend": "increasing",
    "period": "Next 30 days",
    "unit_cost": 245.00
  },
  {
    "id": "2",
    "item_sku": "BRG-102",
    "item_name": "Steel Bearing Assembly",
    "current_demand": 150,
    "forecasted_demand": 152,
    "trend": "stable",
    "period": "Next 30 days",
    "unit_cost": 18.50
  },
  {
    "id": "3",
    "item_sku": "GSK-203",
    "item_name": "High-Temperature Gasket",
    "current_demand": 500,
    "forecasted_demand": 600,
    "trend": "increasing",
    "period": "Next 30 days",
    "unit_cost": 12.75
  },
  {
    "id": "4",
    "item_sku": "MTR-304",
    "item_name": "Electric Motor 5HP",
    "current_demand": 50,
    "forecasted_demand": 35,
    "trend": "decreasing",
    "period": "Next 30 days",
    "unit_cost": 890.00
  },
  {
    "id": "5",
    "item_sku": "FLT-405",
    "item_name": "Oil Filter Cartridge",
    "current_demand": 800,
    "forecasted_demand": 950,
    "trend": "increasing",
    "period": "Next 30 days",
    "unit_cost": 8.25
  },
  {
    "id": "6",
    "item_sku": "VLV-506",
    "item_name": "Pressure Relief Valve",
    "current_demand": 120,
    "forecasted_demand": 121,
    "trend": "stable",
    "period": "Next 30 days",
    "unit_cost": 125.00
  },
  {
    "id": "7",
    "item_sku": "PSU-501",
    "item_name": "5V 10A Switching Power Supply",
    "current_demand": 250,
    "forecasted_demand": 252,
    "trend": "stable",
    "period": "Next 30 days",
    "unit_cost": 42.50
  },
  {
    "id": "8",
    "item_sku": "SNR-420",
    "item_name": "Temperature Sensor Module",
    "current_demand": 180,
    "forecasted_demand": 182,
    "trend": "stable",
    "period": "Next 30 days",
    "unit_cost": 28.00
  },
  {
    "id": "9",
    "item_sku": "CTL-330",
    "item_name": "Logic Controller Board",
    "current_demand": 95,
    "forecasted_demand": 96,
    "trend": "stable",
    "period": "Next 30 days",
    "unit_cost": 165.00
  }
]
```

- [ ] **Step 2: Add `unit_cost` to `DemandForecast` model in `server/main.py`**

Find the `DemandForecast` class (around line 84) and replace it:

```python
class DemandForecast(BaseModel):
    id: str
    item_sku: str
    item_name: str
    current_demand: int
    forecasted_demand: int
    trend: str
    period: str
    unit_cost: float
```

- [ ] **Step 3: Write failing test**

Create `tests/backend/test_restocking.py`:

```python
"""Tests for restocking-related API endpoints."""
import pytest
import sys
from pathlib import Path

server_path = Path(__file__).parent.parent.parent / "server"
sys.path.insert(0, str(server_path))

import main as app_module


@pytest.fixture(autouse=True)
def clear_restocking_orders():
    app_module.restocking_orders.clear()
    yield
    app_module.restocking_orders.clear()


class TestDemandUnitCost:
    def test_demand_forecasts_include_unit_cost(self, client):
        response = client.get("/api/demand")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        for item in data:
            assert "unit_cost" in item
            assert isinstance(item["unit_cost"], float)
            assert item["unit_cost"] > 0
```

- [ ] **Step 4: Run test — expect FAIL first (before model update) then PASS after**

```bash
cd /Users/vadim_dissa/dev/black-belt/inventory-management
uv run pytest tests/backend/test_restocking.py::TestDemandUnitCost -v
```

Expected after both changes: `PASSED`

- [ ] **Step 5: Restart backend to reload JSON, verify manually**

```bash
# In the server terminal, Ctrl+C then:
cd server && uv run python main.py &
curl -s http://localhost:8001/api/demand | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['unit_cost'])"
```

Expected output: `245.0`

- [ ] **Step 6: Commit**

```bash
git add server/data/demand_forecasts.json server/main.py tests/backend/test_restocking.py
git commit -m "feat: add unit_cost to demand forecasts and test"
```

---

### Task 2: Restocking order backend endpoints

**Files:**
- Modify: `server/main.py` — add imports, in-memory store, 3 models, 2 endpoints

**Interfaces:**
- Produces:
  - `POST /api/restocking-orders` body: `{"items": [{"sku": str, "name": str, "quantity": int, "unit_cost": float}]}` → returns `RestockingOrder`
  - `GET /api/restocking-orders` → returns `List[RestockingOrder]` newest first

- [ ] **Step 1: Write failing tests** — append to `tests/backend/test_restocking.py`

```python
class TestRestockingOrders:
    SAMPLE_ITEMS = [
        {"sku": "WDG-001", "name": "Industrial Widget Type A", "quantity": 150, "unit_cost": 245.00},
        {"sku": "FLT-405", "name": "Oil Filter Cartridge", "quantity": 150, "unit_cost": 8.25},
    ]

    def test_get_restocking_orders_empty(self, client):
        response = client.get("/api/restocking-orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_post_restocking_order_returns_201(self, client):
        response = client.post("/api/restocking-orders", json={"items": self.SAMPLE_ITEMS})
        assert response.status_code == 201

    def test_post_restocking_order_structure(self, client):
        response = client.post("/api/restocking-orders", json={"items": self.SAMPLE_ITEMS})
        data = response.json()
        assert "id" in data
        assert "order_number" in data
        assert data["order_number"].startswith("RST-")
        assert data["status"] == "Submitted"
        assert "submitted_date" in data
        assert "expected_delivery" in data
        assert len(data["items"]) == 2

    def test_post_restocking_order_total_cost(self, client):
        response = client.post("/api/restocking-orders", json={"items": self.SAMPLE_ITEMS})
        data = response.json()
        expected_total = (150 * 245.00) + (150 * 8.25)
        assert abs(data["total_cost"] - expected_total) < 0.01

    def test_post_restocking_order_14_day_lead_time(self, client):
        from datetime import datetime, timedelta
        response = client.post("/api/restocking-orders", json={"items": self.SAMPLE_ITEMS})
        data = response.json()
        submitted = datetime.fromisoformat(data["submitted_date"])
        expected = datetime.fromisoformat(data["expected_delivery"])
        assert (expected - submitted).days == 14

    def test_get_restocking_orders_newest_first(self, client):
        client.post("/api/restocking-orders", json={"items": self.SAMPLE_ITEMS})
        client.post("/api/restocking-orders", json={"items": [self.SAMPLE_ITEMS[0]]})
        response = client.get("/api/restocking-orders")
        data = response.json()
        assert len(data) == 2
        # Newest (second posted) should be first
        assert data[0]["order_number"] == "RST-2026-0002"
        assert data[1]["order_number"] == "RST-2026-0001"

    def test_post_restocking_order_numbering(self, client):
        r1 = client.post("/api/restocking-orders", json={"items": self.SAMPLE_ITEMS})
        r2 = client.post("/api/restocking-orders", json={"items": self.SAMPLE_ITEMS})
        assert r1.json()["order_number"] == "RST-2026-0001"
        assert r2.json()["order_number"] == "RST-2026-0002"
```

- [ ] **Step 2: Run tests — confirm they all FAIL**

```bash
uv run pytest tests/backend/test_restocking.py::TestRestockingOrders -v
```

Expected: all 7 tests FAIL with `404` or connection error

- [ ] **Step 3: Add imports and in-memory store to `server/main.py`**

Add these two imports at the top of `main.py`, after the existing imports:

```python
from datetime import datetime, timedelta
import uuid
```

Add this line right after the existing imports block (before `app = FastAPI(...)`):

```python
# In-memory store for restocking orders — clears on server restart
restocking_orders: List[dict] = []
```

- [ ] **Step 4: Add the three new Pydantic models to `server/main.py`**

Add after the `CreatePurchaseOrderRequest` model (around line 122):

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
    items: List[dict]
    total_cost: float
    status: str
    submitted_date: str
    expected_delivery: str
```

- [ ] **Step 5: Add the two new endpoints to `server/main.py`**

Add at the end of the file (after the last endpoint):

```python
@app.post("/api/restocking-orders", response_model=RestockingOrder, status_code=201)
def create_restocking_order(payload: RestockingOrderCreate):
    """Create a restocking order from recommended items."""
    now = datetime.utcnow()
    order_number = f"RST-2026-{len(restocking_orders) + 1:04d}"
    items_data = [
        {
            "sku": item.sku,
            "name": item.name,
            "quantity": item.quantity,
            "unit_cost": item.unit_cost,
        }
        for item in payload.items
    ]
    order = {
        "id": str(uuid.uuid4()),
        "order_number": order_number,
        "items": items_data,
        "total_cost": sum(item.quantity * item.unit_cost for item in payload.items),
        "status": "Submitted",
        "submitted_date": now.isoformat(),
        "expected_delivery": (now + timedelta(days=14)).isoformat(),
    }
    restocking_orders.append(order)
    return order


@app.get("/api/restocking-orders", response_model=List[RestockingOrder])
def get_restocking_orders():
    """Get all submitted restocking orders, newest first."""
    return list(reversed(restocking_orders))
```

- [ ] **Step 6: Run all restocking tests — confirm they all PASS**

```bash
uv run pytest tests/backend/test_restocking.py -v
```

Expected: all 9 tests PASS

- [ ] **Step 7: Run full test suite to check for regressions**

```bash
uv run pytest tests/backend/ -v
```

Expected: all tests PASS

- [ ] **Step 8: Commit**

```bash
git add server/main.py tests/backend/test_restocking.py
git commit -m "feat: add restocking order endpoints with 14-day lead time"
```

---

### Task 3: Add API client methods

**Files:**
- Modify: `client/src/api.js`

**Interfaces:**
- Consumes: `POST /api/restocking-orders`, `GET /api/restocking-orders`
- Produces:
  - `api.submitRestockingOrder(items)` where `items` is `Array<{sku, name, quantity, unit_cost}>`
  - `api.getRestockingOrders()` returns `Promise<Array<RestockingOrder>>`

- [ ] **Step 1: Add two methods to `client/src/api.js`**

Append inside the `api` object, after the `getPurchaseOrderByBacklogItem` method (before the closing `}`):

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

- [ ] **Step 2: Verify no syntax errors**

```bash
cd /Users/vadim_dissa/dev/black-belt/inventory-management/client
node --input-type=module <<'EOF'
import('./src/api.js').then(m => {
  console.log('submitRestockingOrder' in m.api ? 'OK' : 'MISSING')
  console.log('getRestockingOrders' in m.api ? 'OK' : 'MISSING')
})
EOF
```

Expected: two lines of `OK`

- [ ] **Step 3: Commit**

```bash
git add client/src/api.js
git commit -m "feat: add submitRestockingOrder and getRestockingOrders to api client"
```

---

### Task 4: Create `Restocking.vue`

**Files:**
- Create: `client/src/views/Restocking.vue`

**Interfaces:**
- Consumes: `api.getDemandForecasts()`, `api.submitRestockingOrder(items)`
- No props; standalone page

- [ ] **Step 1: Create `client/src/views/Restocking.vue`**

```vue
<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking Planner</h2>
      <p>Set your available budget to see which items to restock based on demand forecasts.</p>
    </div>

    <div v-if="loading" class="loading">Loading demand forecasts...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Budget Slider -->
      <div class="card budget-card">
        <div class="card-header">
          <h3 class="card-title">Available Budget</h3>
          <span class="budget-display">${{ budget.toLocaleString() }}</span>
        </div>
        <div class="slider-wrapper">
          <span class="slider-label">$0</span>
          <input
            type="range"
            v-model.number="budget"
            min="0"
            max="500000"
            step="1000"
            class="budget-slider"
          />
          <span class="slider-label">$500,000</span>
        </div>
      </div>

      <!-- Budget Summary -->
      <div class="stats-grid" v-if="recommendedItems.length > 0 || orderSuccess">
        <div class="stat-card info">
          <div class="stat-label">Allocated</div>
          <div class="stat-value">${{ allocatedBudget.toLocaleString(undefined, { maximumFractionDigits: 0 }) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">Items Recommended</div>
          <div class="stat-value">{{ recommendedItems.length }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">Remaining</div>
          <div class="stat-value">${{ remainingBudget.toLocaleString(undefined, { maximumFractionDigits: 0 }) }}</div>
        </div>
      </div>

      <!-- Success message -->
      <div v-if="orderSuccess" class="success-banner">
        Order <strong>{{ submittedOrderNumber }}</strong> placed successfully.
        Expected delivery: <strong>{{ submittedDelivery }}</strong>.
      </div>

      <!-- Recommended Items -->
      <div class="card" v-if="!orderSuccess">
        <div class="card-header">
          <h3 class="card-title">Recommended Restocking ({{ recommendedItems.length }} items)</h3>
        </div>

        <div v-if="recommendedItems.length === 0" class="empty-state">
          No items can be restocked within this budget. Try increasing the budget.
        </div>

        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>SKU</th>
                <th>Item Name</th>
                <th>Demand Gap</th>
                <th>Unit Cost</th>
                <th>Restock Qty</th>
                <th>Line Total</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendedItems" :key="item.item_sku">
                <td><code>{{ item.item_sku }}</code></td>
                <td>{{ item.item_name }}</td>
                <td>+{{ item.gap }}</td>
                <td>${{ item.unit_cost.toFixed(2) }}</td>
                <td>{{ item.gap }}</td>
                <td><strong>${{ item.lineTotal.toLocaleString(undefined, { maximumFractionDigits: 0 }) }}</strong></td>
                <td>
                  <button class="btn-remove" @click="excludeItem(item.item_sku)" title="Remove">&#x2715;</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="card-footer" v-if="recommendedItems.length > 0">
          <div v-if="!confirmingOrder">
            <button class="btn-primary" @click="confirmingOrder = true">Place Order</button>
          </div>
          <div v-else class="confirm-row">
            <span>Place restocking order for {{ recommendedItems.length }} items totalling ${{ allocatedBudget.toLocaleString(undefined, { maximumFractionDigits: 0 }) }}?</span>
            <button class="btn-primary" @click="placeOrder" :disabled="submitting">
              {{ submitting ? 'Submitting...' : 'Confirm' }}
            </button>
            <button class="btn-secondary" @click="confirmingOrder = false" :disabled="submitting">Cancel</button>
          </div>
          <div v-if="submitError" class="error">{{ submitError }}</div>
        </div>
      </div>

      <!-- Over Budget Items -->
      <div class="card over-budget-card" v-if="overBudgetItems.length > 0 && !orderSuccess">
        <details>
          <summary class="card-title">Over Budget ({{ overBudgetItems.length }} items not included)</summary>
          <div class="table-container" style="margin-top: 12px;">
            <table>
              <thead>
                <tr>
                  <th>SKU</th>
                  <th>Item Name</th>
                  <th>Demand Gap</th>
                  <th>Unit Cost</th>
                  <th>Would Cost</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in overBudgetItems" :key="item.item_sku">
                  <td><code>{{ item.item_sku }}</code></td>
                  <td>{{ item.item_name }}</td>
                  <td>+{{ item.gap }}</td>
                  <td>${{ item.unit_cost.toFixed(2) }}</td>
                  <td>${{ item.lineTotal.toLocaleString(undefined, { maximumFractionDigits: 0 }) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </details>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'

export default {
  name: 'Restocking',
  setup() {
    const loading = ref(true)
    const error = ref(null)
    const forecasts = ref([])
    const budget = ref(100000)
    const excludedSkus = ref(new Set())
    const confirmingOrder = ref(false)
    const submitting = ref(false)
    const submitError = ref(null)
    const orderSuccess = ref(false)
    const submittedOrderNumber = ref('')
    const submittedDelivery = ref('')

    const loadForecasts = async () => {
      try {
        loading.value = true
        error.value = null
        forecasts.value = await api.getDemandForecasts()
      } catch (err) {
        error.value = 'Failed to load demand forecasts: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Items with a positive demand gap, sorted by gap descending
    const candidateItems = computed(() => {
      return forecasts.value
        .filter(f => f.forecasted_demand > f.current_demand && !excludedSkus.value.has(f.item_sku))
        .map(f => ({
          ...f,
          gap: f.forecasted_demand - f.current_demand,
          lineTotal: (f.forecasted_demand - f.current_demand) * f.unit_cost,
        }))
        .sort((a, b) => b.gap - a.gap)
    })

    // Greedy allocation: add items until budget is exhausted
    const allocation = computed(() => {
      let remaining = budget.value
      const recommended = []
      const overBudget = []
      for (const item of candidateItems.value) {
        if (item.lineTotal <= remaining) {
          recommended.push(item)
          remaining -= item.lineTotal
        } else {
          overBudget.push(item)
        }
      }
      return { recommended, overBudget }
    })

    const recommendedItems = computed(() => allocation.value.recommended)
    const overBudgetItems = computed(() => allocation.value.overBudget)
    const allocatedBudget = computed(() => recommendedItems.value.reduce((s, i) => s + i.lineTotal, 0))
    const remainingBudget = computed(() => budget.value - allocatedBudget.value)

    const excludeItem = (sku) => {
      excludedSkus.value = new Set([...excludedSkus.value, sku])
    }

    const placeOrder = async () => {
      submitting.value = true
      submitError.value = null
      try {
        const items = recommendedItems.value.map(i => ({
          sku: i.item_sku,
          name: i.item_name,
          quantity: i.gap,
          unit_cost: i.unit_cost,
        }))
        const order = await api.submitRestockingOrder(items)
        submittedOrderNumber.value = order.order_number
        submittedDelivery.value = new Date(order.expected_delivery).toLocaleDateString('en-US', {
          year: 'numeric', month: 'short', day: 'numeric'
        })
        orderSuccess.value = true
        confirmingOrder.value = false
      } catch (err) {
        submitError.value = 'Failed to place order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadForecasts)

    return {
      loading,
      error,
      budget,
      recommendedItems,
      overBudgetItems,
      allocatedBudget,
      remainingBudget,
      excludeItem,
      confirmingOrder,
      submitting,
      submitError,
      orderSuccess,
      submittedOrderNumber,
      submittedDelivery,
      placeOrder,
    }
  }
}
</script>

<style scoped>
.page-header {
  margin-bottom: 24px;
}
.page-header h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #f1f5f9;
  margin-bottom: 4px;
}
.page-header p {
  color: #64748b;
  font-size: 0.9rem;
}

.budget-card {
  margin-bottom: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.budget-display {
  font-size: 1.4rem;
  font-weight: 700;
  color: #60a5fa;
}
.slider-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}
.slider-label {
  font-size: 0.75rem;
  color: #64748b;
  white-space: nowrap;
}
.budget-slider {
  flex: 1;
  height: 4px;
  accent-color: #3b82f6;
  cursor: pointer;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.success-banner {
  background: #14432a;
  border: 1px solid #22c55e;
  border-radius: 8px;
  padding: 16px 20px;
  color: #4ade80;
  margin-bottom: 20px;
}

.empty-state {
  padding: 32px;
  text-align: center;
  color: #64748b;
}

.card-footer {
  padding: 16px 20px;
  border-top: 1px solid #334155;
  margin-top: 8px;
}
.confirm-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.confirm-row span {
  color: #94a3b8;
  font-size: 0.875rem;
}

.btn-primary {
  background: #3b82f6;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 8px 18px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
}
.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}
.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-secondary {
  background: transparent;
  color: #94a3b8;
  border: 1px solid #475569;
  border-radius: 6px;
  padding: 8px 18px;
  font-size: 0.875rem;
  cursor: pointer;
}
.btn-secondary:hover:not(:disabled) {
  background: #1e293b;
}
.btn-remove {
  background: transparent;
  border: none;
  color: #64748b;
  cursor: pointer;
  font-size: 0.9rem;
  padding: 2px 6px;
  border-radius: 4px;
}
.btn-remove:hover {
  color: #ef4444;
  background: #2d1f1f;
}

.over-budget-card details summary {
  cursor: pointer;
  padding: 4px 0;
  color: #94a3b8;
}
.over-budget-card details summary::-webkit-details-marker {
  color: #64748b;
}

code {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 0.78rem;
  background: #0f172a;
  color: #7dd3fc;
  padding: 2px 6px;
  border-radius: 4px;
}

.error {
  color: #f87171;
  padding: 8px 0;
  font-size: 0.875rem;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}
thead th {
  text-align: left;
  color: #64748b;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 10px 14px;
  border-bottom: 1px solid #334155;
}
tbody td {
  padding: 10px 14px;
  border-bottom: 1px solid #1e293b;
  color: #cbd5e1;
}
tbody tr:last-child td {
  border-bottom: none;
}
tbody tr:hover td {
  background: #243047;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add client/src/views/Restocking.vue
git commit -m "feat: add Restocking.vue with budget slider and demand-based recommendations"
```

---

### Task 5: Wire route and nav link

**Files:**
- Modify: `client/src/main.js`
- Modify: `client/src/App.vue`

**Interfaces:**
- Produces: `/restocking` route renders `Restocking.vue`; nav shows "Restocking" link between Demand Forecast and Reports

- [ ] **Step 1: Add import and route to `client/src/main.js`**

Add the import after the `Reports` import line:

```js
import Restocking from './views/Restocking.vue'
```

Add the route inside the `routes` array, between the `/demand` and `/spending` routes:

```js
{ path: '/restocking', component: Restocking },
```

The full routes array should look like:
```js
routes: [
  { path: '/', component: Dashboard },
  { path: '/inventory', component: Inventory },
  { path: '/orders', component: Orders },
  { path: '/demand', component: Demand },
  { path: '/restocking', component: Restocking },
  { path: '/spending', component: Spending },
  { path: '/reports', component: Reports }
]
```

- [ ] **Step 2: Add nav link to `client/src/App.vue`**

In the `<nav class="nav-tabs">` block, add this link between the Demand Forecast link and the Reports link:

```html
<router-link to="/restocking" :class="{ active: $route.path === '/restocking' }">
  Restocking
</router-link>
```

- [ ] **Step 3: Verify the app compiles and the tab appears**

Open http://localhost:3000 in a browser. The nav should show a "Restocking" tab. Clicking it should load the Restocking Planner page with the budget slider and a recommendations table.

- [ ] **Step 4: Commit**

```bash
git add client/src/main.js client/src/App.vue
git commit -m "feat: add Restocking route and nav link"
```

---

### Task 6: Add restocking orders section to Orders tab

**Files:**
- Modify: `client/src/views/Orders.vue`

**Interfaces:**
- Consumes: `api.getRestockingOrders()` → `Array<{order_number, items, total_cost, submitted_date, expected_delivery, status}>`

- [ ] **Step 1: Add `restockingOrders` ref and load function to `Orders.vue` `setup()`**

In the `setup()` function, after the `const orders = ref([])` line, add:

```js
const restockingOrders = ref([])
```

After the `loadOrders` function, add:

```js
const loadRestockingOrders = async () => {
  try {
    restockingOrders.value = await api.getRestockingOrders()
  } catch {
    // Silent failure — don't break the main orders table
  }
}
```

In the `onMounted` call, add the second load:

```js
onMounted(() => {
  loadOrders()
  loadRestockingOrders()
})
```

Add `restockingOrders` and `formatDate` to the `return` object (note: `formatDate` is already returned — just add `restockingOrders`).

- [ ] **Step 2: Add restocking orders card to the `Orders.vue` template**

Add this block inside the `<div v-else>` wrapper, **before** the `<div class="stats-grid">`:

```html
<!-- Submitted Restocking Orders -->
<div class="card restocking-orders-card" v-if="restockingOrders.length > 0">
  <div class="card-header">
    <h3 class="card-title">Submitted Restocking Orders ({{ restockingOrders.length }})</h3>
  </div>
  <div class="table-container">
    <table class="orders-table">
      <thead>
        <tr>
          <th>Order #</th>
          <th>Items</th>
          <th>Total Cost</th>
          <th>Submitted</th>
          <th>Expected Delivery</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="order in restockingOrders" :key="order.id">
          <td><strong>{{ order.order_number }}</strong></td>
          <td>{{ order.items.length }} item{{ order.items.length !== 1 ? 's' : '' }}</td>
          <td><strong>${{ order.total_cost.toLocaleString(undefined, { maximumFractionDigits: 0 }) }}</strong></td>
          <td>{{ formatDate(order.submitted_date) }}</td>
          <td>{{ formatDate(order.expected_delivery) }}</td>
          <td><span class="badge restocking">{{ order.status }}</span></td>
        </tr>
      </tbody>
    </table>
  </div>
</div>
```

- [ ] **Step 3: Add the `restocking` badge style to `Orders.vue` scoped styles**

In the `<style scoped>` block, add:

```css
.badge.restocking {
  background: #2d1b69;
  color: #a78bfa;
}
```

- [ ] **Step 4: Verify end-to-end**

1. Go to http://localhost:3000/restocking
2. Move the slider to see recommendations update
3. Click "Place Order" → "Confirm"
4. Navigate to http://localhost:3000/orders
5. A "Submitted Restocking Orders" card should appear above the stat cards, showing the order with a purple "Submitted" badge

- [ ] **Step 5: Commit**

```bash
git add client/src/views/Orders.vue
git commit -m "feat: show submitted restocking orders in Orders tab"
```
