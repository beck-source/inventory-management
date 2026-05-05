from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
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
    unit_cost: float
    lead_time_days: int


# --- Restocking models -------------------------------------------------------

class RestockRecommendation(BaseModel):
    """One forecasted-demand item with a positive shortage, plus whether the
    requested budget covers it (greedy fill, largest shortage first)."""
    sku: str
    name: str
    trend: str
    shortage: int           # forecasted_demand - current_demand (units to buy)
    unit_cost: float
    line_cost: float        # shortage * unit_cost
    lead_time_days: int
    included: bool          # true if the budget covers this line


class RestockRecommendationResponse(BaseModel):
    budget: float
    total_cost: float       # sum of line_cost for included items only
    items_covered: int      # count of included items
    items_total: int        # count of all items with a positive shortage
    items: List[RestockRecommendation]


class RestockOrderItemInput(BaseModel):
    sku: str
    quantity: int = Field(gt=0)
    unit_cost: float = Field(gt=0)


class SubmitRestockRequest(BaseModel):
    budget: float
    items: List[RestockOrderItemInput] = Field(min_length=1)


class SubmittedOrderItem(BaseModel):
    sku: str
    name: str
    quantity: int
    unit_cost: float
    lead_time_days: int
    expected_delivery: str  # ISO date


class SubmittedOrder(BaseModel):
    id: str
    order_number: str
    submitted_at: str
    status: str
    total_value: float
    items: List[SubmittedOrderItem]

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

# --- Restocking endpoints ----------------------------------------------------
# In-memory store for restocking orders submitted via the Restocking tab.
# Like the rest of the app this has no persistence: the list resets on restart.
submitted_restock_orders: List[dict] = []
_next_restock_seq = 1


def _build_restock_recommendations(budget: float) -> dict:
    """Greedy budget fill: largest shortage first.

    Items with shortage <= 0 (forecast at/below current demand) are dropped —
    nothing to restock. Remaining items are sorted by shortage descending
    (line_cost descending as a tiebreak so equally-short items prefer the
    higher-impact line). We then walk the list and include any item whose line
    cost still fits in the remaining budget. Items that don't fit are *kept*
    in the response with included=False so the UI can show what the budget
    misses, instead of silently dropping rows.
    """
    candidates = []
    for f in demand_forecasts:
        shortage = f["forecasted_demand"] - f["current_demand"]
        if shortage <= 0:
            continue
        line_cost = round(shortage * f["unit_cost"], 2)
        candidates.append({
            "sku": f["item_sku"],
            "name": f["item_name"],
            "trend": f["trend"],
            "shortage": shortage,
            "unit_cost": f["unit_cost"],
            "line_cost": line_cost,
            "lead_time_days": f["lead_time_days"],
        })

    candidates.sort(key=lambda c: (-c["shortage"], -c["line_cost"]))

    total = 0.0
    covered = 0
    for c in candidates:
        # Skip-and-continue (not stop-at-first-failure): a single expensive
        # line shouldn't block cheaper lines further down the list.
        if total + c["line_cost"] <= budget:
            c["included"] = True
            total = round(total + c["line_cost"], 2)
            covered += 1
        else:
            c["included"] = False

    return {
        "budget": budget,
        "total_cost": total,
        "items_covered": covered,
        "items_total": len(candidates),
        "items": candidates,
    }


@app.get("/api/restocking/recommendations", response_model=RestockRecommendationResponse)
def get_restock_recommendations(budget: float = Query(..., ge=0)):
    """Recommend which forecast shortages the given budget can cover."""
    return _build_restock_recommendations(budget)


@app.post("/api/restocking/orders", response_model=SubmittedOrder, status_code=201)
def submit_restock_order(req: SubmitRestockRequest):
    """Create an in-memory restocking order from a list of SKU/qty lines."""
    global _next_restock_seq

    # Look up name + lead time from the forecast so the caller only has to
    # supply sku/quantity/unit_cost. Reject unknown SKUs early.
    forecast_by_sku = {f["item_sku"]: f for f in demand_forecasts}
    now = datetime.now()
    order_items = []
    total = 0.0
    for line in req.items:
        f = forecast_by_sku.get(line.sku)
        if not f:
            raise HTTPException(status_code=400, detail=f"Unknown SKU {line.sku}")
        lead = f["lead_time_days"]
        order_items.append({
            "sku": line.sku,
            "name": f["item_name"],
            "quantity": line.quantity,
            "unit_cost": line.unit_cost,
            "lead_time_days": lead,
            "expected_delivery": (now + timedelta(days=lead)).strftime("%Y-%m-%dT%H:%M:%S"),
        })
        total = round(total + line.quantity * line.unit_cost, 2)

    order = {
        "id": str(_next_restock_seq),
        "order_number": f"RST-{now.year}-{_next_restock_seq:04d}",
        "submitted_at": now.strftime("%Y-%m-%dT%H:%M:%S"),
        "status": "Submitted",
        "total_value": total,
        "items": order_items,
    }
    _next_restock_seq += 1
    submitted_restock_orders.append(order)
    return order


@app.get("/api/restocking/orders", response_model=List[SubmittedOrder])
def list_submitted_restock_orders():
    """List restocking orders newest-first."""
    return list(reversed(submitted_restock_orders))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
