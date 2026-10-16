import threading
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import date, timedelta
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
    # Optional so older forecast records without these fields still validate
    category: Optional[str] = None
    unit_cost: Optional[float] = None
    quantity_on_hand: Optional[int] = None
    # Units already submitted in restocking orders but not yet received.
    # Computed per request from submitted_orders, never stored on the record.
    on_order: int = 0

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

class RestockLineRequest(BaseModel):
    sku: str
    quantity: int

class CreateRestockOrderRequest(BaseModel):
    items: List[RestockLineRequest]

class SubmittedOrderLine(BaseModel):
    sku: str
    name: str
    quantity: int
    unit_cost: float
    line_total: float
    lead_time_days: int

class SubmittedOrder(BaseModel):
    id: str
    order_number: str
    items: List[SubmittedOrderLine]
    total_value: float
    lead_time_days: int
    order_date: str
    expected_delivery: str
    status: str

# Restocking orders live in their own list so they do not change the main
# orders feed, dashboard totals, or reports. Memory only, reset on restart.
submitted_orders: List[SubmittedOrder] = []
# The endpoint is a sync def, so FastAPI may run concurrent requests in
# threads. The lock keeps id and order_number unique across them.
_restock_lock = threading.Lock()
# Upper bound per line so a direct API call cannot submit an absurd quantity.
MAX_LINE_QUANTITY = 100000

# Fixed delivery lead time in days per product category.
# Unknown categories fall back to DEFAULT_LEAD_TIME_DAYS.
LEAD_TIME_DAYS = {
    'Actuators': 21,
    'Circuit Boards': 10,
    'Controllers': 14,
    'Power Supplies': 7,
    'Sensors': 12
}
DEFAULT_LEAD_TIME_DAYS = 14

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
    """Get demand forecasts, with units already on order from restocking submissions"""
    # Sum submitted quantities per SKU. There is no receiving flow, so these
    # units stay on order for the life of the server process.
    on_order_by_sku = {}
    for order in submitted_orders:
        for line in order.items:
            on_order_by_sku[line.sku] = on_order_by_sku.get(line.sku, 0) + line.quantity
    # Copy each record so the shared forecast data is never mutated.
    return [
        {**forecast, "on_order": on_order_by_sku.get(forecast["item_sku"], 0)}
        for forecast in demand_forecasts
    ]

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

@app.post("/api/restocking/orders", response_model=SubmittedOrder, status_code=201)
def create_restock_order(request: CreateRestockOrderRequest):
    """Submit a restocking order for items from the demand forecast"""
    if not request.items:
        raise HTTPException(status_code=400, detail="Order must include at least one item")

    forecasts_by_sku = {f["item_sku"]: f for f in demand_forecasts}
    seen_skus = set()
    lines = []
    for line in request.items:
        if line.sku in seen_skus:
            raise HTTPException(status_code=400, detail=f"Duplicate SKU in order: {line.sku}")
        seen_skus.add(line.sku)

        if line.quantity <= 0 or line.quantity > MAX_LINE_QUANTITY:
            raise HTTPException(
                status_code=400,
                detail=f"Quantity for {line.sku} must be between 1 and {MAX_LINE_QUANTITY}"
            )

        forecast = forecasts_by_sku.get(line.sku)
        if not forecast:
            raise HTTPException(status_code=400, detail=f"Unknown SKU: {line.sku}")

        # Price and lead time come from server data, never from the request,
        # so a client cannot submit its own unit cost.
        unit_cost = forecast["unit_cost"]
        lead_time = LEAD_TIME_DAYS.get(forecast["category"], DEFAULT_LEAD_TIME_DAYS)
        lines.append(SubmittedOrderLine(
            sku=line.sku,
            name=forecast["item_name"],
            quantity=line.quantity,
            unit_cost=unit_cost,
            line_total=round(unit_cost * line.quantity, 2),
            lead_time_days=lead_time
        ))

    # The order is complete when its slowest line arrives, so the order's
    # lead time is the maximum across lines, not the average.
    order_lead_time = max(line.lead_time_days for line in lines)
    today = date.today()
    # Id is read and assigned inside the lock so two concurrent submits cannot share one.
    with _restock_lock:
        next_number = len(submitted_orders) + 1
        order = SubmittedOrder(
            id=str(next_number),
            order_number=f"RST-{today.year}-{next_number:04d}",
            items=lines,
            total_value=round(sum(line.line_total for line in lines), 2),
            lead_time_days=order_lead_time,
            order_date=today.isoformat(),
            expected_delivery=(today + timedelta(days=order_lead_time)).isoformat(),
            status="Submitted"
        )
        submitted_orders.append(order)
    return order

@app.get("/api/restocking/orders", response_model=List[SubmittedOrder])
def get_submitted_orders():
    """Get submitted restocking orders, newest first"""
    return list(reversed(submitted_orders))

# Tasks live in memory only, like restocking orders, and reset on restart.
class Task(BaseModel):
    id: int
    title: str
    priority: str
    dueDate: str
    status: str

class CreateTaskRequest(BaseModel):
    title: str
    priority: str = "medium"
    dueDate: str

TASK_PRIORITIES = {"low", "medium", "high"}
# The client's mock tasks use ids 1..n and the client checks mock tasks first
# on delete and toggle, so API task ids start high to never collide with them.
TASK_ID_START = 1000
tasks: List[Task] = []
# A separate counter, not len(tasks), so an id is never reused after a delete.
_next_task_id = TASK_ID_START
_task_lock = threading.Lock()

def _find_task(task_id: int) -> Task:
    for task in tasks:
        if task.id == task_id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

@app.get("/api/tasks", response_model=List[Task])
def get_tasks():
    """Get tasks, newest first"""
    return list(reversed(tasks))

@app.post("/api/tasks", response_model=Task, status_code=201)
def create_task(request: CreateTaskRequest):
    """Create a task"""
    title = request.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")
    if request.priority not in TASK_PRIORITIES:
        raise HTTPException(status_code=400, detail="Priority must be low, medium or high")
    try:
        date.fromisoformat(request.dueDate)
    except ValueError:
        raise HTTPException(status_code=400, detail="dueDate must be YYYY-MM-DD")

    global _next_task_id
    with _task_lock:
        task = Task(
            id=_next_task_id,
            title=title,
            priority=request.priority,
            dueDate=request.dueDate,
            status="pending"
        )
        _next_task_id += 1
        tasks.append(task)
    return task

@app.patch("/api/tasks/{task_id}", response_model=Task)
def toggle_task(task_id: int):
    """Toggle a task between pending and completed"""
    with _task_lock:
        task = _find_task(task_id)
        task.status = "completed" if task.status == "pending" else "pending"
    return task

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int):
    """Delete a task"""
    with _task_lock:
        task = _find_task(task_id)
        tasks.remove(task)
    return {"deleted": task_id}

# Purchase orders are created from a backlog item. The list is the same one
# /api/backlog reads, so a new PO immediately shows as has_purchase_order.
_po_lock = threading.Lock()

@app.post("/api/purchase-orders", response_model=PurchaseOrder, status_code=201)
def create_purchase_order(request: CreatePurchaseOrderRequest):
    """Create a purchase order for a backlog item. One PO per backlog item."""
    if not request.supplier_name.strip():
        raise HTTPException(status_code=400, detail="Supplier name is required")
    if request.quantity <= 0 or request.quantity > MAX_LINE_QUANTITY:
        raise HTTPException(
            status_code=400,
            detail=f"Quantity must be between 1 and {MAX_LINE_QUANTITY}"
        )
    if request.unit_cost < 0:
        raise HTTPException(status_code=400, detail="Unit cost cannot be negative")
    try:
        date.fromisoformat(request.expected_delivery_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="expected_delivery_date must be YYYY-MM-DD")

    if not any(item["id"] == request.backlog_item_id for item in backlog_items):
        raise HTTPException(status_code=404, detail=f"Backlog item {request.backlog_item_id} not found")

    today = date.today()
    # The duplicate check and the append share one lock so two concurrent
    # requests cannot both create a PO for the same backlog item.
    with _po_lock:
        if any(po["backlog_item_id"] == request.backlog_item_id for po in purchase_orders):
            raise HTTPException(status_code=409, detail="A purchase order already exists for this backlog item")
        next_number = len(purchase_orders) + 1
        po = {
            "id": f"PO-{today.year}-{next_number:04d}",
            "backlog_item_id": request.backlog_item_id,
            "supplier_name": request.supplier_name.strip(),
            "quantity": request.quantity,
            "unit_cost": request.unit_cost,
            "expected_delivery_date": request.expected_delivery_date,
            "status": "Ordered",
            "created_date": today.isoformat(),
            "notes": request.notes,
        }
        purchase_orders.append(po)
    return po

@app.get("/api/purchase-orders/{backlog_item_id}", response_model=PurchaseOrder)
def get_purchase_order_by_backlog_item(backlog_item_id: str):
    """Get the purchase order for a backlog item"""
    for po in purchase_orders:
        if po["backlog_item_id"] == backlog_item_id:
            return po
    raise HTTPException(status_code=404, detail=f"No purchase order for backlog item {backlog_item_id}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
