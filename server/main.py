from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Literal, Optional
from pydantic import BaseModel, Field
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
    lead_time_days: Optional[int] = None

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

MAX_RESTOCK_BUDGET = 10_000_000
MAX_RESTOCK_QUANTITY = 100_000

class RestockRecommendation(BaseModel):
    item_sku: str
    item_name: str
    trend: str
    forecasted_demand: int
    quantity_on_hand: int
    quantity_on_order: int
    shortfall: int
    recommended_quantity: int
    unit_cost: float
    line_total: float
    lead_time_days: int
    partial: bool

class RestockRecommendationResponse(BaseModel):
    budget: float
    total_cost: float
    remaining_budget: float
    full_restock_cost: float
    items: List[RestockRecommendation]

class RestockOrderLine(BaseModel):
    item_sku: str
    quantity: int = Field(gt=0, le=MAX_RESTOCK_QUANTITY)

class CreateRestockOrderRequest(BaseModel):
    budget: float = Field(gt=0, le=MAX_RESTOCK_BUDGET)
    items: List[RestockOrderLine] = Field(min_length=1)

class RestockOrderItem(BaseModel):
    item_sku: str
    item_name: str
    quantity: int
    unit_cost: float
    line_total: float
    lead_time_days: int

class RestockOrder(BaseModel):
    id: str
    order_number: str
    items: List[RestockOrderItem]
    total_value: float
    budget: float
    status: str
    submitted_date: str
    lead_time_days: int
    expected_delivery: str

class CreateTaskRequest(BaseModel):
    title: str = Field(min_length=1)
    priority: Literal['high', 'medium', 'low'] = 'medium'
    dueDate: str

class Task(BaseModel):
    id: str
    title: str
    priority: str
    dueDate: str
    status: str

# Restocking orders submitted this session (in memory; reset on server restart)
restock_orders: List[dict] = []

# User tasks created this session (in memory; reset on server restart)
tasks: List[dict] = []
next_task_id = 1

TREND_PRIORITY = {'increasing': 0, 'stable': 1, 'decreasing': 2}

def get_on_hand_quantity(sku: str) -> int:
    """Total quantity on hand for a SKU across all warehouses (0 if not stocked)"""
    return sum(item['quantity_on_hand'] for item in inventory_items if item['sku'] == sku)

def get_on_order_quantity(sku: str) -> int:
    """Total quantity of a SKU in restocking orders submitted this session"""
    return sum(line['quantity'] for order in restock_orders for line in order['items'] if line['item_sku'] == sku)

def get_restock_candidates() -> list:
    """Demand forecast items whose forecasted demand exceeds stock on hand plus stock on order, highest priority first"""
    candidates = []
    for forecast in demand_forecasts:
        if forecast.get('unit_cost') is None or forecast.get('lead_time_days') is None:
            continue
        on_hand = get_on_hand_quantity(forecast['item_sku'])
        on_order = get_on_order_quantity(forecast['item_sku'])
        shortfall = forecast['forecasted_demand'] - on_hand - on_order
        if shortfall <= 0:
            continue
        candidates.append({**forecast, 'quantity_on_hand': on_hand, 'quantity_on_order': on_order, 'shortfall': shortfall})
    candidates.sort(key=lambda c: (TREND_PRIORITY.get(c['trend'], 3), -c['shortfall'] * c['unit_cost']))
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

@app.get("/api/restocking/recommendations", response_model=RestockRecommendationResponse)
def get_restocking_recommendations(budget: float = Query(gt=0, le=MAX_RESTOCK_BUDGET)):
    """Recommend demand forecast items to restock, filling the budget in priority order"""
    candidates = get_restock_candidates()
    remaining = budget
    items = []
    for c in candidates:
        affordable = int(remaining // c['unit_cost'])
        quantity = min(c['shortfall'], affordable)
        if quantity <= 0:
            continue
        line_total = round(quantity * c['unit_cost'], 2)
        remaining = round(remaining - line_total, 2)
        items.append({
            'item_sku': c['item_sku'],
            'item_name': c['item_name'],
            'trend': c['trend'],
            'forecasted_demand': c['forecasted_demand'],
            'quantity_on_hand': c['quantity_on_hand'],
            'quantity_on_order': c['quantity_on_order'],
            'shortfall': c['shortfall'],
            'recommended_quantity': quantity,
            'unit_cost': c['unit_cost'],
            'line_total': line_total,
            'lead_time_days': c['lead_time_days'],
            'partial': quantity < c['shortfall'],
        })
    total_cost = round(sum(i['line_total'] for i in items), 2)
    return {
        'budget': budget,
        'total_cost': total_cost,
        'remaining_budget': round(budget - total_cost, 2),
        'full_restock_cost': round(sum(c['shortfall'] * c['unit_cost'] for c in candidates), 2),
        'items': items,
    }

@app.get("/api/restocking/orders", response_model=List[RestockOrder])
def get_restocking_orders():
    """Get submitted restocking orders, newest first"""
    return list(reversed(restock_orders))

@app.post("/api/restocking/orders", response_model=RestockOrder, status_code=201)
def create_restocking_order(request: CreateRestockOrderRequest):
    """Submit a restocking order; prices and lead times come from the demand forecast, not the client"""
    forecasts_by_sku = {f['item_sku']: f for f in demand_forecasts}
    seen = set()
    items = []
    for line in request.items:
        if line.item_sku in seen:
            raise HTTPException(status_code=400, detail=f"Duplicate item {line.item_sku} in order")
        seen.add(line.item_sku)
        forecast = forecasts_by_sku.get(line.item_sku)
        if not forecast or forecast.get('unit_cost') is None or forecast.get('lead_time_days') is None:
            raise HTTPException(status_code=400, detail=f"Item {line.item_sku} is not available for restocking")
        items.append({
            'item_sku': forecast['item_sku'],
            'item_name': forecast['item_name'],
            'quantity': line.quantity,
            'unit_cost': forecast['unit_cost'],
            'line_total': round(line.quantity * forecast['unit_cost'], 2),
            'lead_time_days': forecast['lead_time_days'],
        })

    total_value = round(sum(i['line_total'] for i in items), 2)
    if total_value > request.budget:
        raise HTTPException(status_code=400, detail=f"Order total {total_value} exceeds budget {request.budget}")

    submitted = datetime.now().replace(microsecond=0)
    lead_time_days = max(i['lead_time_days'] for i in items)
    order_id = str(len(restock_orders) + 1)
    order = {
        'id': order_id,
        'order_number': f"RST-{submitted.year}-{order_id.zfill(4)}",
        'items': items,
        'total_value': total_value,
        'budget': request.budget,
        'status': 'Submitted',
        'submitted_date': submitted.isoformat(),
        'lead_time_days': lead_time_days,
        'expected_delivery': (submitted + timedelta(days=lead_time_days)).isoformat(),
    }
    restock_orders.append(order)
    return order

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

def parse_order_month(order_date: str) -> Optional[tuple]:
    """Return (year, month) from a YYYY-MM-DD order_date, or None if malformed"""
    try:
        parsed = datetime.strptime(order_date[:7], '%Y-%m')
    except (TypeError, ValueError):
        return None
    return parsed.year, parsed.month

@app.get("/api/reports/quarterly")
def get_quarterly_reports(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get quarterly performance reports with optional filtering"""
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)

    # Calculate quarterly statistics from orders
    quarters = {}

    for order in filtered_orders:
        parsed = parse_order_month(order.get('order_date', ''))
        if not parsed:
            continue
        year, order_month = parsed
        quarter = f"Q{(order_month - 1) // 3 + 1}-{year}"

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

    # Sort chronologically (year, then quarter number)
    result.sort(key=lambda x: (x['quarter'][3:], x['quarter'][:2]))
    return result

@app.get("/api/reports/monthly-trends")
def get_monthly_trends(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get month-over-month trends with optional filtering"""
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)

    months = {}

    for order in filtered_orders:
        parsed = parse_order_month(order.get('order_date', ''))
        if not parsed:
            continue
        year, order_month = parsed
        month_key = f"{year}-{order_month:02d}"

        if month_key not in months:
            months[month_key] = {
                'month': month_key,
                'order_count': 0,
                'revenue': 0,
                'delivered_count': 0
            }

        months[month_key]['order_count'] += 1
        months[month_key]['revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            months[month_key]['delivered_count'] += 1

    # Convert to list and sort
    result = list(months.values())
    result.sort(key=lambda x: x['month'])
    return result

def find_task(task_id: str) -> dict:
    task = next((t for t in tasks if t['id'] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task

@app.get("/api/tasks", response_model=List[Task])
def get_tasks():
    """Get tasks created this session, newest first"""
    return list(reversed(tasks))

@app.post("/api/tasks", response_model=Task, status_code=201)
def create_task(request: CreateTaskRequest):
    """Create a pending task"""
    global next_task_id
    title = request.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Task title cannot be blank")
    try:
        datetime.strptime(request.dueDate, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="dueDate must be YYYY-MM-DD")
    task = {
        'id': f"task-{next_task_id}",
        'title': title,
        'priority': request.priority,
        'dueDate': request.dueDate,
        'status': 'pending',
    }
    next_task_id += 1
    tasks.append(task)
    return task

@app.patch("/api/tasks/{task_id}", response_model=Task)
def toggle_task(task_id: str):
    """Toggle a task between pending and completed"""
    task = find_task(task_id)
    task['status'] = 'completed' if task['status'] == 'pending' else 'pending'
    return task

@app.delete("/api/tasks/{task_id}", response_model=Task)
def delete_task(task_id: str):
    """Delete a task and return it"""
    task = find_task(task_id)
    tasks.remove(task)
    return task

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
