from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import itertools
import threading
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
    allow_origins=["*"],
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
    unit_cost: Optional[float] = None

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
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    notes: Optional[str] = None

# --- Task models ---
# dueDate is intentionally camelCase: the UI reads task.dueDate directly.
class Task(BaseModel):
    id: str
    title: str
    priority: str
    dueDate: str
    status: str

class CreateTaskRequest(BaseModel):
    title: str
    priority: str = "medium"
    dueDate: str

# --- Restocking models ---

class RestockRecommendation(BaseModel):
    item_sku: str
    item_name: str
    current_demand: int
    forecasted_demand: int
    demand_gap: int
    trend: str
    recommended_quantity: int
    unit_cost: float
    line_total: float
    lead_time_days: int
    priority_rank: int

class RestockOrderItemRequest(BaseModel):
    item_sku: str
    item_name: str
    quantity: int = Field(ge=1)
    unit_cost: float = Field(ge=0)

class CreateRestockOrderRequest(BaseModel):
    budget: float = Field(ge=0)
    items: List[RestockOrderItemRequest]

class RestockOrderItem(BaseModel):
    item_sku: str
    item_name: str
    quantity: int
    unit_cost: float
    line_total: float
    lead_time_days: int
    expected_delivery: str

class RestockOrder(BaseModel):
    id: str
    order_number: str
    status: str
    created_date: str
    budget: float
    total_value: float
    item_count: int
    lead_time_days: int
    expected_delivery: str
    items: List[RestockOrderItem]

# In-memory store for submitted restocking orders (resets on server restart,
# consistent with the demo's no-database design).
submitted_restock_orders: List[dict] = []
# Monotonic order sequence + lock so concurrent submissions never collide on
# id / order_number (the sync endpoint runs in Starlette's threadpool).
_restock_order_seq = itertools.count(1)
_restock_lock = threading.Lock()

# In-memory store for tasks (resets on server restart), mirroring the
# restocking-order store + monotonic sequence + lock pattern.
tasks_store: List[dict] = []
_task_seq = itertools.count(1)
_task_lock = threading.Lock()

# Monotonic PO sequence + lock so concurrent purchase-order creations never
# collide on id (mirrors the restocking-order pattern).
_po_seq = itertools.count(1)
_po_lock = threading.Lock()

def restock_unit_cost(sku: str):
    """Authoritative unit cost for a SKU: the demand forecast price, falling
    back to the inventory unit cost. Returns None for an unknown SKU."""
    forecast = next((f for f in demand_forecasts if f["item_sku"] == sku), None)
    if forecast is None:
        return None
    cost = forecast.get("unit_cost")
    if cost is None:
        inv = next((i for i in inventory_items if i["sku"] == sku), None)
        cost = inv["unit_cost"] if inv else None
    return cost

def restock_lead_time_days(sku: str) -> int:
    """Deterministic per-SKU delivery lead time in the 7-28 day range.

    Uses a stable character-sum hash (not Python's randomized hash()) so the
    same SKU always reports the same lead time across requests and restarts.
    """
    return 7 + (sum(ord(c) for c in sku) % 22)

def build_restock_recommendations() -> List[dict]:
    """Build budget-agnostic restock candidates from the demand forecast.

    A candidate is any forecast item with a positive demand gap
    (forecasted - current). Recommended quantity covers exactly that gap.
    Sorted by demand urgency: largest gap first, then largest line total,
    then SKU for a fully deterministic order.
    """
    candidates = []
    for f in demand_forecasts:
        gap = f["forecasted_demand"] - f["current_demand"]
        if gap <= 0:
            continue
        unit_cost = restock_unit_cost(f["item_sku"])
        if unit_cost is None:
            unit_cost = 0.0
        line_total = round(gap * unit_cost, 2)
        candidates.append({
            "item_sku": f["item_sku"],
            "item_name": f["item_name"],
            "current_demand": f["current_demand"],
            "forecasted_demand": f["forecasted_demand"],
            "demand_gap": gap,
            "trend": f["trend"],
            "recommended_quantity": gap,
            "unit_cost": round(unit_cost, 2),
            "line_total": line_total,
            "lead_time_days": restock_lead_time_days(f["item_sku"]),
        })

    candidates.sort(key=lambda c: (-c["demand_gap"], -c["line_total"], c["item_sku"]))
    for rank, c in enumerate(candidates, start=1):
        c["priority_rank"] = rank
    return candidates

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

@app.get("/api/restock/recommendations", response_model=List[RestockRecommendation])
def get_restock_recommendations():
    """Get restock recommendations derived from the demand forecast.

    Returns every item with a positive demand gap, ordered by demand urgency.
    Budget selection happens client-side so the slider responds instantly.
    """
    return build_restock_recommendations()

@app.get("/api/restock/orders", response_model=List[RestockOrder])
def get_restock_orders():
    """Get submitted restocking orders, most recent first."""
    return list(reversed(submitted_restock_orders))

@app.post("/api/restock/orders", response_model=RestockOrder, status_code=201)
def create_restock_order(request: CreateRestockOrderRequest):
    """Submit a restocking order.

    The server is the source of truth: it prices each line from the authoritative
    SKU unit cost (ignoring any client-supplied price), recomputes line totals
    and per-item lead times, and derives the order-level lead time from the
    slowest line (the order is complete only once the last item arrives). It then
    assigns a unique, monotonic RST order number.
    """
    if not request.items:
        raise HTTPException(status_code=400, detail="A restocking order must contain at least one item.")

    created_dt = datetime.now()
    order_items = []
    total_value = 0.0
    max_lead = 0

    for item in request.items:
        unit_cost = restock_unit_cost(item.item_sku)
        if unit_cost is None:
            raise HTTPException(status_code=400, detail=f"Unknown or unpriced SKU: {item.item_sku}")
        line_total = round(item.quantity * unit_cost, 2)
        lead = restock_lead_time_days(item.item_sku)
        total_value += line_total
        max_lead = max(max_lead, lead)
        order_items.append({
            "item_sku": item.item_sku,
            "item_name": item.item_name,
            "quantity": item.quantity,
            "unit_cost": round(unit_cost, 2),
            "line_total": line_total,
            "lead_time_days": lead,
            "expected_delivery": (created_dt + timedelta(days=lead)).isoformat(timespec="seconds"),
        })

    total_value = round(total_value, 2)
    if total_value > round(request.budget, 2) + 1e-9:
        raise HTTPException(
            status_code=400,
            detail=f"Order total {total_value} exceeds budget {request.budget}.",
        )

    # Distinct, never-reused identifiers even under concurrent submissions.
    with _restock_lock:
        seq = next(_restock_order_seq)
        new_order = {
            "id": str(seq),
            "order_number": f"RST-{created_dt.year}-{seq:04d}",
            "status": "Submitted",
            "created_date": created_dt.isoformat(timespec="seconds"),
            "budget": round(request.budget, 2),
            "total_value": total_value,
            "item_count": len(order_items),
            "lead_time_days": max_lead,
            "expected_delivery": (created_dt + timedelta(days=max_lead)).isoformat(timespec="seconds"),
            "items": order_items,
        }
        submitted_restock_orders.append(new_order)
    return new_order

# --- Tasks endpoints ---
@app.get("/api/tasks", response_model=List[Task])
def get_tasks():
    """Get all tasks, newest first."""
    return list(reversed(tasks_store))

@app.post("/api/tasks", response_model=Task, status_code=201)
def create_task(request: CreateTaskRequest):
    """Create a new task.

    The id is the STRING f"task-{seq}" on purpose: the frontend mock tasks in
    useAuth.js use INTEGER ids 1-4 and App.vue uses strict === to decide
    mock-vs-API, so a string id can never collide with them and mutations
    always route to the API instead of the mock list.
    """
    with _task_lock:
        seq = next(_task_seq)
        new_task = {
            "id": f"task-{seq}",
            "title": request.title,
            "priority": request.priority,
            "dueDate": request.dueDate,
            "status": "pending",
        }
        tasks_store.append(new_task)
    return new_task

@app.patch("/api/tasks/{task_id}", response_model=Task)
def toggle_task(task_id: str):
    """Toggle a task's status between 'pending' and 'completed'."""
    task = next((t for t in tasks_store if t["id"] == task_id), None)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    task["status"] = "completed" if task["status"] == "pending" else "pending"
    return task

@app.delete("/api/tasks/{task_id}", status_code=204)
def delete_task(task_id: str):
    """Delete a task by id."""
    task = next((t for t in tasks_store if t["id"] == task_id), None)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    tasks_store.remove(task)

# --- Purchase order endpoints ---
@app.post("/api/purchase-orders", response_model=PurchaseOrder, status_code=201)
def create_purchase_order(request: CreatePurchaseOrderRequest):
    """Create a purchase order for a backlog item.

    Returns the created PO including its id and backlog_item_id, both of which
    the frontend's handlePOCreated handler relies on to update button state.
    """
    created_date = datetime.now().date().isoformat()
    with _po_lock:
        seq = next(_po_seq)
        new_po = {
            "id": f"PO-{seq:04d}",
            "backlog_item_id": request.backlog_item_id,
            "supplier_name": request.supplier_name,
            "quantity": request.quantity,
            "unit_cost": request.unit_cost,
            "expected_delivery_date": request.expected_delivery_date,
            "status": "Pending",
            "created_date": created_date,
            "notes": request.notes,
        }
        purchase_orders.append(new_po)
    return new_po

@app.get("/api/purchase-orders/{backlog_item_id}", response_model=PurchaseOrder)
def get_purchase_order(backlog_item_id: str):
    """Get the purchase order associated with a backlog item."""
    po = next((p for p in purchase_orders if p["backlog_item_id"] == backlog_item_id), None)
    if po is None:
        raise HTTPException(status_code=404, detail=f"No purchase order for backlog item {backlog_item_id}")
    return po

@app.get("/api/backlog", response_model=List[BacklogItem])
def get_backlog():
    """Get backlog items with purchase order status"""
    # Add has_purchase_order flag to each backlog item
    result = []
    for item in backlog_items:
        item_dict = dict(item)
        # Surface the matching PO's id (not just a boolean) so the Dashboard's
        # Create/View PO button state persists across reloads, since the
        # template keys off item.purchase_order_id.
        po = next((p for p in purchase_orders if p["backlog_item_id"] == item["id"]), None)
        if po is not None:
            item_dict["purchase_order_id"] = po["id"]
            item_dict["has_purchase_order"] = True
        else:
            item_dict["has_purchase_order"] = False
        result.append(item_dict)
    return result

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
    uvicorn.run(app, host="0.0.0.0", port=8001)
