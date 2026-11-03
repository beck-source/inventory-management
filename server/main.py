from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
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
    source: Optional[str] = None

class DemandForecast(BaseModel):
    id: str
    item_sku: str
    item_name: str
    current_demand: int
    forecasted_demand: int
    trend: str
    period: str
    unit_cost: Optional[float] = None

class RestockingOrderItem(BaseModel):
    sku: str
    name: str
    quantity: int
    unit_price: float

class CreateRestockingOrderRequest(BaseModel):
    warehouse: str
    items: List[RestockingOrderItem]

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

# Restocking
# Fixed supplier lead time per warehouse, in days
RESTOCKING_LEAD_TIME_DAYS = {
    'San Francisco': 14,
    'London': 21,
    'Tokyo': 18
}

def _unit_cost_for_sku(sku: str) -> Optional[float]:
    """Return the unit cost for a SKU from the demand forecast data."""
    match = next((f for f in demand_forecasts if f["item_sku"] == sku), None)
    return match.get("unit_cost") if match else None

@app.get("/api/restocking/recommendations")
def get_restocking_recommendations(warehouse: str, budget: float):
    """
    Recommend demand-forecast items to restock at a warehouse within a budget.

    Items are ranked by shortfall (forecasted demand minus quantity on hand at
    that warehouse). Each item is filled greedily, in ranked order, with as many
    units as the remaining budget allows, up to its shortfall.
    """
    if warehouse not in RESTOCKING_LEAD_TIME_DAYS:
        raise HTTPException(status_code=400, detail=f"Unknown warehouse: {warehouse}")
    if budget < 0:
        raise HTTPException(status_code=400, detail="Budget must be zero or greater")

    candidates = []
    for forecast in demand_forecasts:
        unit_cost = forecast.get("unit_cost")
        if not unit_cost or unit_cost <= 0:
            continue
        on_hand = sum(
            item["quantity_on_hand"]
            for item in inventory_items
            if item["sku"] == forecast["item_sku"] and item["warehouse"] == warehouse
        )
        shortfall = forecast["forecasted_demand"] - on_hand
        if shortfall > 0:
            candidates.append({
                "sku": forecast["item_sku"],
                "name": forecast["item_name"],
                "forecasted_demand": forecast["forecasted_demand"],
                "current_stock": on_hand,
                "shortfall": shortfall,
                "unit_cost": unit_cost,
            })

    candidates.sort(key=lambda c: (-c["shortfall"], c["sku"]))

    remaining = budget
    recommendations = []
    for candidate in candidates:
        affordable = int(remaining // candidate["unit_cost"])
        quantity = min(candidate["shortfall"], affordable)
        if quantity <= 0:
            continue
        line_total = round(quantity * candidate["unit_cost"], 2)
        remaining = round(remaining - line_total, 2)
        recommendations.append({
            **candidate,
            "recommended_quantity": quantity,
            "line_total": line_total,
        })

    total_cost = round(sum(r["line_total"] for r in recommendations), 2)
    return {
        "warehouse": warehouse,
        "budget": budget,
        "lead_time_days": RESTOCKING_LEAD_TIME_DAYS[warehouse],
        "items": recommendations,
        "total_cost": total_cost,
        "remaining_budget": round(budget - total_cost, 2),
    }

@app.post("/api/restocking/orders", response_model=Order, status_code=201)
def create_restocking_order(request: CreateRestockingOrderRequest):
    """Submit a restocking order. It is appended to the in-memory orders list."""
    if request.warehouse not in RESTOCKING_LEAD_TIME_DAYS:
        raise HTTPException(status_code=400, detail=f"Unknown warehouse: {request.warehouse}")
    if not request.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")
    if any(item.quantity <= 0 or item.unit_price < 0 for item in request.items):
        raise HTTPException(status_code=400, detail="Quantities must be positive and prices non-negative")

    now = datetime.now().replace(microsecond=0)
    lead_days = RESTOCKING_LEAD_TIME_DAYS[request.warehouse]
    next_id = max((int(o["id"]) for o in orders), default=0) + 1

    order = {
        "id": str(next_id),
        "order_number": f"RST-{now.year}-{next_id:04d}",
        "customer": "Internal Restocking",
        "items": [item.model_dump() for item in request.items],
        "status": "Processing",
        "warehouse": request.warehouse,
        "category": "Restocking",
        "order_date": now.isoformat(),
        "expected_delivery": (now + timedelta(days=lead_days)).isoformat(),
        "total_value": round(sum(i.quantity * i.unit_price for i in request.items), 2),
        "actual_delivery": None,
        "source": "restocking",
    }
    orders.append(order)
    return order

# Tasks (in-memory; resets on server restart)
class TaskItem(BaseModel):
    id: int
    title: str
    priority: str = "medium"
    dueDate: Optional[str] = None
    status: str = "pending"

class CreateTaskRequest(BaseModel):
    title: str
    priority: str = "medium"
    dueDate: Optional[str] = None

tasks_store: List[dict] = []
_next_task_id = 1000

@app.get("/api/tasks", response_model=List[TaskItem])
def get_tasks():
    return tasks_store

@app.post("/api/tasks", response_model=TaskItem, status_code=201)
def create_task(request: CreateTaskRequest):
    global _next_task_id
    _next_task_id += 1
    task = {"id": _next_task_id, "title": request.title, "priority": request.priority,
            "dueDate": request.dueDate, "status": "pending"}
    tasks_store.insert(0, task)
    return task

@app.patch("/api/tasks/{task_id}", response_model=TaskItem)
def toggle_task(task_id: int):
    task = next((t for t in tasks_store if t["id"] == task_id), None)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    task["status"] = "completed" if task["status"] == "pending" else "pending"
    return task

@app.delete("/api/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    global tasks_store
    remaining = [t for t in tasks_store if t["id"] != task_id]
    if len(remaining) == len(tasks_store):
        raise HTTPException(status_code=404, detail="Task not found")
    tasks_store = remaining

# Purchase orders (one PO per backlog item)
@app.get("/api/purchase-orders/{backlog_item_id}", response_model=PurchaseOrder)
def get_purchase_order(backlog_item_id: str):
    po = next((p for p in purchase_orders if p["backlog_item_id"] == backlog_item_id), None)
    if po is None:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return po

@app.post("/api/purchase-orders", response_model=PurchaseOrder, status_code=201)
def create_purchase_order(request: CreatePurchaseOrderRequest):
    if any(p["backlog_item_id"] == request.backlog_item_id for p in purchase_orders):
        raise HTTPException(status_code=409, detail="A purchase order already exists for this backlog item")
    if request.quantity <= 0 or request.unit_cost < 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive and unit cost non-negative")
    next_id = max((int(p["id"].split("-")[-1]) for p in purchase_orders), default=0) + 1
    now = datetime.now()
    po = {
        "id": f"PO-{now.year}-{next_id:04d}",
        "backlog_item_id": request.backlog_item_id,
        "supplier_name": request.supplier_name,
        "quantity": request.quantity,
        "unit_cost": request.unit_cost,
        "expected_delivery_date": request.expected_delivery_date,
        "status": "Open",
        "created_date": now.date().isoformat(),
        "notes": request.notes,
    }
    purchase_orders.append(po)
    return po


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
