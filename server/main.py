from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders
import uuid
from datetime import datetime, timedelta

# In-memory store for submitted restocking orders
restocking_orders: list = []

# In-memory store for user-created tasks (resets on server restart)
tasks_store: list = []

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

class Task(BaseModel):
    id: str
    title: str
    priority: str
    # camelCase to match the frontend task shape (TasksModal / useAuth)
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

# ─── Restocking models ────────────────────────────────────────────────────────

class RestockingRecommendation(BaseModel):
    sku: str
    item_name: str
    category: str
    warehouse: str
    current_demand: int
    forecasted_demand: int
    trend: str
    quantity_on_hand: int
    reorder_point: int
    recommended_quantity: int
    unit_cost: float
    total_cost: float
    priority: str   # "critical" | "high" | "medium"


class RestockingOrderItem(BaseModel):
    sku: str
    item_name: str
    quantity: int
    unit_cost: float


class CreateRestockingOrderRequest(BaseModel):
    items: List[RestockingOrderItem]


class RestockingOrder(BaseModel):
    id: str
    order_number: str
    items: List[RestockingOrderItem]
    total_cost: float
    order_date: str
    expected_delivery: str
    status: str
    lead_time_days: int


# ─── Restocking endpoints ──────────────────────────────────────────────────────

@app.get("/api/restocking/recommendations", response_model=List[RestockingRecommendation])
def get_restocking_recommendations():
    """Return prioritised restocking recommendations derived from inventory stock levels
    and demand-forecast trends."""
    demand_by_sku = {d["item_sku"]: d for d in demand_forecasts}

    PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2}
    recommendations = []

    for item in inventory_items:
        sku = item["sku"]
        qty = item["quantity_on_hand"]
        reorder = item["reorder_point"]
        unit_cost = item["unit_cost"]

        demand = demand_by_sku.get(sku)
        trend = demand["trend"] if demand else "stable"
        current_demand = demand["current_demand"] if demand else qty
        forecasted_demand = demand["forecasted_demand"] if demand else qty

        below_reorder = qty <= reorder
        near_reorder = qty <= reorder * 1.5

        # Determine priority – skip items that are well-stocked with no demand pressure
        if trend == "decreasing" and not below_reorder:
            continue
        if trend == "stable" and not near_reorder:
            continue

        if below_reorder and trend == "increasing":
            priority = "critical"
        elif below_reorder:
            priority = "high"
        elif near_reorder and trend == "increasing":
            priority = "high"
        elif trend == "increasing":
            priority = "medium"
        elif near_reorder:
            priority = "medium"
        else:
            continue

        # Recommended quantity: cover reorder buffer + forecast gap where available
        if trend == "increasing" and demand:
            base_qty = max(forecasted_demand - qty, reorder * 2 - qty)
        else:
            base_qty = reorder * 2 - qty

        recommended_quantity = max(int(base_qty), 10)
        total_cost = round(recommended_quantity * unit_cost, 2)

        recommendations.append({
            "sku": sku,
            "item_name": item["name"],
            "category": item["category"],
            "warehouse": item["warehouse"],
            "current_demand": current_demand,
            "forecasted_demand": forecasted_demand,
            "trend": trend,
            "quantity_on_hand": qty,
            "reorder_point": reorder,
            "recommended_quantity": recommended_quantity,
            "unit_cost": unit_cost,
            "total_cost": total_cost,
            "priority": priority,
        })

    recommendations.sort(key=lambda x: PRIORITY_ORDER.get(x["priority"], 3))
    return recommendations


@app.post("/api/restocking/orders", response_model=RestockingOrder)
def create_restocking_order(order: CreateRestockingOrderRequest):
    """Submit a restocking order. Lead time is fixed at 14 days."""
    if not order.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")

    now = datetime.utcnow()
    delivery = now + timedelta(days=14)
    total_cost = round(sum(i.unit_cost * i.quantity for i in order.items), 2)
    order_number = f"RST-{len(restocking_orders) + 1:04d}"

    new_order = {
        "id": str(uuid.uuid4())[:8],
        "order_number": order_number,
        "items": [i.model_dump() for i in order.items],
        "total_cost": total_cost,
        "order_date": now.strftime("%Y-%m-%dT%H:%M:%S"),
        "expected_delivery": delivery.strftime("%Y-%m-%dT%H:%M:%S"),
        "status": "Submitted",
        "lead_time_days": 14,
    }
    restocking_orders.append(new_order)
    return new_order


@app.get("/api/restocking/submitted-orders", response_model=List[RestockingOrder])
def get_submitted_restocking_orders():
    """Return all submitted restocking orders."""
    return list(reversed(restocking_orders))


# ─── Task endpoints ─────────────────────────────────────────────────────────

@app.get("/api/tasks", response_model=List[Task])
def get_tasks():
    """Return user-created tasks (newest first). Stored in memory only."""
    return list(reversed(tasks_store))


@app.post("/api/tasks", response_model=Task)
def create_task(task: CreateTaskRequest):
    """Create a new task. New tasks always start with status 'pending'."""
    new_task = {
        "id": str(uuid.uuid4())[:8],
        "title": task.title,
        "priority": task.priority,
        "dueDate": task.dueDate,
        "status": "pending",
    }
    tasks_store.append(new_task)
    return new_task


@app.patch("/api/tasks/{task_id}", response_model=Task)
def toggle_task(task_id: str):
    """Toggle a task between 'pending' and 'completed'."""
    task = next((t for t in tasks_store if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task["status"] = "completed" if task["status"] == "pending" else "pending"
    return task


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str):
    """Delete a task by id."""
    task = next((t for t in tasks_store if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    tasks_store.remove(task)
    return {"success": True, "id": task_id}


# ─── Purchase order endpoints ───────────────────────────────────────────────

@app.post("/api/purchase-orders", response_model=PurchaseOrder)
def create_purchase_order(po: CreatePurchaseOrderRequest):
    """Create a purchase order for a backlog item."""
    backlog_item = next((b for b in backlog_items if b["id"] == po.backlog_item_id), None)
    if not backlog_item:
        raise HTTPException(status_code=404, detail="Backlog item not found")
    if any(existing["backlog_item_id"] == po.backlog_item_id for existing in purchase_orders):
        raise HTTPException(status_code=400, detail="A purchase order already exists for this backlog item")

    new_po = {
        "id": f"PO-{uuid.uuid4().hex[:8].upper()}",
        "backlog_item_id": po.backlog_item_id,
        "supplier_name": po.supplier_name,
        "quantity": po.quantity,
        "unit_cost": po.unit_cost,
        "expected_delivery_date": po.expected_delivery_date,
        "status": "Pending",
        "created_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "notes": po.notes,
    }
    purchase_orders.append(new_po)
    return new_po


@app.get("/api/purchase-orders/{backlog_item_id}", response_model=PurchaseOrder)
def get_purchase_order_by_backlog_item(backlog_item_id: str):
    """Return the purchase order associated with a backlog item, if one exists."""
    po = next((p for p in purchase_orders if p["backlog_item_id"] == backlog_item_id), None)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return po


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
