import datetime
from math import ceil
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders

app = FastAPI(title="Factory Inventory Management System")

# Quarter mapping for date filtering
QUARTER_MAP = {
    'Q1-2025': ['2025-01', '2025-02', '2025-03'],
    'Q2-2025': ['2025-04', '2025-05', '2025-06'],
    'Q3-2025': ['2025-07', '2025-08', '2025-09'],
    'Q4-2025': ['2025-10', '2025-11', '2025-12']
}

# Per-warehouse fixed lead times for restocking. Picked to roughly match
# transit-time expectations from each region's primary supplier hub.
LEAD_TIMES = {
    "San Francisco": 7,
    "London": 14,
    "Tokyo": 21,
}

# In-memory state for restocking submissions. Matches the rest of the demo:
# nothing persists across restarts, mock data resets to JSON on reload.
submitted_orders: List[dict] = []
_submitted_seq = 0

# In-memory task list. Same volatile pattern as submitted_orders — wiped on
# restart. Frontend merges these with mock tasks from useAuth.js.
tasks: List[dict] = []
_task_seq = 0

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

class SubmittedOrderLine(BaseModel):
    sku: str
    name: str
    quantity: int
    unit_cost: float
    line_total: float

class SubmittedOrder(BaseModel):
    id: str
    warehouse: str
    items: List[SubmittedOrderLine]
    total_value: float
    submitted_date: str
    expected_delivery_date: str
    lead_time_days: int
    status: str = "Submitted"

class RestockingRecommendation(BaseModel):
    sku: str
    name: str
    warehouse: str
    category: str
    unit_cost: float
    quantity_on_hand: int
    reorder_point: int
    forecasted_demand: int
    trend: Optional[str] = None
    tier: int
    shortfall: int
    urgency: str
    recommended_quantity: int
    line_total: float

class RestockingCartItem(BaseModel):
    sku: str
    quantity: int

class CreateRestockingRequest(BaseModel):
    items: List[RestockingCartItem]
    budget: float

# Task fields use camelCase (dueDate, not due_date) to match the frontend
# shape — App.vue merges these with mock tasks from useAuth.js which already
# use camelCase, so renaming server-side would force a frontend rewrite.
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
    result = []
    for item in backlog_items:
        item_dict = dict(item)
        # Check if this backlog item has a purchase order
        has_po = any(po["backlog_item_id"] == item["id"] for po in purchase_orders)
        item_dict["has_purchase_order"] = has_po
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

def compute_recommendations(budget: float) -> List[dict]:
    """Build a budget-bounded restocking plan."""
    # Tiered priority + greedy fill. We sort all candidates into 3 tiers:
    #   tier 1 = qty_on_hand below reorder_point (urgent stockout risk)
    #   tier 2 = trend == 'increasing' (rising demand, plan ahead)
    #   tier 3 = trend == 'stable' (steady-state restock)
    # Items with trend == 'decreasing' are intentionally skipped — never
    # buy more of something demand is dropping for.
    demand_by_sku = {d["item_sku"]: d for d in demand_forecasts}
    candidates = []
    for item in inventory_items:
        sku = item["sku"]
        forecast = demand_by_sku.get(sku)
        trend = forecast.get("trend") if forecast else None

        if item["quantity_on_hand"] < item["reorder_point"]:
            tier, urgency = 1, "urgent"
            shortfall = item["reorder_point"] - item["quantity_on_hand"]
        elif trend == "increasing":
            tier, urgency = 2, "rising"
            shortfall = 0
        elif trend == "stable":
            tier, urgency = 3, "stable"
            shortfall = 0
        else:
            continue

        forecasted = forecast["forecasted_demand"] if forecast else 0
        # Recommended qty: enough to refill below-reorder gaps OR cover ~1/3
        # of the next forecast window, whichever is larger. Floor at 1.
        recommended_qty = max(
            item["reorder_point"] - item["quantity_on_hand"],
            ceil(forecasted / 3) if forecasted else 1,
            1,
        )

        candidates.append({
            "sku": sku,
            "name": item["name"],
            "warehouse": item["warehouse"],
            "category": item["category"],
            "unit_cost": item["unit_cost"],
            "quantity_on_hand": item["quantity_on_hand"],
            "reorder_point": item["reorder_point"],
            "forecasted_demand": forecasted,
            "trend": trend,
            "tier": tier,
            "shortfall": shortfall,
            "urgency": urgency,
            "recommended_quantity": recommended_qty,
            "line_total": round(recommended_qty * item["unit_cost"], 2),
        })

    # Sort by tier asc; within tier, biggest shortfall first, then highest
    # forecasted demand. This pushes the most-at-risk SKUs to the top.
    candidates.sort(key=lambda c: (c["tier"], -c["shortfall"], -c["forecasted_demand"]))

    # Greedy fill: take a candidate if it fits; if not, try buying a
    # smaller (still >=1) quantity at the same unit cost. Continue past
    # misses — later candidates may be cheaper and still fit.
    selected = []
    remaining = budget
    for c in candidates:
        if c["line_total"] <= remaining:
            selected.append(c)
            remaining -= c["line_total"]
            continue
        max_qty = int(remaining // c["unit_cost"])
        if max_qty >= 1:
            partial = dict(c)
            partial["recommended_quantity"] = max_qty
            partial["line_total"] = round(max_qty * c["unit_cost"], 2)
            selected.append(partial)
            remaining -= partial["line_total"]
    return selected

@app.get("/api/restocking/recommendations", response_model=List[RestockingRecommendation])
def get_restocking_recommendations(budget: float = 100000.0):
    """Compute restocking candidates that fit within budget."""
    if budget < 0:
        raise HTTPException(status_code=400, detail="Budget must be non-negative")
    return compute_recommendations(budget)

@app.get("/api/restocking/orders", response_model=List[SubmittedOrder])
def get_submitted_orders():
    """Return all restocking orders submitted in this server session."""
    return submitted_orders

@app.post("/api/restocking/orders", response_model=List[SubmittedOrder])
def create_restocking_orders(req: CreateRestockingRequest):
    """Submit a restocking cart. Returns one order per touched warehouse."""
    global _submitted_seq
    if not req.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    inventory_by_sku = {item["sku"]: item for item in inventory_items}

    # Group by warehouse — lead time is per-warehouse, so each warehouse
    # gets its own SubmittedOrder with its own ETA. One click can produce
    # multiple orders if the cart spans warehouses.
    by_warehouse: dict = {}
    for cart_item in req.items:
        item = inventory_by_sku.get(cart_item.sku)
        if not item:
            raise HTTPException(status_code=400, detail=f"Unknown SKU: {cart_item.sku}")
        if cart_item.quantity < 1:
            raise HTTPException(status_code=400, detail=f"Quantity must be >= 1 for {cart_item.sku}")
        warehouse = item["warehouse"]
        line = {
            "sku": cart_item.sku,
            "name": item["name"],
            "quantity": cart_item.quantity,
            "unit_cost": item["unit_cost"],
            "line_total": round(cart_item.quantity * item["unit_cost"], 2),
        }
        by_warehouse.setdefault(warehouse, []).append(line)

    today = datetime.date.today()
    new_orders = []
    for warehouse, lines in by_warehouse.items():
        _submitted_seq += 1
        # Fallback to 14 days for any warehouse not in LEAD_TIMES (defensive
        # only — current data has just SF/London/Tokyo).
        lead_days = LEAD_TIMES.get(warehouse, 14)
        eta = today + datetime.timedelta(days=lead_days)
        order = {
            "id": f"SUB-{_submitted_seq:03d}",
            "warehouse": warehouse,
            "items": lines,
            "total_value": round(sum(l["line_total"] for l in lines), 2),
            "submitted_date": today.isoformat(),
            "expected_delivery_date": eta.isoformat(),
            "lead_time_days": lead_days,
            "status": "Submitted",
        }
        submitted_orders.append(order)
        new_orders.append(order)

    return new_orders

@app.get("/api/tasks", response_model=List[Task])
def get_tasks():
    """Get all API-created tasks (mock tasks live client-side in useAuth.js)."""
    return tasks

@app.post("/api/tasks", response_model=Task)
def create_task(req: CreateTaskRequest):
    """Create a new task. New tasks always start in 'pending' status."""
    global _task_seq
    _task_seq += 1
    # Prefix distinguishes API-created tasks from mock ones; App.vue routes
    # delete/toggle calls based on whether the id is found in the mock list.
    task = {
        "id": f"task-api-{_task_seq:03d}",
        "title": req.title,
        "priority": req.priority,
        "dueDate": req.dueDate,
        "status": "pending",
    }
    tasks.append(task)
    return task

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str):
    """Delete a task by id. Mock tasks are removed client-side, never reach here."""
    idx = next((i for i, t in enumerate(tasks) if t["id"] == task_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Task not found")
    tasks.pop(idx)
    return {"success": True}

@app.patch("/api/tasks/{task_id}", response_model=Task)
def toggle_task(task_id: str):
    """Flip a task between 'pending' and 'completed'."""
    task = next((t for t in tasks if t["id"] == task_id), None)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    task["status"] = "completed" if task["status"] == "pending" else "pending"
    return task

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
