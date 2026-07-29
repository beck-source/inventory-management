import math
from datetime import datetime, timedelta, timezone
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
    lead_time_days: Optional[int] = None

class DemandForecast(BaseModel):
    id: str
    item_sku: str
    item_name: str
    current_demand: int
    forecasted_demand: int
    trend: str
    period: str
    unit_cost: Optional[float] = None
    quantity_on_hand: Optional[int] = None
    reorder_point: Optional[int] = None

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
    dueDate: Optional[str] = None
    status: str = "pending"

class CreateTaskRequest(BaseModel):
    title: str
    priority: str = "medium"
    dueDate: Optional[str] = None

tasks: List[dict] = []
_next_task_id = 1

class RecommendedRestockItem(BaseModel):
    sku: str
    name: str
    category: Optional[str] = None
    warehouse: Optional[str] = None
    trend: str
    current_demand: int
    forecasted_demand: int
    percent_increase: float
    unit_cost: float
    quantity_on_hand: int
    reorder_point: int
    recommended_qty: int
    line_total: float

class RestockRecommendationResponse(BaseModel):
    budget: float
    total_cost: float
    remaining_budget: float
    items: List[RecommendedRestockItem]

class RestockOrderItem(BaseModel):
    sku: str
    name: str
    quantity: int
    unit_cost: float

class CreateRestockOrderRequest(BaseModel):
    budget: float
    items: List[RestockOrderItem]

RESTOCK_LEAD_TIME_DAYS = 7

def build_restock_recommendations(budget: float) -> dict:
    """Rank restockable items by demand trend/forecasted increase and
    greedily fill the given budget with recommended quantities."""
    inventory_by_sku = {item['sku']: item for item in inventory_items}
    candidates = []

    for forecast in demand_forecasts:
        inv = inventory_by_sku.get(forecast['item_sku'])
        if not inv:
            continue
        if forecast['trend'] == 'decreasing':
            continue

        healthy_level = math.ceil(inv['reorder_point'] * 1.5)
        deficit = healthy_level - inv['quantity_on_hand']
        if deficit <= 0:
            continue

        current = forecast['current_demand']
        percent_increase = ((forecast['forecasted_demand'] - current) / current * 100) if current else 0

        candidates.append({
            'sku': inv['sku'],
            'name': inv['name'],
            'category': inv['category'],
            'warehouse': inv['warehouse'],
            'trend': forecast['trend'],
            'current_demand': current,
            'forecasted_demand': forecast['forecasted_demand'],
            'percent_increase': round(percent_increase, 1),
            'unit_cost': inv['unit_cost'],
            'quantity_on_hand': inv['quantity_on_hand'],
            'reorder_point': inv['reorder_point'],
            'deficit_qty': deficit,
        })

    trend_rank = {'increasing': 0, 'stable': 1}
    candidates.sort(key=lambda c: (trend_rank.get(c['trend'], 2), -c['percent_increase']))

    remaining_budget = budget
    result_items = []

    for candidate in candidates:
        if remaining_budget <= 0:
            break

        full_qty = candidate['deficit_qty']
        full_cost = round(full_qty * candidate['unit_cost'], 2)

        if full_cost <= remaining_budget:
            qty = full_qty
        else:
            qty = int(remaining_budget // candidate['unit_cost'])
            if qty <= 0:
                continue

        line_total = round(qty * candidate['unit_cost'], 2)
        remaining_budget = round(remaining_budget - line_total, 2)

        item = {k: v for k, v in candidate.items() if k != 'deficit_qty'}
        item['recommended_qty'] = qty
        item['line_total'] = line_total
        result_items.append(item)

        if qty < full_qty:
            # Only a partial fill was affordable; the budget is exhausted.
            break

    total_cost = round(sum(i['line_total'] for i in result_items), 2)
    return {
        'budget': budget,
        'total_cost': total_cost,
        'remaining_budget': round(budget - total_cost, 2),
        'items': result_items,
    }

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
    """Get demand forecasts, joined with inventory cost/stock data by SKU"""
    inventory_by_sku = {item['sku']: item for item in inventory_items}
    result = []
    for forecast in demand_forecasts:
        forecast_dict = dict(forecast)
        inv = inventory_by_sku.get(forecast['item_sku'])
        if inv:
            forecast_dict['unit_cost'] = inv['unit_cost']
            forecast_dict['quantity_on_hand'] = inv['quantity_on_hand']
            forecast_dict['reorder_point'] = inv['reorder_point']
        result.append(forecast_dict)
    return result

@app.get("/api/restocking/recommendations", response_model=RestockRecommendationResponse)
def get_restock_recommendations(budget: float = 0.0):
    """Recommend items to restock within a given budget, ranked by demand trend"""
    if budget < 0:
        raise HTTPException(status_code=400, detail="Budget must be non-negative")
    return build_restock_recommendations(budget)

@app.post("/api/restocking/order", response_model=Order, status_code=201)
def create_restock_order(request: CreateRestockOrderRequest):
    """Submit a restocking order built from recommended items"""
    if not request.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")

    order_date = datetime.now(timezone.utc).replace(tzinfo=None)
    expected_delivery = order_date + timedelta(days=RESTOCK_LEAD_TIME_DAYS)

    order_items = [
        {"sku": i.sku, "name": i.name, "quantity": i.quantity, "unit_price": i.unit_cost}
        for i in request.items
    ]
    total_value = round(sum(i.quantity * i.unit_cost for i in request.items), 2)

    new_order = {
        "id": str(len(orders) + 1),
        "order_number": f"RESTOCK-{order_date.strftime('%Y%m%d%H%M%S')}",
        "customer": "Internal Restocking",
        "items": order_items,
        "status": "Submitted",
        "order_date": order_date.isoformat(),
        "expected_delivery": expected_delivery.isoformat(),
        "total_value": total_value,
        "actual_delivery": None,
        "warehouse": None,
        "category": None,
        "lead_time_days": RESTOCK_LEAD_TIME_DAYS,
    }
    orders.append(new_order)
    return new_order

@app.post("/api/purchase-orders", response_model=PurchaseOrder, status_code=201)
def create_purchase_order(request: CreatePurchaseOrderRequest):
    """Create a purchase order for a backlog item"""
    backlog_item = next((b for b in backlog_items if b["id"] == request.backlog_item_id), None)
    if not backlog_item:
        raise HTTPException(status_code=404, detail=f"Backlog item {request.backlog_item_id} not found")

    new_po = {
        "id": f"PO-{len(purchase_orders) + 1:04d}",
        "backlog_item_id": request.backlog_item_id,
        "supplier_name": request.supplier_name,
        "quantity": request.quantity,
        "unit_cost": request.unit_cost,
        "expected_delivery_date": request.expected_delivery_date,
        "status": "Pending",
        "created_date": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        "notes": request.notes,
    }
    purchase_orders.append(new_po)
    return new_po

@app.get("/api/purchase-orders/{backlog_item_id}", response_model=PurchaseOrder)
def get_purchase_order_by_backlog_item(backlog_item_id: str):
    """Get the purchase order associated with a backlog item"""
    po = next((p for p in purchase_orders if p["backlog_item_id"] == backlog_item_id), None)
    if not po:
        raise HTTPException(status_code=404, detail=f"No purchase order found for backlog item {backlog_item_id}")
    return po

@app.get("/api/tasks", response_model=List[Task])
def get_tasks():
    """Get all API-created tasks"""
    return tasks

@app.post("/api/tasks", response_model=Task, status_code=201)
def create_task(request: CreateTaskRequest):
    """Create a new task"""
    global _next_task_id
    new_task = {
        "id": f"task-{_next_task_id}",
        "title": request.title,
        "priority": request.priority,
        "dueDate": request.dueDate,
        "status": "pending",
    }
    _next_task_id += 1
    tasks.append(new_task)
    return new_task

@app.patch("/api/tasks/{task_id}", response_model=Task)
def toggle_task(task_id: str):
    """Toggle a task's status between pending and completed"""
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    task["status"] = "completed" if task["status"] == "pending" else "pending"
    return task

@app.delete("/api/tasks/{task_id}", status_code=204)
def delete_task(task_id: str):
    """Delete a task"""
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    tasks.remove(task)

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
