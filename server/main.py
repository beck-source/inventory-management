import random
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders, tasks

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
    lead_time_days: Optional[int] = None

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
    # Dashboard.vue keys the Create PO / View PO button off purchase_order_id,
    # so it must survive a page reload rather than only being set client-side
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

class Task(BaseModel):
    # Field names are camelCase to match the client task shape used by
    # TasksModal.vue and the mock tasks in composables/useAuth.js
    id: str
    title: str
    priority: str
    dueDate: str
    status: str

class CreateTaskRequest(BaseModel):
    title: str
    priority: str
    dueDate: str

class RestockOrderItem(BaseModel):
    sku: str
    name: str
    quantity: int
    unit_cost: float

class RestockOrderRequest(BaseModel):
    items: List[RestockOrderItem]
    budget: float

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

@app.post("/api/restock-orders", response_model=Order)
def create_restock_order(request: RestockOrderRequest):
    """Submit a restocking order built from budget-based recommendations"""
    if not request.items:
        raise HTTPException(status_code=400, detail="Restock order must include at least one item")

    order_date = datetime.now()
    lead_time_days = random.randint(7, 14)
    expected_delivery = order_date + timedelta(days=lead_time_days)
    total_value = sum(item.quantity * item.unit_cost for item in request.items)

    new_order = {
        "id": str(len(orders) + 1),
        "order_number": f"RESTOCK-{str(len(orders) + 1).zfill(4)}",
        "customer": "Internal Restocking",
        "items": [
            {
                "sku": item.sku,
                "name": item.name,
                "quantity": item.quantity,
                "unit_price": item.unit_cost
            }
            for item in request.items
        ],
        "status": "Processing",
        "order_date": order_date.isoformat(),
        "expected_delivery": expected_delivery.isoformat(),
        "total_value": round(total_value, 2),
        "actual_delivery": None,
        "warehouse": None,
        "category": None,
        "source": "restocking",
        "lead_time_days": lead_time_days
    }

    orders.append(new_order)
    return new_order

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
        existing_po = next((po for po in purchase_orders if po["backlog_item_id"] == item["id"]), None)
        item_dict["has_purchase_order"] = existing_po is not None
        # Expose the PO id too, so the dashboard button state is correct on reload
        item_dict["purchase_order_id"] = existing_po["id"] if existing_po else None
        result.append(item_dict)
    return result

@app.post("/api/purchase-orders", response_model=PurchaseOrder)
def create_purchase_order(request: CreatePurchaseOrderRequest):
    """Create a purchase order to cover a backlog item shortage"""
    backlog_item = next((item for item in backlog_items if item["id"] == request.backlog_item_id), None)
    if not backlog_item:
        raise HTTPException(
            status_code=404,
            detail=f"Backlog item {request.backlog_item_id} not found"
        )

    if request.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than zero")

    if request.unit_cost < 0:
        raise HTTPException(status_code=400, detail="Unit cost cannot be negative")

    # One PO per backlog item - the dashboard shows either Create PO or View PO, never both
    if any(po["backlog_item_id"] == request.backlog_item_id for po in purchase_orders):
        raise HTTPException(
            status_code=400,
            detail=f"Backlog item {request.backlog_item_id} already has a purchase order"
        )

    new_po = {
        "id": f"PO-{str(len(purchase_orders) + 1).zfill(4)}",
        "backlog_item_id": request.backlog_item_id,
        "supplier_name": request.supplier_name,
        "quantity": request.quantity,
        "unit_cost": request.unit_cost,
        "expected_delivery_date": request.expected_delivery_date,
        "status": "Pending",
        "created_date": datetime.now().strftime("%Y-%m-%d"),
        "notes": request.notes
    }

    purchase_orders.append(new_po)
    return new_po

@app.get("/api/purchase-orders/{backlog_item_id}", response_model=PurchaseOrder)
def get_purchase_order_by_backlog_item(backlog_item_id: str):
    """Get the purchase order associated with a backlog item"""
    po = next((po for po in purchase_orders if po["backlog_item_id"] == backlog_item_id), None)
    if not po:
        raise HTTPException(
            status_code=404,
            detail=f"No purchase order found for backlog item {backlog_item_id}"
        )
    return po

@app.get("/api/tasks", response_model=List[Task])
def get_tasks():
    """Get user-created tasks"""
    return tasks

@app.post("/api/tasks", response_model=Task)
def create_task(request: CreateTaskRequest):
    """Create a task"""
    if not request.title.strip():
        raise HTTPException(status_code=400, detail="Task title cannot be empty")

    if request.priority not in ("high", "medium", "low"):
        raise HTTPException(
            status_code=400,
            detail="Priority must be one of: high, medium, low"
        )

    # String ids keep API tasks distinct from the integer-keyed mock tasks in
    # useAuth.js, which App.vue matches on before falling back to the API.
    # Derived from the highest existing suffix rather than len(tasks) so that
    # deleting a task can never cause the next create to reuse a live id.
    existing_numbers = [
        int(t["id"].rsplit("-", 1)[-1])
        for t in tasks
        if t["id"].rsplit("-", 1)[-1].isdigit()
    ]
    next_number = max(existing_numbers, default=0) + 1

    new_task = {
        "id": f"task-{next_number}",
        "title": request.title.strip(),
        "priority": request.priority,
        "dueDate": request.dueDate,
        "status": "pending"
    }

    tasks.append(new_task)
    return new_task

@app.patch("/api/tasks/{task_id}", response_model=Task)
def toggle_task(task_id: str):
    """Toggle a task between pending and completed"""
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    task["status"] = "completed" if task["status"] == "pending" else "pending"
    return task

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str):
    """Delete a task"""
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    tasks.remove(task)
    return {"id": task_id, "deleted": True}

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
