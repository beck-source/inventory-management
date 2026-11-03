import math
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel, Field
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders, restocking_orders


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
    unit_cost: float
    lead_time_days: int

class RestockRecommendation(BaseModel):
    sku: str
    name: str
    quantity: int
    unit_cost: float
    line_total: float
    lead_time_days: int
    trend: str
    demand_gap: int

class RecommendationResponse(BaseModel):
    budget: float
    total_cost: float
    remaining_budget: float
    max_budget: float
    items: List[RestockRecommendation]

class RestockOrderRequest(BaseModel):
    budget: float = Field(gt=0)

class RestockOrder(BaseModel):
    id: str
    order_number: str
    items: List[RestockRecommendation]
    total_cost: float
    budget: float
    status: str
    created_at: str
    lead_time_days: int
    expected_delivery: str

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
    # Dashboard.vue keys its Create PO / View PO button off this field
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
        po = next((p for p in purchase_orders if p["backlog_item_id"] == item["id"]), None)
        item_dict["has_purchase_order"] = po is not None
        item_dict["purchase_order_id"] = po["id"] if po else None
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

def build_restock_recommendations(budget: float) -> dict:
    """Pick forecast items to restock within a budget using a priority-greedy fill.

    Rules:
    1. Only items whose forecasted demand exceeds current demand are candidates;
       the gap (forecasted - current) is the quantity we want to restock.
    2. Items with an "increasing" trend come first, then the remaining candidates.
       Within each group, the item with the largest gap cost (gap * unit_cost) wins,
       so the biggest shortfalls are covered before small ones.
    3. Each item gets its full gap if the budget allows. The first item that does
       not fit gets as many whole units as the remaining budget can buy, which is
       why the loop keeps going: a cheaper later item may still fit partially.
    """
    candidates = []
    for f in demand_forecasts:
        gap = f['forecasted_demand'] - f['current_demand']
        if gap > 0:
            candidates.append((f, gap))

    candidates.sort(key=lambda c: (c[0]['trend'].lower() != 'increasing', -c[1] * c[0]['unit_cost']))

    # Cost of covering every gap; the frontend uses this as the slider maximum
    max_budget = round(sum(gap * f['unit_cost'] for f, gap in candidates), 2)

    remaining = budget
    items = []
    for f, gap in candidates:
        # Small epsilon guards against float rounding refusing an exact-fit unit
        quantity = min(gap, math.floor((remaining + 1e-9) / f['unit_cost']))
        if quantity <= 0:
            continue
        line_total = round(quantity * f['unit_cost'], 2)
        remaining = round(remaining - line_total, 2)
        items.append({
            'sku': f['item_sku'],
            'name': f['item_name'],
            'quantity': quantity,
            'unit_cost': f['unit_cost'],
            'line_total': line_total,
            'lead_time_days': f['lead_time_days'],
            'trend': f['trend'],
            'demand_gap': gap,
        })

    total_cost = round(sum(i['line_total'] for i in items), 2)
    return {
        'budget': budget,
        'total_cost': total_cost,
        'remaining_budget': round(budget - total_cost, 2),
        'max_budget': max_budget,
        'items': items,
    }

@app.get("/api/restocking/recommendations", response_model=RecommendationResponse)
def get_restock_recommendations(budget: float = Query(..., ge=0)):
    """Recommend forecast items to restock within the given budget"""
    return build_restock_recommendations(budget)

@app.get("/api/restocking/orders", response_model=List[RestockOrder])
def get_restock_orders():
    """Get submitted restocking orders, newest first"""
    return list(reversed(restocking_orders))

@app.post("/api/restocking/orders", response_model=RestockOrder, status_code=201)
def create_restock_order(request: RestockOrderRequest):
    """Submit a restocking order for the given budget.

    Line items are recomputed server-side from the budget rather than accepted
    from the client, so quantities and prices can't be tampered with.
    """
    recommendation = build_restock_recommendations(request.budget)
    if not recommendation['items']:
        raise HTTPException(status_code=400, detail="Budget is too small to restock any item")

    created_at = datetime.now().replace(microsecond=0)
    # The order arrives when its slowest item does
    lead_time_days = max(i['lead_time_days'] for i in recommendation['items'])
    sequence = len(restocking_orders) + 1
    order = {
        'id': str(sequence),
        'order_number': f"RST-{created_at.year}-{sequence:04d}",
        'items': recommendation['items'],
        'total_cost': recommendation['total_cost'],
        'budget': request.budget,
        'status': 'Submitted',
        'created_at': created_at.isoformat(),
        'lead_time_days': lead_time_days,
        'expected_delivery': (created_at + timedelta(days=lead_time_days)).isoformat(),
    }
    restocking_orders.append(order)
    return order

# --- Purchase orders (created from the dashboard's Inventory Shortages table) ---

@app.post("/api/purchase-orders", response_model=PurchaseOrder, status_code=201)
def create_purchase_order(request: CreatePurchaseOrderRequest):
    """Create a purchase order for a backlog item (one PO per backlog item)"""
    if not any(b["id"] == request.backlog_item_id for b in backlog_items):
        raise HTTPException(status_code=404, detail="Backlog item not found")
    if any(po["backlog_item_id"] == request.backlog_item_id for po in purchase_orders):
        raise HTTPException(status_code=409, detail="Backlog item already has a purchase order")

    po = {
        "id": f"PO-{len(purchase_orders) + 1:04d}",
        **request.model_dump(),
        "status": "pending",
        "created_date": datetime.now().replace(microsecond=0).isoformat(),
    }
    purchase_orders.append(po)
    return po

@app.get("/api/purchase-orders/{backlog_item_id}", response_model=PurchaseOrder)
def get_purchase_order_by_backlog_item(backlog_item_id: str):
    """Look up a purchase order by the backlog item it was created for"""
    po = next((p for p in purchase_orders if p["backlog_item_id"] == backlog_item_id), None)
    if po is None:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return po

# --- Tasks (user to-do list in the profile menu; in-memory, reset on restart) ---

class Task(BaseModel):
    id: str
    title: str
    priority: str
    dueDate: str
    status: str

class CreateTaskRequest(BaseModel):
    title: str = Field(..., min_length=1)
    priority: str = Field("medium", pattern="^(high|medium|low)$")
    dueDate: str

tasks: List[dict] = []
_task_seq = 0

@app.get("/api/tasks", response_model=List[Task])
def get_tasks():
    """Get user-created tasks, newest first"""
    return list(reversed(tasks))

@app.post("/api/tasks", response_model=Task, status_code=201)
def create_task(request: CreateTaskRequest):
    """Create a pending task"""
    global _task_seq
    _task_seq += 1
    # String IDs ("task-N") so they never collide with the numeric IDs of the
    # client-side mock tasks in useAuth.js, which App.vue merges into the same list.
    task = {"id": f"task-{_task_seq}", **request.model_dump(), "status": "pending"}
    tasks.append(task)
    return task

def _find_task(task_id: str) -> dict:
    task = next((t for t in tasks if t["id"] == task_id), None)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.patch("/api/tasks/{task_id}", response_model=Task)
def toggle_task(task_id: str):
    """Toggle a task between pending and completed"""
    task = _find_task(task_id)
    task["status"] = "completed" if task["status"] == "pending" else "pending"
    return task

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str):
    """Delete a task"""
    tasks.remove(_find_task(task_id))
    return {"deleted": task_id}

if __name__ == "__main__":
    import uvicorn
    # client/src/api.js hardcodes API_BASE_URL to localhost:8001; change both together
    port = 8001
    print(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
