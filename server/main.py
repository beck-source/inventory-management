import os
import random
import re
from datetime import datetime, timedelta
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders

app = FastAPI(title="Factory Inventory Management System")

# In-memory store for restocking orders submitted from the Restocking tab
restock_orders: List[dict] = []

# Tasks created via the Tasks modal are backed by GitHub Issues on this repo,
# rather than an in-memory store, so they persist and are visible outside the demo.
GITHUB_API_BASE = "https://api.github.com"
TASKS_REPO_OWNER = "dWhisper"
TASKS_REPO_NAME = "inventory-management"
TASKS_LABEL = "task"
TASKS_COMPLETED_LABEL = "task-completed"
TASKS_DUE_DATE_RE = re.compile(r"Due:\s*(\d{4}-\d{2}-\d{2})")

def _github_headers() -> dict:
    """Auth headers for the GitHub REST API, read from the environment at request time."""
    token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
    if not token:
        raise HTTPException(status_code=500, detail="GITHUB_PERSONAL_ACCESS_TOKEN is not set on the server")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

def _issue_to_task(issue: dict) -> dict:
    """Map a GitHub issue onto the Task shape the Tasks modal expects."""
    label_names = [label["name"] for label in issue.get("labels", [])]
    priority = "medium"
    for name in label_names:
        if name.startswith("priority:"):
            priority = name.split(":", 1)[1]
            break

    match = TASKS_DUE_DATE_RE.search(issue.get("body") or "")
    due_date = match.group(1) if match else issue["created_at"][:10]

    return {
        "id": str(issue["number"]),
        "title": issue["title"],
        "priority": priority,
        "dueDate": due_date,
        "status": "completed" if TASKS_COMPLETED_LABEL in label_names else "pending",
    }

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
    unit_cost: float

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

class RestockOrderItemRequest(BaseModel):
    item_sku: str
    item_name: str
    quantity: int
    unit_cost: float

class CreateRestockOrderRequest(BaseModel):
    budget: float
    items: List[RestockOrderItemRequest]

class RestockOrderItem(BaseModel):
    item_sku: str
    item_name: str
    quantity: int
    unit_cost: float
    subtotal: float

class RestockOrder(BaseModel):
    id: str
    order_number: str
    items: List[RestockOrderItem]
    budget: float
    total_cost: float
    status: str
    order_date: str
    lead_time_days: int
    expected_delivery: str

class Task(BaseModel):
    id: str
    title: str
    priority: str
    dueDate: str
    status: str

class CreateTaskRequest(BaseModel):
    title: str
    priority: str
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

@app.get("/api/restock-orders", response_model=List[RestockOrder])
def get_restock_orders():
    """Get all submitted restocking orders"""
    return restock_orders

@app.post("/api/restock-orders", response_model=RestockOrder)
def create_restock_order(request: CreateRestockOrderRequest):
    """Submit a restocking order built from demand forecast recommendations"""
    if not request.items:
        raise HTTPException(status_code=400, detail="Restocking order must include at least one item")

    order_items = []
    total_cost = 0.0
    for item in request.items:
        subtotal = round(item.quantity * item.unit_cost, 2)
        total_cost += subtotal
        order_items.append({
            "item_sku": item.item_sku,
            "item_name": item.item_name,
            "quantity": item.quantity,
            "unit_cost": item.unit_cost,
            "subtotal": subtotal
        })

    order_date = datetime.now()
    lead_time_days = random.randint(3, 14)
    expected_delivery = order_date + timedelta(days=lead_time_days)

    new_order = {
        "id": str(len(restock_orders) + 1),
        "order_number": f"RSK-{order_date.strftime('%Y%m%d')}-{len(restock_orders) + 1:03d}",
        "items": order_items,
        "budget": request.budget,
        "total_cost": round(total_cost, 2),
        "status": "Ordered",
        "order_date": order_date.isoformat(),
        "lead_time_days": lead_time_days,
        "expected_delivery": expected_delivery.isoformat()
    }
    restock_orders.append(new_order)
    return new_order

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

@app.get("/api/tasks", response_model=List[Task])
async def get_tasks():
    """Get all open tasks, backed by GitHub Issues labeled 'task' on this repo"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/repos/{TASKS_REPO_OWNER}/{TASKS_REPO_NAME}/issues",
            headers=_github_headers(),
            params={"labels": TASKS_LABEL, "state": "open", "per_page": 100},
        )
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to fetch tasks from GitHub")
    return [_issue_to_task(issue) for issue in response.json()]

@app.post("/api/tasks", response_model=Task)
async def create_task(request: CreateTaskRequest):
    """Create a task by opening a GitHub issue"""
    body = f"Due: {request.dueDate}\n\nCreated via the Tasks modal in the Factory Inventory Management demo."
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GITHUB_API_BASE}/repos/{TASKS_REPO_OWNER}/{TASKS_REPO_NAME}/issues",
            headers=_github_headers(),
            json={
                "title": request.title,
                "body": body,
                "labels": [TASKS_LABEL, f"priority:{request.priority}"],
            },
        )
    if response.status_code != 201:
        raise HTTPException(status_code=502, detail="Failed to create task on GitHub")
    return _issue_to_task(response.json())

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a task by closing its GitHub issue (as not planned)"""
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{GITHUB_API_BASE}/repos/{TASKS_REPO_OWNER}/{TASKS_REPO_NAME}/issues/{task_id}",
            headers=_github_headers(),
            json={"state": "closed", "state_reason": "not_planned"},
        )
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Task not found")
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to delete task on GitHub")
    return {"message": "Task deleted"}

@app.patch("/api/tasks/{task_id}", response_model=Task)
async def toggle_task(task_id: str):
    """Toggle a task's completion status by adding/removing the completed label"""
    async with httpx.AsyncClient() as client:
        get_response = await client.get(
            f"{GITHUB_API_BASE}/repos/{TASKS_REPO_OWNER}/{TASKS_REPO_NAME}/issues/{task_id}",
            headers=_github_headers(),
        )
        if get_response.status_code == 404:
            raise HTTPException(status_code=404, detail="Task not found")
        if get_response.status_code != 200:
            raise HTTPException(status_code=502, detail="Failed to fetch task from GitHub")

        label_names = [label["name"] for label in get_response.json().get("labels", [])]
        if TASKS_COMPLETED_LABEL in label_names:
            new_labels = [name for name in label_names if name != TASKS_COMPLETED_LABEL]
        else:
            new_labels = label_names + [TASKS_COMPLETED_LABEL]

        patch_response = await client.patch(
            f"{GITHUB_API_BASE}/repos/{TASKS_REPO_OWNER}/{TASKS_REPO_NAME}/issues/{task_id}",
            headers=_github_headers(),
            json={"labels": new_labels},
        )
    if patch_response.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to update task on GitHub")
    return _issue_to_task(patch_response.json())

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
def get_quarterly_reports(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None
):
    """Get quarterly performance reports"""
    # Calculate quarterly statistics from orders
    filtered_orders = apply_filters(orders, warehouse, category, status)
    quarters = {}

    for order in filtered_orders:
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
def get_monthly_trends(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None
):
    """Get month-over-month trends"""
    filtered_orders = apply_filters(orders, warehouse, category, status)
    months = {}

    for order in filtered_orders:
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
