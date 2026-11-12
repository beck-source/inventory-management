import os
import threading
from pathlib import Path
from datetime import date, datetime, timedelta
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load the repo-root .env (gitignored) before anything reads the Anthropic credentials.
# Resolved from this file so it works no matter which directory the server
# starts in; already-exported variables win over the file.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import restock_ai
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders

app = FastAPI(title="Factory Inventory Management System")

# Quarter mapping for date filtering
QUARTER_MAP = {
    'Q1-2025': ['2025-01', '2025-02', '2025-03'],
    'Q2-2025': ['2025-04', '2025-05', '2025-06'],
    'Q3-2025': ['2025-07', '2025-08', '2025-09'],
    'Q4-2025': ['2025-10', '2025-11', '2025-12']
}

def filter_by_month(items: list, month: Optional[str]) -> list:
    """Filter items by month/quarter based on order_date field"""
    if not month or month == 'all':
        return items

    if month.startswith('Q'):
        # Handle quarters
        if month in QUARTER_MAP:
            months = QUARTER_MAP[month]
            return [item for item in items if any(m in item.get('order_date', '') for m in months)]
    else:
        # Direct month match
        return [item for item in items if month in item.get('order_date', '')]

    return items

def apply_filters(items: list, warehouse: Optional[str] = None, category: Optional[str] = None,
                 status: Optional[str] = None) -> list:
    """Apply common filters to a list of items"""
    filtered = items

    if warehouse and warehouse != 'all':
        filtered = [item for item in filtered if item.get('warehouse') == warehouse]

    if category and category != 'all':
        filtered = [item for item in filtered if item.get('category', '').lower() == category.lower()]

    if status and status != 'all':
        filtered = [item for item in filtered if item.get('status', '').lower() == status.lower()]

    return filtered

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    # Only the local Vite dev server may call this API from a browser. A wildcard
    # here would let any website the user visits read and submit orders.
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class InventoryItem(BaseModel):
    id: str
    sku: str
    name: str
    category: str
    warehouse: str
    quantity_on_hand: int
    reorder_point: int
    unit_cost: float
    location: str
    last_updated: str

class Order(BaseModel):
    id: str
    order_number: str
    customer: str
    items: List[dict]
    status: str
    order_date: str
    expected_delivery: str
    total_value: float
    actual_delivery: Optional[str] = None
    warehouse: Optional[str] = None
    category: Optional[str] = None

class DemandForecast(BaseModel):
    id: str
    item_sku: str
    item_name: str
    current_demand: int
    forecasted_demand: int
    trend: str
    period: str
    unit_cost: float
    lead_time_days: int

class BacklogItem(BaseModel):
    id: str
    order_id: str
    item_sku: str
    item_name: str
    quantity_needed: int
    quantity_available: int
    days_delayed: int
    priority: str
    has_purchase_order: Optional[bool] = False
    # The dashboard switches "Create PO" to "View PO" based on this id.
    purchase_order_id: Optional[str] = None

class PurchaseOrder(BaseModel):
    id: str
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    status: str
    created_date: str
    notes: Optional[str] = None

class CreatePurchaseOrderRequest(BaseModel):
    backlog_item_id: str
    supplier_name: str = Field(min_length=1, max_length=200)
    quantity: int = Field(ge=1)
    unit_cost: float = Field(gt=0)
    expected_delivery_date: str
    notes: Optional[str] = Field(default=None, max_length=2000)

class Task(BaseModel):
    id: str
    title: str
    priority: str
    # camelCase to match the shape TasksModal.vue and the mock user tasks use.
    dueDate: str
    status: str

class CreateTaskRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    priority: Literal['high', 'medium', 'low'] = 'medium'
    dueDate: str

class RestockLine(BaseModel):
    sku: str
    name: str
    quantity: int
    unit_cost: float
    line_total: float
    lead_time_days: int

class RestockRecommendation(BaseModel):
    budget: float
    total_cost: float
    remaining_budget: float
    max_useful_budget: float
    items: List[RestockLine]

class RestockOrderItemRequest(BaseModel):
    sku: str
    quantity: int = Field(ge=1)

class CreateRestockOrderRequest(BaseModel):
    budget: float = Field(ge=0)
    items: List[RestockOrderItemRequest] = Field(min_length=1)

class RestockOrder(BaseModel):
    id: str
    order_number: str
    items: List[RestockLine]
    total_cost: float
    budget: float
    status: str
    submitted_date: str
    lead_time_days: int
    expected_delivery: str

class AIRestockRequest(BaseModel):
    budget: Optional[float] = Field(default=None, ge=0)

class AIRestockLine(BaseModel):
    sku: str
    name: str
    quantity_on_hand: int
    reorder_point: int
    daily_velocity: float
    days_of_cover: Optional[float] = None
    quantity: int
    unit_cost: float
    line_total: float
    priority: Literal['high', 'medium', 'low']
    reason: str

class AIRestockResponse(BaseModel):
    summary: str
    model: str
    generated_at: str
    budget: Optional[float] = None
    total_cost: float
    items: List[AIRestockLine]

# Inventory items have no lead time of their own; used when a restock order
# includes a SKU that isn't in the demand forecasts.
DEFAULT_LEAD_TIME_DAYS = 14

# Submitted restock orders live in memory only, like the rest of the mock data.
restock_orders: List[dict] = []
# Sync endpoints run in a threadpool, so id assignment + append must be atomic
# or two concurrent POSTs could get the same order number.
restock_orders_lock = threading.Lock()
purchase_orders_lock = threading.Lock()

# API-created tasks, in memory only. Monotonic counter (not len()) so ids are
# never reused after a delete.
tasks: List[dict] = []
next_task_id = 1
tasks_lock = threading.Lock()

# Rank order for trends: growing demand is the most urgent to restock.
TREND_PRIORITY = {'increasing': 0, 'stable': 1, 'decreasing': 2}

def _to_cents(amount: float) -> int:
    # Budget math is done in integer cents: repeated float subtraction drifts
    # (e.g. 8998.78 - ... ends 1e-12 short) and would drop a unit at exact budgets.
    return round(amount * 100)

def _restock_line(forecast: dict, quantity: int) -> dict:
    return {
        "sku": forecast["item_sku"],
        "name": forecast["item_name"],
        "quantity": quantity,
        "unit_cost": forecast["unit_cost"],
        "line_total": round(quantity * forecast["unit_cost"], 2),
        "lead_time_days": forecast["lead_time_days"],
    }

def build_restock_recommendation(budget: float) -> dict:
    """Greedily pick forecast items to restock within the given budget."""
    # Only restock the gap between forecasted and current demand; items whose
    # demand is flat or shrinking (gap <= 0) don't need extra stock.
    candidates = [
        (f, f["forecasted_demand"] - f["current_demand"])
        for f in demand_forecasts
        if f["forecasted_demand"] - f["current_demand"] > 0
    ]
    # Most urgent first: increasing trends, then the largest shortfall.
    candidates.sort(key=lambda c: (TREND_PRIORITY.get(c[0]["trend"], 99), -c[1]))

    max_useful_budget = sum(_to_cents(f["unit_cost"]) * gap for f, gap in candidates) / 100

    items = []
    remaining = _to_cents(budget)
    for forecast, gap in candidates:
        unit_cents = _to_cents(forecast["unit_cost"])
        if unit_cents * gap <= remaining:
            items.append(_restock_line(forecast, gap))
            remaining -= unit_cents * gap
            continue
        # The next-priority item doesn't fully fit: spend what's left on as many
        # whole units as possible, then stop so lower-priority items don't jump
        # ahead of it.
        partial_qty = remaining // unit_cents
        if partial_qty > 0:
            items.append(_restock_line(forecast, partial_qty))
            remaining -= partial_qty * unit_cents
        break

    total_cost = round(sum(i["line_total"] for i in items), 2)
    return {
        "budget": budget,
        "total_cost": total_cost,
        "remaining_budget": round(budget - total_cost, 2),
        "max_useful_budget": max_useful_budget,
        "items": items,
    }

# API endpoints
@app.get("/")
def root():
    return {"message": "Factory Inventory Management System API", "version": "1.0.0"}

@app.get("/api/inventory", response_model=List[InventoryItem])
def get_inventory(
    warehouse: Optional[str] = None,
    category: Optional[str] = None
):
    """Get all inventory items with optional filtering"""
    return apply_filters(inventory_items, warehouse, category)

@app.get("/api/inventory/{item_id}", response_model=InventoryItem)
def get_inventory_item(item_id: str):
    """Get a specific inventory item"""
    item = next((item for item in inventory_items if item["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.get("/api/orders", response_model=List[Order])
def get_orders(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get all orders with optional filtering"""
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)
    return filtered_orders

@app.get("/api/orders/{order_id}", response_model=Order)
def get_order(order_id: str):
    """Get a specific order"""
    order = next((order for order in orders if order["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.get("/api/demand", response_model=List[DemandForecast])
def get_demand_forecasts():
    """Get demand forecasts"""
    return demand_forecasts

@app.get("/api/backlog", response_model=List[BacklogItem])
def get_backlog():
    """Get backlog items with purchase order status"""
    # Add has_purchase_order flag to each backlog item
    po_by_backlog = {po["backlog_item_id"]: po for po in purchase_orders}
    result = []
    for item in backlog_items:
        item_dict = dict(item)
        po = po_by_backlog.get(item["id"])
        item_dict["has_purchase_order"] = po is not None
        item_dict["purchase_order_id"] = po["id"] if po else None
        result.append(item_dict)
    return result

def _require_iso_date(value: str, field: str) -> None:
    # Dates stay strings in the API (like the rest of the mock data), but must be
    # valid YYYY-MM-DD so the UI's new Date(...) never yields "Invalid Date".
    try:
        date.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"{field} must be a YYYY-MM-DD date")

@app.post("/api/purchase-orders", response_model=PurchaseOrder, status_code=201)
def create_purchase_order(request: CreatePurchaseOrderRequest):
    """Create a purchase order for a backlog item (one PO per item)."""
    if not any(b["id"] == request.backlog_item_id for b in backlog_items):
        raise HTTPException(status_code=404, detail=f"Backlog item {request.backlog_item_id} not found")
    _require_iso_date(request.expected_delivery_date, "expected_delivery_date")

    with purchase_orders_lock:
        # Checked under the lock so two concurrent submits can't both create a PO.
        if any(po["backlog_item_id"] == request.backlog_item_id for po in purchase_orders):
            raise HTTPException(status_code=409, detail="A purchase order already exists for this backlog item")
        po = {
            "id": f"PO-{len(purchase_orders) + 1:04d}",
            **request.model_dump(),
            "status": "Pending",
            "created_date": date.today().isoformat(),
        }
        purchase_orders.append(po)
    return po

@app.get("/api/purchase-orders/{backlog_item_id}", response_model=PurchaseOrder)
def get_purchase_order_by_backlog_item(backlog_item_id: str):
    """Get the purchase order created for a backlog item."""
    po = next((po for po in purchase_orders if po["backlog_item_id"] == backlog_item_id), None)
    if not po:
        raise HTTPException(status_code=404, detail=f"No purchase order for backlog item {backlog_item_id}")
    return po

@app.get("/api/tasks", response_model=List[Task])
def get_tasks():
    """Get tasks created through the API (mock user tasks live in the client)."""
    return tasks

@app.post("/api/tasks", response_model=Task, status_code=201)
def create_task(request: CreateTaskRequest):
    """Create a pending task."""
    global next_task_id
    _require_iso_date(request.dueDate, "dueDate")
    with tasks_lock:
        # String ids with a prefix so they never collide with the client's
        # numeric mock-task ids (App.vue routes deletes by id).
        task = {"id": f"task-{next_task_id}", **request.model_dump(), "status": "pending"}
        next_task_id += 1
        # Newest first, matching how App.vue unshifts new tasks.
        tasks.insert(0, task)
    return task

def _find_task(task_id: str) -> dict:
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str):
    """Delete a task."""
    with tasks_lock:
        tasks.remove(_find_task(task_id))
    return {"id": task_id, "deleted": True}

@app.patch("/api/tasks/{task_id}", response_model=Task)
def toggle_task(task_id: str):
    """Toggle a task between pending and completed."""
    with tasks_lock:
        task = _find_task(task_id)
        task["status"] = "pending" if task["status"] == "completed" else "completed"
    return task

@app.get("/api/restock/recommendations", response_model=RestockRecommendation)
def get_restock_recommendations(budget: float = Query(..., ge=0)):
    """Recommend demand-forecast items to restock within a budget."""
    return build_restock_recommendation(budget)

@app.post("/api/restock/ai-recommendations", response_model=AIRestockResponse)
def get_ai_restock_recommendations(request: AIRestockRequest):
    """Ask Claude to rank inventory SKUs for restocking from stock and order history."""
    # POST rather than GET: each call is a paid, non-deterministic model request
    # that shouldn't be cached or prefetched.
    metrics = restock_ai.build_sku_metrics(inventory_items, orders)
    try:
        plan = restock_ai.call_model(metrics, request.budget)
    except restock_ai.AINotConfiguredError as e:
        raise HTTPException(status_code=503, detail=e.detail)
    except restock_ai.AIUpstreamError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    lines = restock_ai.validate_plan(plan, metrics, request.budget)
    return {
        "summary": plan.summary,
        "model": restock_ai.MODEL,
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "budget": request.budget,
        "total_cost": round(sum(l["line_total"] for l in lines), 2),
        "items": lines,
    }

@app.get("/api/restock-orders", response_model=List[RestockOrder])
def get_restock_orders():
    """Get submitted restock orders, newest first."""
    return list(reversed(restock_orders))

@app.post("/api/restock-orders", response_model=RestockOrder, status_code=201)
def create_restock_order(request: CreateRestockOrderRequest):
    """Submit a restock order for the given SKUs and quantities."""
    forecasts_by_sku = {f["item_sku"]: f for f in demand_forecasts}
    inventory_by_sku = {i["sku"]: i for i in inventory_items}

    # Duplicate SKUs would create duplicate lines (and duplicate UI keys); the
    # client should merge quantities instead.
    skus = [item.sku for item in request.items]
    if len(skus) != len(set(skus)):
        raise HTTPException(status_code=400, detail="Each SKU may appear only once per order")

    lines = []
    for item in request.items:
        # Prices come from server data, never from the client, so the budget
        # check below can't be bypassed by sending a lower unit cost.
        forecast = forecasts_by_sku.get(item.sku)
        if forecast:
            lines.append(_restock_line(forecast, item.quantity))
            continue
        # AI recommendations cover all inventory SKUs, most of which have no
        # forecast; fall back to the inventory unit cost and a default lead time.
        inv = inventory_by_sku.get(item.sku)
        if not inv:
            raise HTTPException(status_code=404, detail=f"SKU {item.sku} not found in demand forecasts or inventory")
        lines.append({
            "sku": inv["sku"],
            "name": inv["name"],
            "quantity": item.quantity,
            "unit_cost": inv["unit_cost"],
            "line_total": round(item.quantity * inv["unit_cost"], 2),
            "lead_time_days": DEFAULT_LEAD_TIME_DAYS,
        })

    total_cost = round(sum(l["line_total"] for l in lines), 2)
    if _to_cents(total_cost) > _to_cents(request.budget):
        raise HTTPException(
            status_code=400,
            detail=f"Order total {total_cost:.2f} exceeds budget {request.budget:.2f}"
        )

    # Items ship together, so the order arrives when its slowest item does.
    lead_time_days = max(l["lead_time_days"] for l in lines)
    submitted = datetime.now().replace(microsecond=0)

    with restock_orders_lock:
        next_id = len(restock_orders) + 1
        order = {
            "id": str(next_id),
            "order_number": f"RST-{submitted.year}-{next_id:04d}",
            "items": lines,
            "total_cost": total_cost,
            "budget": request.budget,
            "status": "Submitted",
            "submitted_date": submitted.isoformat(),
            "lead_time_days": lead_time_days,
            "expected_delivery": (submitted + timedelta(days=lead_time_days)).isoformat(),
        }
        restock_orders.append(order)
    return order

@app.get("/api/dashboard/summary")
def get_dashboard_summary(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get summary statistics for dashboard with optional filtering"""
    # Filter inventory
    filtered_inventory = apply_filters(inventory_items, warehouse, category)

    # Filter orders
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)

    total_inventory_value = sum(item["quantity_on_hand"] * item["unit_cost"] for item in filtered_inventory)
    low_stock_items = len([item for item in filtered_inventory if item["quantity_on_hand"] <= item["reorder_point"]])
    pending_orders = len([order for order in filtered_orders if order["status"] in ["Processing", "Backordered"]])
    total_backlog_items = len(backlog_items)

    return {
        "total_inventory_value": round(total_inventory_value, 2),
        "low_stock_items": low_stock_items,
        "pending_orders": pending_orders,
        "total_backlog_items": total_backlog_items,
        "total_orders_value": sum(order["total_value"] for order in filtered_orders)
    }

@app.get("/api/spending/summary")
def get_spending_summary():
    """Get spending summary statistics"""
    return spending_summary

@app.get("/api/spending/monthly")
def get_monthly_spending():
    """Get monthly spending breakdown"""
    return monthly_spending

@app.get("/api/spending/categories")
def get_category_spending():
    """Get spending by category"""
    return category_spending

@app.get("/api/spending/transactions")
def get_recent_transactions():
    """Get recent transactions"""
    return recent_transactions

@app.get("/api/reports/quarterly")
def get_quarterly_reports():
    """Get quarterly performance reports"""
    # Calculate quarterly statistics from orders
    quarters = {}

    for order in orders:
        order_date = order.get('order_date', '')
        # Determine quarter
        if '2025-01' in order_date or '2025-02' in order_date or '2025-03' in order_date:
            quarter = 'Q1-2025'
        elif '2025-04' in order_date or '2025-05' in order_date or '2025-06' in order_date:
            quarter = 'Q2-2025'
        elif '2025-07' in order_date or '2025-08' in order_date or '2025-09' in order_date:
            quarter = 'Q3-2025'
        elif '2025-10' in order_date or '2025-11' in order_date or '2025-12' in order_date:
            quarter = 'Q4-2025'
        else:
            continue

        if quarter not in quarters:
            quarters[quarter] = {
                'quarter': quarter,
                'total_orders': 0,
                'total_revenue': 0,
                'delivered_orders': 0,
                'avg_order_value': 0
            }

        quarters[quarter]['total_orders'] += 1
        quarters[quarter]['total_revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            quarters[quarter]['delivered_orders'] += 1

    # Calculate averages and fulfillment rate
    result = []
    for q, data in quarters.items():
        if data['total_orders'] > 0:
            data['avg_order_value'] = round(data['total_revenue'] / data['total_orders'], 2)
            data['fulfillment_rate'] = round((data['delivered_orders'] / data['total_orders']) * 100, 1)
        result.append(data)

    # Sort by quarter
    result.sort(key=lambda x: x['quarter'])
    return result

@app.get("/api/reports/monthly-trends")
def get_monthly_trends():
    """Get month-over-month trends"""
    months = {}

    for order in orders:
        order_date = order.get('order_date', '')
        if not order_date:
            continue

        # Extract month (format: YYYY-MM-DD)
        month = order_date[:7]  # Gets YYYY-MM

        if month not in months:
            months[month] = {
                'month': month,
                'order_count': 0,
                'revenue': 0,
                'delivered_count': 0
            }

        months[month]['order_count'] += 1
        months[month]['revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            months[month]['delivered_count'] += 1

    # Convert to list and sort
    result = list(months.values())
    result.sort(key=lambda x: x['month'])
    return result

if __name__ == "__main__":
    import uvicorn
    # Bind to loopback by default: the API has no authentication, so it must not be
    # reachable from other machines. API_HOST exists for containerized setups only.
    uvicorn.run(app, host=os.environ.get("API_HOST", "127.0.0.1"), port=8001)
