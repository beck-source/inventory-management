from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders, submitted_orders

app = FastAPI(title="Factory Inventory Management System")

# Quarter mapping for date filtering
QUARTER_MAP = {
    'Q1-2025': ['2025-01', '2025-02', '2025-03'],
    'Q2-2025': ['2025-04', '2025-05', '2025-06'],
    'Q3-2025': ['2025-07', '2025-08', '2025-09'],
    'Q4-2025': ['2025-10', '2025-11', '2025-12']
}

# Delivery lead time per inventory category, in days. Used when computing the
# expected delivery date for a submitted restocking order. Fallback below is
# applied for any category not listed here.
CATEGORY_LEAD_TIMES = {
    "Circuit Boards": 14,
    "Sensors": 7,
    "Actuators": 10,
    "Controllers": 12,
    "Power Supplies": 9,
}
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

class RestockingRecommendation(BaseModel):
    sku: str
    name: str
    category: str
    warehouse: str
    unit_cost: float
    current_quantity: int
    reorder_point: int
    quantity_to_order: int
    line_cost: float
    reason: str  # 'below_reorder_point' | 'increasing_trend'
    trend: Optional[str] = None

class RestockingRecommendationsResponse(BaseModel):
    budget: float
    total_cost: float
    items_count: int
    recommendations: List[RestockingRecommendation]

class SubmitOrderItemRequest(BaseModel):
    sku: str
    name: str
    category: str
    warehouse: str
    unit_cost: float
    quantity: int

class SubmitOrderRequest(BaseModel):
    items: List[SubmitOrderItemRequest]
    budget: Optional[float] = None

class SubmittedOrderItem(BaseModel):
    sku: str
    name: str
    category: str
    warehouse: str
    unit_cost: float
    quantity: int
    line_cost: float
    lead_time_days: int

class SubmittedOrder(BaseModel):
    id: str
    order_number: str
    submitted_date: str
    total_cost: float
    total_items: int
    items: List[SubmittedOrderItem]
    status: str
    max_lead_time_days: int
    expected_delivery: str

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

@app.get("/api/restocking/recommendations", response_model=RestockingRecommendationsResponse)
def get_restocking_recommendations(budget: float = 0.0):
    """Recommend items to restock within a budget.

    Priority 1: inventory items below their reorder_point — sorted by largest deficit.
    Priority 2: items with an 'increasing' demand trend not already in P1.

    Items are matched to demand forecasts by name (case-insensitive) because
    demand_forecasts.json and inventory.json don't share SKU prefixes.
    Greedy fill: line items are added in priority order while their line cost
    fits in the remaining budget.
    """
    if budget < 0:
        raise HTTPException(status_code=400, detail="Budget must be non-negative")

    demand_by_name = {f["item_name"].lower(): f for f in demand_forecasts}

    candidates = []

    # Priority 1: below reorder point. Order enough to reach 2x reorder_point so the
    # buffer is meaningful for the demo (a pure deficit refill could be a single unit).
    for item in inventory_items:
        if item["quantity_on_hand"] < item["reorder_point"]:
            qty = (2 * item["reorder_point"]) - item["quantity_on_hand"]
            forecast = demand_by_name.get(item["name"].lower())
            candidates.append({
                "sku": item["sku"],
                "name": item["name"],
                "category": item["category"],
                "warehouse": item["warehouse"],
                "unit_cost": item["unit_cost"],
                "current_quantity": item["quantity_on_hand"],
                "reorder_point": item["reorder_point"],
                "quantity_to_order": qty,
                "line_cost": round(qty * item["unit_cost"], 2),
                "reason": "below_reorder_point",
                "trend": forecast["trend"] if forecast else None,
                "_priority": 1,
                "_deficit": item["reorder_point"] - item["quantity_on_hand"],
            })

    p1_skus = {c["sku"] for c in candidates}

    # Priority 2: trending up but not yet below reorder. Order ~30% of forecasted
    # demand as a forward buffer.
    for item in inventory_items:
        if item["sku"] in p1_skus:
            continue
        forecast = demand_by_name.get(item["name"].lower())
        if forecast and forecast["trend"] == "increasing":
            qty = max(int(forecast["forecasted_demand"] * 0.3), 1)
            candidates.append({
                "sku": item["sku"],
                "name": item["name"],
                "category": item["category"],
                "warehouse": item["warehouse"],
                "unit_cost": item["unit_cost"],
                "current_quantity": item["quantity_on_hand"],
                "reorder_point": item["reorder_point"],
                "quantity_to_order": qty,
                "line_cost": round(qty * item["unit_cost"], 2),
                "reason": "increasing_trend",
                "trend": "increasing",
                "_priority": 2,
                "_deficit": 0,
            })

    candidates.sort(key=lambda c: (c["_priority"], -c["_deficit"], c["line_cost"]))

    selected = []
    total_cost = 0.0
    for c in candidates:
        if total_cost + c["line_cost"] <= budget:
            c.pop("_priority", None)
            c.pop("_deficit", None)
            selected.append(c)
            total_cost += c["line_cost"]

    return {
        "budget": budget,
        "total_cost": round(total_cost, 2),
        "items_count": len(selected),
        "recommendations": selected,
    }

@app.post("/api/restocking/submit", response_model=SubmittedOrder)
def submit_restocking_order(request: SubmitOrderRequest):
    """Submit a restocking order. The order is stored in-memory (resets on
    restart) and surfaces in /api/restocking/submitted.

    Lead time is per-line based on category (CATEGORY_LEAD_TIMES). The order's
    expected_delivery uses the longest line lead time so the whole order is
    considered fulfilled once the slowest item arrives.
    """
    if not request.items:
        raise HTTPException(status_code=400, detail="At least one item is required")

    submitted_at = datetime.now()
    order_number = f"RST-{submitted_at.strftime('%Y%m%d-%H%M%S')}"

    order_items = []
    total_cost = 0.0
    max_lead = 0
    for item in request.items:
        if item.quantity <= 0:
            raise HTTPException(status_code=400, detail=f"Quantity for {item.sku} must be positive")
        lead = CATEGORY_LEAD_TIMES.get(item.category, DEFAULT_LEAD_TIME_DAYS)
        line_cost = round(item.unit_cost * item.quantity, 2)
        total_cost += line_cost
        if lead > max_lead:
            max_lead = lead
        order_items.append({
            "sku": item.sku,
            "name": item.name,
            "category": item.category,
            "warehouse": item.warehouse,
            "unit_cost": item.unit_cost,
            "quantity": item.quantity,
            "line_cost": line_cost,
            "lead_time_days": lead,
        })

    expected_delivery = (submitted_at + timedelta(days=max_lead)).date().isoformat()

    new_order = {
        "id": f"sub-{len(submitted_orders) + 1}",
        "order_number": order_number,
        "submitted_date": submitted_at.isoformat(),
        "total_cost": round(total_cost, 2),
        "total_items": len(order_items),
        "items": order_items,
        "status": "Submitted",
        "max_lead_time_days": max_lead,
        "expected_delivery": expected_delivery,
    }
    submitted_orders.append(new_order)
    return new_order

@app.get("/api/restocking/submitted", response_model=List[SubmittedOrder])
def get_submitted_orders():
    """List submitted restocking orders, most recent first."""
    return sorted(submitted_orders, key=lambda o: o["submitted_date"], reverse=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
