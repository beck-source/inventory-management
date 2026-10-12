from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders, restock_orders, tasks

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

class RestockRecommendation(BaseModel):
    sku: str
    item_name: str
    trend: str
    current_demand: int
    forecasted_demand: int
    quantity_on_hand: int
    recommended_qty: int
    funded_qty: int
    unit_cost: float
    line_total: float
    priority_score: float

class RestockRecommendationResponse(BaseModel):
    budget: float
    total_cost: float
    items: List[RestockRecommendation]

class RestockOrderLineItem(BaseModel):
    sku: str
    item_name: str
    quantity: int
    unit_cost: float
    line_total: float

class RestockOrderItemRequest(BaseModel):
    sku: str
    item_name: str
    quantity: int
    unit_cost: float

class CreateRestockOrderRequest(BaseModel):
    items: List[RestockOrderItemRequest]

class RestockOrder(BaseModel):
    id: str
    order_number: str
    items: List[RestockOrderLineItem]
    status: str
    order_date: str
    expected_delivery: str
    lead_time_days: int
    total_value: float

class Task(BaseModel):
    id: int
    title: str
    priority: str
    dueDate: str
    status: str

class CreateTaskRequest(BaseModel):
    title: str
    priority: str
    dueDate: str

LEAD_TIME_DAYS = 14

def build_recommendations(budget: float) -> RestockRecommendationResponse:
    """Build priority-ranked restock recommendations within a budget"""
    # Aggregate quantity_on_hand and unit_cost per SKU across all warehouse rows
    inventory_by_sku = {}
    for inv in inventory_items:
        sku = inv["sku"]
        if sku not in inventory_by_sku:
            inventory_by_sku[sku] = {"quantity_on_hand": 0, "unit_cost": inv["unit_cost"]}
        inventory_by_sku[sku]["quantity_on_hand"] += inv["quantity_on_hand"]

    candidates = []
    for f in demand_forecasts:
        sku = f["item_sku"]
        inv = inventory_by_sku.get(sku)
        if not inv:
            continue  # no matching inventory row, skip

        recommended_qty = max(0, f["forecasted_demand"] - inv["quantity_on_hand"])
        if recommended_qty <= 0:
            continue  # nothing to restock

        trend_weight = {"increasing": 2.0, "stable": 1.0, "decreasing": 0.5}.get(f["trend"], 1.0)
        gap_ratio = recommended_qty / max(f["forecasted_demand"], 1)
        priority_score = trend_weight * (1 + gap_ratio)

        candidates.append({
            "sku": sku,
            "item_name": f["item_name"],
            "trend": f["trend"],
            "current_demand": f["current_demand"],
            "forecasted_demand": f["forecasted_demand"],
            "quantity_on_hand": inv["quantity_on_hand"],
            "recommended_qty": recommended_qty,
            "unit_cost": inv["unit_cost"],
            "priority_score": priority_score,
        })

    # Priority-first, highest score wins; ties broken by larger gap
    candidates.sort(key=lambda c: (c["priority_score"], c["recommended_qty"]), reverse=True)

    remaining = budget
    results = []
    for c in candidates:
        if remaining <= 0:
            # Can't afford any more items; continue scanning for cheaper items that might fit
            if c["unit_cost"] > 0 and remaining + c["unit_cost"] > c["unit_cost"]:
                # There's a chance a cheaper item fits; check it
                pass
            else:
                continue

        full_cost = c["recommended_qty"] * c["unit_cost"]
        if full_cost <= remaining:
            funded_qty = c["recommended_qty"]
        else:
            funded_qty = int(remaining // c["unit_cost"]) if c["unit_cost"] > 0 else 0

        if funded_qty <= 0:
            continue  # can't afford even 1 unit

        line_total = round(funded_qty * c["unit_cost"], 2)
        remaining -= line_total
        results.append(RestockRecommendation(funded_qty=funded_qty, line_total=line_total, **c))

    total_cost = round(sum(r.line_total for r in results), 2)
    return RestockRecommendationResponse(budget=budget, total_cost=total_cost, items=results)

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
def get_restock_recommendations(budget: float):
    """Get budget-constrained, priority-ranked restock recommendations"""
    if budget <= 0:
        raise HTTPException(status_code=400, detail="Budget must be greater than 0")
    return build_recommendations(budget)

@app.post("/api/restocking/orders", response_model=RestockOrder, status_code=201)
def create_restock_order(request: CreateRestockOrderRequest):
    """Submit a consolidated restocking order from recommended/selected items"""
    if not request.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")

    line_items = []
    total_value = 0.0
    for it in request.items:
        if it.quantity <= 0:
            raise HTTPException(status_code=400, detail=f"Invalid quantity for {it.sku}")
        line_total = round(it.quantity * it.unit_cost, 2)
        total_value += line_total
        line_items.append(RestockOrderLineItem(
            sku=it.sku, item_name=it.item_name, quantity=it.quantity,
            unit_cost=it.unit_cost, line_total=line_total
        ))

    order_date = datetime.now()
    expected_delivery = order_date + timedelta(days=LEAD_TIME_DAYS)
    order_number = f"RESTOCK-{order_date.year}-{len(restock_orders) + 1:04d}"

    order = RestockOrder(
        id=str(len(restock_orders) + 1),
        order_number=order_number,
        items=line_items,
        status="Processing",
        order_date=order_date.isoformat(),
        expected_delivery=expected_delivery.isoformat(),
        lead_time_days=LEAD_TIME_DAYS,
        total_value=round(total_value, 2)
    )
    restock_orders.append(order.dict())
    return order

@app.get("/api/restocking/orders", response_model=List[RestockOrder])
def get_restock_orders():
    """Get all submitted restocking orders"""
    return restock_orders

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

@app.post("/api/purchase-orders", response_model=PurchaseOrder, status_code=201)
def create_purchase_order(request: CreatePurchaseOrderRequest):
    """Create a purchase order for a backlog item"""
    backlog_item = next((b for b in backlog_items if b["id"] == request.backlog_item_id), None)
    if not backlog_item:
        raise HTTPException(status_code=404, detail="Backlog item not found")

    order = PurchaseOrder(
        id=str(len(purchase_orders) + 1),
        backlog_item_id=request.backlog_item_id,
        supplier_name=request.supplier_name,
        quantity=request.quantity,
        unit_cost=request.unit_cost,
        expected_delivery_date=request.expected_delivery_date,
        status="Pending",
        created_date=datetime.now().isoformat(),
        notes=request.notes
    )
    purchase_orders.append(order.dict())
    return order

@app.get("/api/purchase-orders/{backlog_item_id}", response_model=PurchaseOrder)
def get_purchase_order_by_backlog_item(backlog_item_id: str):
    """Get the purchase order associated with a backlog item"""
    order = next((po for po in purchase_orders if po["backlog_item_id"] == backlog_item_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return order

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

@app.get("/api/tasks", response_model=List[Task])
def get_tasks():
    """Get all tasks"""
    return tasks

@app.post("/api/tasks", response_model=Task, status_code=201)
def create_task(request: CreateTaskRequest):
    """Create a new task"""
    next_id = max((t["id"] for t in tasks), default=0) + 1
    task = Task(id=next_id, title=request.title, priority=request.priority, dueDate=request.dueDate, status="pending")
    tasks.append(task.dict())
    return task

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int):
    """Delete a task"""
    index = next((i for i, t in enumerate(tasks) if t["id"] == task_id), None)
    if index is None:
        raise HTTPException(status_code=404, detail="Task not found")
    tasks.pop(index)
    return {"message": "Task deleted"}

@app.patch("/api/tasks/{task_id}", response_model=Task)
def toggle_task(task_id: int):
    """Toggle a task's status between pending and completed"""
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task["status"] = "completed" if task["status"] == "pending" else "pending"
    return task

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
