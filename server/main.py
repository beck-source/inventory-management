from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import itertools
import math
import os
import re
import threading
from datetime import date, datetime, timedelta
from functools import lru_cache
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders, submitted_orders

app = FastAPI(title="Factory Inventory Management System")

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    # Drop echoed input: it can hold non-JSON floats (NaN) and large payloads
    errors = [{"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": errors})

# Quarter mapping for date filtering
QUARTER_MAP = {
    'Q1-2025': ['2025-01', '2025-02', '2025-03'],
    'Q2-2025': ['2025-04', '2025-05', '2025-06'],
    'Q3-2025': ['2025-07', '2025-08', '2025-09'],
    'Q4-2025': ['2025-10', '2025-11', '2025-12']
}

MONTH_PATTERN = re.compile(r'^\d{4}-(0[1-9]|1[0-2])$')

# month string (YYYY-MM) -> quarter key, derived from QUARTER_MAP
MONTH_TO_QUARTER = {m: q for q, months in QUARTER_MAP.items() for m in months}

# Caps on runtime-created records (in-memory demo, cleared on restart)
MAX_STORED_RECORDS = 1000

def filter_by_month(items: list, month: Optional[str]) -> list:
    """Filter items by month (YYYY-MM) or quarter (e.g. Q1-2025) based on order_date field"""
    if not month or month == 'all':
        return items

    if month in QUARTER_MAP:
        months = set(QUARTER_MAP[month])
        return [item for item in items if item.get('order_date', '')[:7] in months]

    if MONTH_PATTERN.match(month):
        return [item for item in items if item.get('order_date', '')[:7] == month]

    raise HTTPException(status_code=400, detail="Invalid month: use YYYY-MM, a quarter such as Q1-2025, or 'all'")

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

# CORS middleware: local frontend only by default, override with CORS_ORIGINS (comma-separated)
DEFAULT_CORS_ORIGINS = "http://localhost:3000,http://127.0.0.1:3000"
CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", DEFAULT_CORS_ORIGINS).split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
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
    model_config = ConfigDict(allow_inf_nan=False)

    backlog_item_id: str = Field(max_length=64)
    supplier_name: str = Field(min_length=1, max_length=200)
    quantity: int = Field(le=1_000_000)
    unit_cost: float = Field(le=10_000_000)
    expected_delivery_date: date
    notes: Optional[str] = Field(default=None, max_length=2000)

class RestockRecommendation(BaseModel):
    sku: str
    name: str
    category: str
    trend: str
    current_stock: int
    forecasted_demand: int
    shortfall: int
    unit_cost: float
    quantity: int
    line_cost: float
    lead_time_days: int

class RestockRecommendationsResponse(BaseModel):
    budget: float
    total_cost: float
    items: List[RestockRecommendation]

class RestockOrderItem(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    sku: str = Field(max_length=64)
    quantity: int = Field(le=1_000_000)

class CreateRestockOrderRequest(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    budget: float = Field(le=1_000_000_000)
    items: List[RestockOrderItem] = Field(max_length=200)

class SubmittedOrderItem(BaseModel):
    sku: str
    name: str
    category: str
    quantity: int
    unit_cost: float
    line_cost: float
    lead_time_days: int

class SubmittedOrder(BaseModel):
    id: str
    order_number: str
    submitted_at: str
    budget: float
    items: List[SubmittedOrderItem]
    total_cost: float
    lead_time_days: int
    expected_delivery: str
    status: str

# Restocking lead times in days, by inventory category
CATEGORY_LEAD_TIME_DAYS = {
    'Circuit Boards': 7,
    'Sensors': 10,
    'Controllers': 12,
    'Power Supplies': 14,
    'Actuators': 21,
}
DEFAULT_LEAD_TIME_DAYS = 14

TREND_PRIORITY = {'increasing': 0, 'stable': 1, 'decreasing': 2}

restock_order_lock = threading.Lock()
purchase_order_lock = threading.Lock()

def lead_time_for(category: str) -> int:
    return CATEGORY_LEAD_TIME_DAYS.get(category, DEFAULT_LEAD_TIME_DAYS)

def to_cents(amount: float) -> int:
    return round(amount * 100)

def restock_candidates() -> list:
    """Demand items with a positive shortfall: (forecast, inventory item, shortfall)"""
    inventory_by_sku = {item["sku"]: item for item in inventory_items}
    candidates = []
    for forecast in demand_forecasts:
        stock = inventory_by_sku.get(forecast["item_sku"])
        if not stock:
            continue
        shortfall = forecast["forecasted_demand"] - stock["quantity_on_hand"]
        if shortfall <= 0 or stock["unit_cost"] <= 0:
            continue
        candidates.append((forecast, stock, shortfall))
    return candidates

inventory_by_id = {item["id"]: item for item in inventory_items}
orders_by_id = {order["id"]: order for order in orders}
backlog_ids = {item["id"] for item in backlog_items}

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
    item = inventory_by_id.get(item_id)
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
    order = orders_by_id.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.get("/api/demand", response_model=List[DemandForecast])
def get_demand_forecasts():
    """Get demand forecasts"""
    return demand_forecasts

@app.get("/api/restock/recommendations", response_model=RestockRecommendationsResponse)
def get_restock_recommendations(budget: float = 0):
    """Recommend demand-forecast items to restock within the given budget"""
    if not math.isfinite(budget) or budget < 0:
        raise HTTPException(status_code=400, detail="Budget must be a non-negative number")

    candidates = restock_candidates()

    # Increasing trend first, then largest shortfall
    candidates.sort(key=lambda c: (TREND_PRIORITY.get(c[0]["trend"], 3), -c[2]))

    remaining_cents = to_cents(budget)
    recommendations = []
    for forecast, stock, shortfall in candidates:
        unit_cents = to_cents(stock["unit_cost"])
        quantity = min(shortfall, remaining_cents // unit_cents)
        if quantity <= 0:
            continue
        line_cost = quantity * unit_cents / 100
        remaining_cents -= quantity * unit_cents
        recommendations.append({
            "sku": stock["sku"],
            "name": stock["name"],
            "category": stock["category"],
            "trend": forecast["trend"],
            "current_stock": stock["quantity_on_hand"],
            "forecasted_demand": forecast["forecasted_demand"],
            "shortfall": shortfall,
            "unit_cost": stock["unit_cost"],
            "quantity": quantity,
            "line_cost": line_cost,
            "lead_time_days": lead_time_for(stock["category"]),
        })

    return {
        "budget": budget,
        "total_cost": round(sum(r["line_cost"] for r in recommendations), 2),
        "items": recommendations,
    }

@app.post("/api/restock/orders", response_model=SubmittedOrder)
def create_restock_order(request: CreateRestockOrderRequest):
    """Submit a restocking order"""
    if not math.isfinite(request.budget) or request.budget <= 0:
        raise HTTPException(status_code=400, detail="Budget must be positive")
    if not request.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")

    skus = [i.sku for i in request.items]
    if len(set(skus)) != len(skus):
        raise HTTPException(status_code=400, detail="Duplicate SKUs in order")

    shortfall_by_sku = {stock["sku"]: (stock, shortfall) for _, stock, shortfall in restock_candidates()}
    line_items = []
    total_cents = 0
    for requested in request.items:
        if requested.quantity <= 0:
            raise HTTPException(status_code=400, detail=f"Quantity must be positive for {requested.sku}")
        entry = shortfall_by_sku.get(requested.sku)
        if not entry:
            raise HTTPException(status_code=400, detail=f"SKU not eligible for restocking: {requested.sku}")
        stock, shortfall = entry
        if requested.quantity > shortfall:
            raise HTTPException(status_code=400, detail=f"Quantity for {requested.sku} exceeds shortfall of {shortfall}")
        line_cents = requested.quantity * to_cents(stock["unit_cost"])
        total_cents += line_cents
        line_items.append({
            "sku": stock["sku"],
            "name": stock["name"],
            "category": stock["category"],
            "quantity": requested.quantity,
            "unit_cost": stock["unit_cost"],
            "line_cost": line_cents / 100,
            "lead_time_days": lead_time_for(stock["category"]),
        })

    if total_cents > to_cents(request.budget):
        raise HTTPException(status_code=400, detail="Order total exceeds budget")
    total_cost = total_cents / 100

    lead_time_days = max(i["lead_time_days"] for i in line_items)
    with restock_order_lock:
        if len(submitted_orders) >= MAX_STORED_RECORDS:
            raise HTTPException(status_code=429, detail="Restock order limit reached")
        order_id = str(max((int(o["id"]) for o in submitted_orders), default=0) + 1)
        order = _build_restock_order(order_id, request, line_items, total_cost, lead_time_days)
        submitted_orders.append(order)
    return order

def _build_restock_order(order_id, request, line_items, total_cost, lead_time_days) -> dict:
    return {
        "id": order_id,
        "order_number": f"RST-{int(order_id):04d}",
        "submitted_at": datetime.now().isoformat(timespec="seconds"),
        "budget": request.budget,
        "items": line_items,
        "total_cost": total_cost,
        "lead_time_days": lead_time_days,
        "expected_delivery": (date.today() + timedelta(days=lead_time_days)).isoformat(),
        "status": "Submitted",
    }

@app.get("/api/restock/orders", response_model=List[SubmittedOrder])
def get_restock_orders():
    """Get submitted restocking orders, newest first"""
    return list(reversed(submitted_orders))

@app.get("/api/backlog", response_model=List[BacklogItem])
def get_backlog():
    """Get backlog items with purchase order status"""
    # Add has_purchase_order flag to each backlog item
    result = []
    with purchase_order_lock:
        po_backlog_ids = {po["backlog_item_id"] for po in purchase_orders}
    for item in backlog_items:
        item_dict = dict(item)
        item_dict["has_purchase_order"] = item["id"] in po_backlog_ids
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

@lru_cache(maxsize=1)
def _quarterly_report() -> tuple:
    # Orders are static mock data, so the aggregate is computed once
    quarters = {}

    for order in orders:
        quarter = MONTH_TO_QUARTER.get(order.get('order_date', '')[:7])
        if quarter is None:
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
    for data in quarters.values():
        if data['total_orders'] > 0:
            data['avg_order_value'] = round(data['total_revenue'] / data['total_orders'], 2)
            data['fulfillment_rate'] = round((data['delivered_orders'] / data['total_orders']) * 100, 1)
        result.append(data)

    result.sort(key=lambda x: x['quarter'])
    return tuple(result)

@lru_cache(maxsize=1)
def _monthly_trends() -> tuple:
    months = {}

    for order in orders:
        order_date = order.get('order_date', '')
        if not order_date:
            continue

        month = order_date[:7]  # YYYY-MM

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

    return tuple(sorted(months.values(), key=lambda x: x['month']))

@app.get("/api/reports/quarterly")
def get_quarterly_reports():
    """Get quarterly performance reports"""
    return list(_quarterly_report())

@app.get("/api/reports/monthly-trends")
def get_monthly_trends():
    """Get month-over-month trends"""
    return list(_monthly_trends())

class Task(BaseModel):
    id: str
    title: str
    priority: str
    dueDate: str
    status: str

class CreateTaskRequest(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    title: str = Field(min_length=1, max_length=200)
    priority: Literal["low", "medium", "high"] = "medium"
    dueDate: date

# Tasks created at runtime (in-memory, cleared on restart)
tasks: List[dict] = []
tasks_lock = threading.Lock()
task_counter = itertools.count(1)

@app.get("/api/tasks", response_model=List[Task])
def get_tasks():
    """Get tasks, newest first"""
    with tasks_lock:
        return list(reversed(tasks))

@app.post("/api/tasks", response_model=Task)
def create_task(request: CreateTaskRequest):
    """Create a new pending task"""
    with tasks_lock:
        if len(tasks) >= MAX_STORED_RECORDS:
            raise HTTPException(status_code=429, detail="Task limit reached")
        task = {
            "id": f"task-{next(task_counter)}-{int(datetime.now().timestamp() * 1000)}",
            "title": request.title,
            "priority": request.priority,
            "dueDate": request.dueDate.isoformat(),
            "status": "pending",
        }
        tasks.append(task)
        return task

@app.delete("/api/tasks/{task_id}", response_model=Task)
def delete_task(task_id: str):
    """Delete a task and return the removed task"""
    with tasks_lock:
        for i, task in enumerate(tasks):
            if task["id"] == task_id:
                return tasks.pop(i)
    raise HTTPException(status_code=404, detail="Task not found")

@app.patch("/api/tasks/{task_id}", response_model=Task)
def toggle_task(task_id: str):
    """Toggle a task between pending and completed"""
    with tasks_lock:
        for task in tasks:
            if task["id"] == task_id:
                task["status"] = "completed" if task["status"] == "pending" else "pending"
                return task
    raise HTTPException(status_code=404, detail="Task not found")

def _po_number(po: dict) -> int:
    match = re.fullmatch(r"PO-(\d+)", po["id"])
    return int(match.group(1)) if match else 0

@app.post("/api/purchase-orders", response_model=PurchaseOrder)
def create_purchase_order(request: CreatePurchaseOrderRequest):
    """Create a purchase order for a backlog item (one per item)"""
    if request.backlog_item_id not in backlog_ids:
        raise HTTPException(status_code=404, detail="Backlog item not found")
    if request.quantity <= 0 or request.unit_cost < 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive and unit cost non-negative")
    with purchase_order_lock:
        if len(purchase_orders) >= MAX_STORED_RECORDS:
            raise HTTPException(status_code=429, detail="Purchase order limit reached")
        if any(po["backlog_item_id"] == request.backlog_item_id for po in purchase_orders):
            raise HTTPException(status_code=409, detail="Purchase order already exists for this backlog item")
        po = {
            "id": f"PO-{max((_po_number(p) for p in purchase_orders), default=0) + 1:04d}",
            "backlog_item_id": request.backlog_item_id,
            "supplier_name": request.supplier_name,
            "quantity": request.quantity,
            "unit_cost": request.unit_cost,
            "expected_delivery_date": request.expected_delivery_date.isoformat(),
            "status": "pending",
            "created_date": date.today().isoformat(),
            "notes": request.notes,
        }
        purchase_orders.append(po)
        return po

@app.get("/api/purchase-orders/{backlog_item_id}", response_model=PurchaseOrder)
def get_purchase_order(backlog_item_id: str):
    """Get the purchase order for a backlog item"""
    with purchase_order_lock:
        for po in purchase_orders:
            if po["backlog_item_id"] == backlog_item_id:
                return po
    raise HTTPException(status_code=404, detail="Purchase order not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.environ.get("HOST", "127.0.0.1"), port=8001)
