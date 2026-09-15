from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders, restock_orders

app = FastAPI(title="Factory Inventory Management System")

# Quarter mapping for date filtering
QUARTER_MAP = {
    'Q1-2025': ['2025-01', '2025-02', '2025-03'],
    'Q2-2025': ['2025-04', '2025-05', '2025-06'],
    'Q3-2025': ['2025-07', '2025-08', '2025-09'],
    'Q4-2025': ['2025-10', '2025-11', '2025-12']
}

# Supplier lead time by product category, in calendar days.
# The dataset has no per-item lead time, so category is the only signal available;
# these values are demo constants, not sourced from a supplier contract.
CATEGORY_LEAD_TIME_DAYS = {
    'Circuit Boards': 10,
    'Sensors': 7,
    'Actuators': 21,
    'Controllers': 14,
    'Power Supplies': 12
}

# Used when an item's category is missing from the table above.
DEFAULT_LEAD_TIME_DAYS = 14

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
    # The client keys its "Create PO" / "View PO" branch off this id, not off the
    # boolean above, so both have to be sent or the button never flips.
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

class RestockRecommendation(BaseModel):
    item_sku: str
    item_name: str
    category: str
    warehouse: str
    unit_cost: float
    current_demand: int
    forecasted_demand: int
    demand_gap: int
    recommended_quantity: int
    line_total: float
    is_partial: bool
    lead_time_days: int
    quantity_on_hand: int
    reorder_point: int

class RestockPlan(BaseModel):
    budget: float
    total_cost: float
    remaining_budget: float
    item_count: int
    total_units: int
    lead_time_days: int
    full_coverage_cost: float
    recommendations: List[RestockRecommendation]
    # Forecast SKUs dropped because inventory.json has no matching record, so no
    # unit_cost could be resolved. Surfaced instead of silently omitted, otherwise
    # the UI would show a shorter list than the Demand tab with no explanation.
    unpriced_skus: List[str]

class RestockOrderLine(BaseModel):
    item_sku: str
    item_name: str
    category: str
    quantity: int
    unit_cost: float
    line_total: float
    lead_time_days: int

class RestockOrder(BaseModel):
    id: str
    order_number: str
    status: str
    created_date: str
    expected_delivery: str
    lead_time_days: int
    budget: float
    total_value: float
    item_count: int
    total_units: int
    lines: List[RestockOrderLine]

class RestockOrderLineRequest(BaseModel):
    item_sku: str
    quantity: int

class CreateRestockOrderRequest(BaseModel):
    budget: float
    lines: List[RestockOrderLineRequest]

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
        existing_po = next((po for po in purchase_orders if po["backlog_item_id"] == item["id"]), None)
        item_dict["has_purchase_order"] = existing_po is not None
        item_dict["purchase_order_id"] = existing_po["id"] if existing_po else None
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

# ---------------------------------------------------------------------------
# Restocking
# ---------------------------------------------------------------------------

def lead_time_for_category(category: str) -> int:
    """Look up supplier lead time in days for a product category."""
    return CATEGORY_LEAD_TIME_DAYS.get(category, DEFAULT_LEAD_TIME_DAYS)

def build_restock_plan(budget: float) -> dict:
    """Recommend what to restock within `budget`, largest demand gap first.

    Demand forecasts carry no price, so each forecast is joined to inventory on
    SKU to resolve unit_cost and category. Forecasts with no inventory match are
    reported separately rather than dropped quietly.
    """
    inventory_by_sku = {item["sku"]: item for item in inventory_items}

    candidates = []
    unpriced_skus = []
    for forecast in demand_forecasts:
        gap = forecast["forecasted_demand"] - forecast["current_demand"]
        if gap <= 0:
            # Demand is flat or shrinking - nothing to restock.
            continue

        item = inventory_by_sku.get(forecast["item_sku"])
        if not item:
            unpriced_skus.append(forecast["item_sku"])
            continue

        candidates.append((forecast, item, gap))

    # Largest gap first. Ties break to the cheaper unit so the same budget closes
    # more of the shortfall; SKU is the final key purely to keep ordering stable
    # across runs when gap and unit_cost are identical.
    candidates.sort(key=lambda c: (-c[2], c[1]["unit_cost"], c[0]["item_sku"]))

    remaining = float(budget)
    recommendations = []
    for forecast, item, gap in candidates:
        unit_cost = item["unit_cost"]

        # Epsilon guards against a float remainder like 4018.6599999 flooring one
        # unit short of what the budget can actually cover.
        affordable_quantity = int((remaining + 1e-9) // unit_cost)
        if affordable_quantity <= 0:
            break

        quantity = min(gap, affordable_quantity)
        line_total = round(quantity * unit_cost, 2)
        is_partial = quantity < gap

        recommendations.append({
            "item_sku": forecast["item_sku"],
            "item_name": forecast["item_name"],
            "category": item["category"],
            "warehouse": item["warehouse"],
            "unit_cost": unit_cost,
            "current_demand": forecast["current_demand"],
            "forecasted_demand": forecast["forecasted_demand"],
            "demand_gap": gap,
            "recommended_quantity": quantity,
            "line_total": line_total,
            "is_partial": is_partial,
            "lead_time_days": lead_time_for_category(item["category"]),
            "quantity_on_hand": item["quantity_on_hand"],
            "reorder_point": item["reorder_point"]
        })
        remaining = round(remaining - line_total, 2)

        if is_partial:
            # The budget ran out mid-line. Stop here rather than skipping ahead to
            # cheaper items - the ranking is by priority, not by what still fits.
            break

    total_cost = round(sum(r["line_total"] for r in recommendations), 2)
    full_coverage_cost = round(sum(gap * item["unit_cost"] for _, item, gap in candidates), 2)

    return {
        "budget": round(float(budget), 2),
        "total_cost": total_cost,
        "remaining_budget": round(float(budget) - total_cost, 2),
        "item_count": len(recommendations),
        "total_units": sum(r["recommended_quantity"] for r in recommendations),
        # A shipment is only complete when its slowest line arrives.
        "lead_time_days": max((r["lead_time_days"] for r in recommendations), default=0),
        "full_coverage_cost": full_coverage_cost,
        "recommendations": recommendations,
        "unpriced_skus": unpriced_skus
    }

@app.get("/api/restock/recommendations", response_model=RestockPlan)
def get_restock_recommendations(budget: float = 0):
    """Recommend restocking quantities that fit within the given budget."""
    if budget < 0:
        raise HTTPException(status_code=400, detail="Budget must not be negative")
    return build_restock_plan(budget)

@app.get("/api/restock-orders", response_model=List[RestockOrder])
def get_restock_orders():
    """Get all submitted restocking orders, newest first."""
    return list(reversed(restock_orders))

@app.post("/api/restock-orders", response_model=RestockOrder, status_code=201)
def create_restock_order(request: CreateRestockOrderRequest):
    """Submit a restocking order.

    Quantities come from the client but prices do not - every line is re-priced
    from inventory so a tampered or stale client payload cannot set its own cost.
    """
    if not request.lines:
        raise HTTPException(status_code=400, detail="A restocking order needs at least one line")

    inventory_by_sku = {item["sku"]: item for item in inventory_items}

    lines = []
    for requested in request.lines:
        if requested.quantity <= 0:
            raise HTTPException(
                status_code=400,
                detail=f"Quantity for {requested.item_sku} must be greater than zero"
            )

        item = inventory_by_sku.get(requested.item_sku)
        if not item:
            raise HTTPException(status_code=404, detail=f"Unknown SKU: {requested.item_sku}")

        lines.append({
            "item_sku": item["sku"],
            "item_name": item["name"],
            "category": item["category"],
            "quantity": requested.quantity,
            "unit_cost": item["unit_cost"],
            "line_total": round(requested.quantity * item["unit_cost"], 2),
            "lead_time_days": lead_time_for_category(item["category"])
        })

    total_value = round(sum(line["line_total"] for line in lines), 2)

    # Tolerance of one cent absorbs rounding drift between the client's running
    # total and the server's re-priced total; anything larger is a real overspend.
    if total_value > request.budget + 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"Order total {total_value} exceeds budget {request.budget}"
        )

    lead_time_days = max(line["lead_time_days"] for line in lines)
    created = datetime.now()

    order = {
        "id": str(len(restock_orders) + 1),
        "order_number": f"RO-{len(restock_orders) + 1:04d}",
        "status": "Submitted",
        "created_date": created.isoformat(timespec="seconds"),
        "expected_delivery": (created + timedelta(days=lead_time_days)).isoformat(timespec="seconds"),
        "lead_time_days": lead_time_days,
        "budget": round(request.budget, 2),
        "total_value": total_value,
        "item_count": len(lines),
        "total_units": sum(line["quantity"] for line in lines),
        "lines": lines
    }

    # Mutate in place: main.py and mock_data.py bind the same list object, so
    # appending keeps both views consistent. Rebinding would desynchronise them.
    restock_orders.append(order)
    return order

# ---------------------------------------------------------------------------
# Purchase orders (raised against a backlog shortage)
# ---------------------------------------------------------------------------

@app.get("/api/purchase-orders/{backlog_item_id}", response_model=PurchaseOrder)
def get_purchase_order(backlog_item_id: str):
    """Get the purchase order raised for a backlog item."""
    po = next((po for po in purchase_orders if po["backlog_item_id"] == backlog_item_id), None)
    if not po:
        raise HTTPException(
            status_code=404,
            detail=f"No purchase order for backlog item {backlog_item_id}"
        )
    return po

@app.post("/api/purchase-orders", response_model=PurchaseOrder, status_code=201)
def create_purchase_order(request: CreatePurchaseOrderRequest):
    """Raise a purchase order against a backlog shortage."""
    if not any(item["id"] == request.backlog_item_id for item in backlog_items):
        raise HTTPException(
            status_code=404,
            detail=f"Unknown backlog item: {request.backlog_item_id}"
        )

    if any(po["backlog_item_id"] == request.backlog_item_id for po in purchase_orders):
        raise HTTPException(
            status_code=400,
            detail=f"Backlog item {request.backlog_item_id} already has a purchase order"
        )

    if request.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than zero")

    if request.unit_cost < 0:
        raise HTTPException(status_code=400, detail="Unit cost must not be negative")

    if not request.supplier_name.strip():
        raise HTTPException(status_code=400, detail="Supplier name is required")

    purchase_order = {
        "id": f"PO-{len(purchase_orders) + 1:04d}",
        "backlog_item_id": request.backlog_item_id,
        "supplier_name": request.supplier_name.strip(),
        "quantity": request.quantity,
        "unit_cost": request.unit_cost,
        "expected_delivery_date": request.expected_delivery_date,
        "status": "Ordered",
        "created_date": datetime.now().isoformat(timespec="seconds"),
        "notes": request.notes
    }

    # get_backlog() reads this same list object by reference, so appending here is
    # what makes the item's has_purchase_order flag flip on the next request.
    purchase_orders.append(purchase_order)
    return purchase_order

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
