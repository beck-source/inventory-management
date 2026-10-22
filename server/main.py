from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, date
from itertools import count
from mock_data import (inventory_items, orders, demand_forecasts, backlog_items, spending_summary,
                       monthly_spending, category_spending, recent_transactions, purchase_orders,
                       restock_orders, tasks, lead_time_for_category)

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


# No target stock level exists anywhere in the data. Restocking to exactly the reorder
# point would re-trip the low-stock alert on the next unit sold, so we top up to twice
# it. A demand forecast, where one exists for the SKU, can raise this target but never
# lower it -- a forecast should not make an item look healthier than its reorder policy.
RESTOCK_TARGET_MULTIPLIER = 2


def build_restock_candidates(warehouse: Optional[str] = None, category: Optional[str] = None) -> list:
    """
    Inventory left-joined to demand forecasts, reduced to the items that are short.

    Only inventory carries unit_cost/warehouse/category, so it drives the candidate list;
    a forecast matching on sku == item_sku can raise an item's target and contributes its
    trend. Items already at or above target are dropped.
    """
    forecasts_by_sku = {forecast['item_sku']: forecast for forecast in demand_forecasts}
    candidates = []

    for item in apply_filters(inventory_items, warehouse, category):
        forecast = forecasts_by_sku.get(item['sku'])
        target = item['reorder_point'] * RESTOCK_TARGET_MULTIPLIER
        shortfall_source = 'reorder_point'

        if forecast and forecast['forecasted_demand'] > target:
            target = forecast['forecasted_demand']
            shortfall_source = 'forecast'

        shortfall = target - item['quantity_on_hand']
        if shortfall <= 0:
            continue

        candidates.append({
            'sku': item['sku'],
            'name': item['name'],
            'category': item['category'],
            'warehouse': item['warehouse'],
            'unit_cost': item['unit_cost'],
            'quantity_on_hand': item['quantity_on_hand'],
            'reorder_point': item['reorder_point'],
            # Same comparison the dashboard summary uses, so the two low-stock counts agree
            'below_reorder_point': item['quantity_on_hand'] <= item['reorder_point'],
            'shortfall': shortfall,
            'shortfall_source': shortfall_source,
            'forecast_trend': forecast['trend'] if forecast else None,
            'forecasted_demand': forecast['forecasted_demand'] if forecast else None,
            'lead_time_days': lead_time_for_category(item['category']),
        })

    return candidates


def rank_restock_candidates(candidates: list) -> list:
    """
    Items at or below their reorder point first, then by largest shortfall.

    unit_cost and sku break ties so the ranking is total and deterministic rather than
    dependent on dict insertion order -- TMP-201 and PSU-508 currently tie on shortfall.
    """
    return sorted(
        candidates,
        key=lambda c: (0 if c['below_reorder_point'] else 1, -c['shortfall'], c['unit_cost'], c['sku'])
    )


def allocate_budget(ranked: list, budget: float):
    """
    Greedily fill the budget down the ranked list, allowing a partial final line.

    Scanning continues past an item that does not fit rather than stopping, so leftover
    budget can still reach a cheaper item further down without disturbing priority order.
    Returns (allocation dicts, total cost).
    """
    remaining = budget
    allocations = []

    for candidate in ranked:
        # The epsilon stops float noise from turning an exactly-affordable quantity into
        # one unit fewer, e.g. 2237.50 / 89.50 landing on 24.999999 instead of 25.
        affordable = int((remaining + 1e-9) // candidate['unit_cost'])
        quantity = min(candidate['shortfall'], affordable)
        if quantity < 1:
            continue

        allocations.append({
            **candidate,
            'recommended_quantity': quantity,
            'line_cost': round(quantity * candidate['unit_cost'], 2),
            'fully_covered': quantity == candidate['shortfall'],
        })
        remaining -= quantity * candidate['unit_cost']

    return allocations, round(budget - remaining, 2)


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
    supplier_name: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    unit_cost: float = Field(gt=0)
    expected_delivery_date: date
    notes: Optional[str] = None

class Task(BaseModel):
    id: str
    title: str
    priority: Literal['high', 'medium', 'low']
    dueDate: str
    status: Literal['pending', 'completed']

class CreateTaskRequest(BaseModel):
    title: str = Field(min_length=1)
    priority: Literal['high', 'medium', 'low'] = 'medium'
    dueDate: date


class RestockRecommendationItem(BaseModel):
    sku: str
    name: str
    category: str
    warehouse: str
    unit_cost: float
    quantity_on_hand: int
    reorder_point: int
    below_reorder_point: bool
    shortfall: int
    shortfall_source: str
    forecast_trend: Optional[str] = None
    forecasted_demand: Optional[int] = None
    recommended_quantity: int
    line_cost: float
    fully_covered: bool
    lead_time_days: int

class RestockRecommendationResponse(BaseModel):
    budget: float
    total_cost: float
    remaining_budget: float
    candidate_count: int
    max_useful_cost: float
    min_unit_cost: Optional[float] = None
    items: List[RestockRecommendationItem]

class RestockOrderLineRequest(BaseModel):
    sku: str
    quantity: int = Field(gt=0)

class CreateRestockOrderRequest(BaseModel):
    budget: float = Field(ge=0)
    items: List[RestockOrderLineRequest] = Field(min_length=1)

class RestockOrderLine(BaseModel):
    sku: str
    name: str
    category: str
    warehouse: str
    quantity: int
    unit_cost: float
    line_cost: float
    lead_time_days: int

class RestockOrder(BaseModel):
    id: str
    order_number: str
    status: str
    created_date: str
    budget: float
    total_cost: float
    lead_time_days: int
    expected_delivery: str
    items: List[RestockOrderLine]

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
    po_by_backlog_item = {po["backlog_item_id"]: po for po in purchase_orders}
    result = []
    for item in backlog_items:
        item_dict = dict(item)
        po = po_by_backlog_item.get(item["id"])
        item_dict["has_purchase_order"] = po is not None
        # The dashboard switches between "Create PO" and "View PO" on this id
        item_dict["purchase_order_id"] = po["id"] if po else None
        result.append(item_dict)
    return result

@app.post("/api/purchase-orders", response_model=PurchaseOrder, status_code=201)
def create_purchase_order(request: CreatePurchaseOrderRequest):
    """Raise a purchase order against a backlog item. In-memory only, lost on restart."""
    if not any(item["id"] == request.backlog_item_id for item in backlog_items):
        raise HTTPException(status_code=404, detail=f"Backlog item {request.backlog_item_id} not found")
    if any(po["backlog_item_id"] == request.backlog_item_id for po in purchase_orders):
        raise HTTPException(status_code=400, detail="A purchase order already exists for this backlog item")

    po = {
        "id": f"PO-{len(purchase_orders) + 1:04d}",
        "backlog_item_id": request.backlog_item_id,
        "supplier_name": request.supplier_name.strip(),
        "quantity": request.quantity,
        "unit_cost": request.unit_cost,
        "expected_delivery_date": request.expected_delivery_date.isoformat(),
        "status": "pending",
        "created_date": datetime.now().replace(microsecond=0).isoformat(),
        "notes": request.notes
    }
    purchase_orders.append(po)
    return po

@app.get("/api/purchase-orders/{backlog_item_id}", response_model=PurchaseOrder)
def get_purchase_order_by_backlog_item(backlog_item_id: str):
    """Get the purchase order raised against a backlog item"""
    po = next((po for po in purchase_orders if po["backlog_item_id"] == backlog_item_id), None)
    if not po:
        raise HTTPException(status_code=404, detail=f"No purchase order for backlog item {backlog_item_id}")
    return po

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

@app.get("/api/restocking/recommendations", response_model=RestockRecommendationResponse)
def get_restock_recommendations(
    budget: float = Query(0, ge=0),
    warehouse: Optional[str] = None,
    category: Optional[str] = None
):
    """Recommend what to restock within a budget, most urgent first"""
    ranked = rank_restock_candidates(build_restock_candidates(warehouse, category))
    allocations, total_cost = allocate_budget(ranked, budget)

    return {
        "budget": budget,
        "total_cost": total_cost,
        "remaining_budget": round(budget - total_cost, 2),
        "candidate_count": len(ranked),
        # Cost of fully covering every candidate. The client sizes its budget slider from
        # this, so the track never extends past the point where more money buys nothing.
        "max_useful_cost": round(sum(c['shortfall'] * c['unit_cost'] for c in ranked), 2),
        "min_unit_cost": min((c['unit_cost'] for c in ranked), default=None),
        "items": allocations
    }

@app.post("/api/restocking/orders", response_model=RestockOrder, status_code=201)
def create_restock_order(request: CreateRestockOrderRequest):
    """Submit a restocking order. Held in memory only, so it is lost on restart."""
    inventory_by_sku = {item['sku']: item for item in inventory_items}
    lines = []

    for requested in request.items:
        item = inventory_by_sku.get(requested.sku)
        if not item:
            raise HTTPException(status_code=404, detail=f"Inventory item {requested.sku} not found")

        # Price from inventory rather than trusting the client, so a submitted order can
        # never disagree with the catalogue it was built from.
        lines.append({
            'sku': item['sku'],
            'name': item['name'],
            'category': item['category'],
            'warehouse': item['warehouse'],
            'quantity': requested.quantity,
            'unit_cost': item['unit_cost'],
            'line_cost': round(requested.quantity * item['unit_cost'], 2),
            'lead_time_days': lead_time_for_category(item['category'])
        })

    total_cost = round(sum(line['line_cost'] for line in lines), 2)
    # A cent of slack absorbs float drift between the client's running total and ours
    if total_cost > request.budget + 0.01:
        raise HTTPException(status_code=400, detail="Order total exceeds budget")

    # The order is only complete once its slowest line lands
    lead_time_days = max(line['lead_time_days'] for line in lines)
    created = datetime.now().replace(microsecond=0)
    sequence = len(restock_orders) + 1

    order = {
        'id': str(sequence),
        # The sequence restarts with the process, so a number can be reissued after a
        # restart. Harmless while orders are in-memory, but not a durable identifier.
        'order_number': f"RST-{created.year}-{sequence:04d}",
        'status': 'Submitted',
        'created_date': created.isoformat(),
        'budget': request.budget,
        'total_cost': total_cost,
        'lead_time_days': lead_time_days,
        'expected_delivery': (created + timedelta(days=lead_time_days)).isoformat(),
        'items': lines
    }
    restock_orders.append(order)
    return order

@app.get("/api/restocking/orders", response_model=List[RestockOrder])
def get_restock_orders(
    warehouse: Optional[str] = None,
    category: Optional[str] = None
):
    """
    List submitted restocking orders.

    An order can span warehouses and categories, so it matches when any of its lines
    does. Status and month are deliberately not accepted: every restock order has status
    "Submitted" and a current-year date, so either filter would hide all of them.
    """
    return [order for order in restock_orders if apply_filters(order['items'], warehouse, category)]

# Unlike the other in-memory sequences, tasks can be deleted, so a len()-based id could
# be handed out twice. The "api-" prefix also keeps these ids apart from the client's
# built-in mock tasks, which use small integers.
_task_ids = count(1)

def _find_task(task_id: str) -> dict:
    task = next((t for t in tasks if t['id'] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task

@app.get("/api/tasks", response_model=List[Task])
def get_tasks():
    """List tasks created through the UI"""
    return tasks

@app.post("/api/tasks", response_model=Task, status_code=201)
def create_task(request: CreateTaskRequest):
    """Create a task. In-memory only, lost on restart."""
    task = {
        'id': f"api-{next(_task_ids)}",
        'title': request.title.strip(),
        'priority': request.priority,
        'dueDate': request.dueDate.isoformat(),
        'status': 'pending'
    }
    tasks.append(task)
    return task

@app.patch("/api/tasks/{task_id}", response_model=Task)
def toggle_task(task_id: str):
    """Flip a task between pending and completed"""
    task = _find_task(task_id)
    task['status'] = 'completed' if task['status'] == 'pending' else 'pending'
    return task

@app.delete("/api/tasks/{task_id}", response_model=Task)
def delete_task(task_id: str):
    """Delete a task and return it"""
    task = _find_task(task_id)
    tasks.remove(task)
    return task

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
