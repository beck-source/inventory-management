from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders, restock_orders

app = FastAPI(title="Factory Inventory Management System")

# Quarter mapping for date filtering
QUARTER_MAP = {
    'Q1-2025': ['2025-01', '2025-02', '2025-03'],
    'Q2-2025': ['2025-04', '2025-05', '2025-06'],
    'Q3-2025': ['2025-07', '2025-08', '2025-09'],
    'Q4-2025': ['2025-10', '2025-11', '2025-12']
}

# Restocking recommendation tuning: increasing-demand items get a bigger
# safety buffer than stable/decreasing ones when computing target quantity.
BUFFER_PCT = {"increasing": 0.20, "stable": 0.10, "decreasing": 0.05}
TREND_PRIORITY = {"increasing": 0, "stable": 1, "decreasing": 2}

def _target_quantity(forecast: dict) -> int:
    """Ideal restock quantity for an item if budget were unlimited."""
    gap = max(forecast["forecasted_demand"] - forecast["current_demand"], 0)
    buffer = round(forecast["forecasted_demand"] * BUFFER_PCT[forecast["trend"]])
    return buffer + gap

def _rank_key(forecast: dict) -> tuple:
    """Recommendation priority: rising trend first, then bigger demand gap,
    then cheaper items first (stretches a limited budget further)."""
    gap = max(forecast["forecasted_demand"] - forecast["current_demand"], 0)
    return (TREND_PRIORITY[forecast["trend"]], -gap, forecast["unit_cost"], forecast["item_sku"])

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

class RestockRecommendationItem(BaseModel):
    item_sku: str
    item_name: str
    trend: str
    unit_cost: float
    lead_time_days: int
    target_quantity: int
    suggested_quantity: int
    suggested_cost: float
    within_budget: bool

class RestockRecommendationResponse(BaseModel):
    budget: float
    items: List[RestockRecommendationItem]
    total_suggested_cost: float
    remaining_budget: float

class RestockOrderLineItem(BaseModel):
    item_sku: str
    item_name: str
    quantity: int
    unit_cost: float
    lead_time_days: int
    line_total: float

class CreateRestockOrderLineItem(BaseModel):
    item_sku: str
    quantity: int = Field(..., gt=0)

class CreateRestockOrderRequest(BaseModel):
    budget: float = Field(..., ge=0)
    items: List[CreateRestockOrderLineItem] = Field(..., min_length=1)

class RestockOrder(BaseModel):
    id: str
    order_number: str
    items: List[RestockOrderLineItem]
    total_cost: float
    budget: float
    status: str
    created_date: str
    expected_delivery: str
    lead_time_days: int

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

@app.get("/api/restock/recommendations", response_model=RestockRecommendationResponse)
def get_restock_recommendations(budget: float = Query(..., ge=0)):
    """Recommend demand-forecast items to restock that fit within a budget.

    Greedily fills the budget in priority order (see _rank_key), including a
    partial quantity on the first item that doesn't fully fit so the budget
    isn't left needlessly unused.
    """
    ranked = sorted(demand_forecasts, key=_rank_key)
    remaining = budget
    items = []
    for forecast in ranked:
        target = _target_quantity(forecast)
        unit_cost = forecast["unit_cost"]
        affordable = int(remaining // unit_cost) if unit_cost > 0 else target
        suggested = min(target, max(affordable, 0))
        cost = round(suggested * unit_cost, 2)
        within = suggested > 0
        if within:
            remaining -= cost
        items.append(RestockRecommendationItem(
            item_sku=forecast["item_sku"],
            item_name=forecast["item_name"],
            trend=forecast["trend"],
            unit_cost=unit_cost,
            lead_time_days=forecast["lead_time_days"],
            target_quantity=target,
            suggested_quantity=suggested,
            suggested_cost=cost,
            within_budget=within
        ))
    total = round(sum(item.suggested_cost for item in items), 2)
    return RestockRecommendationResponse(
        budget=budget,
        items=items,
        total_suggested_cost=total,
        remaining_budget=round(budget - total, 2)
    )

@app.post("/api/restock/orders", response_model=RestockOrder, status_code=201)
def create_restock_order(payload: CreateRestockOrderRequest):
    """Place a restocking order for a set of demand-forecast items.

    Costs and lead time are always computed server-side from the catalog,
    never trusted from the client. Orders are not rejected for exceeding
    the given budget — the budget is a planning input, not a hard limit.
    """
    catalog = {forecast["item_sku"]: forecast for forecast in demand_forecasts}
    line_items = []
    for line in payload.items:
        forecast = catalog.get(line.item_sku)
        if not forecast:
            raise HTTPException(status_code=400, detail=f"Unknown item SKU: {line.item_sku}")
        line_total = round(line.quantity * forecast["unit_cost"], 2)
        line_items.append(RestockOrderLineItem(
            item_sku=line.item_sku,
            item_name=forecast["item_name"],
            quantity=line.quantity,
            unit_cost=forecast["unit_cost"],
            lead_time_days=forecast["lead_time_days"],
            line_total=line_total
        ))

    total_cost = round(sum(line_item.line_total for line_item in line_items), 2)
    max_lead_time = max(line_item.lead_time_days for line_item in line_items)
    created_dt = datetime.now()
    expected_dt = created_dt + timedelta(days=max_lead_time)
    year = created_dt.year
    seq = len([o for o in restock_orders if o["order_number"].startswith(f"PO-{year}-")]) + 1

    order = RestockOrder(
        id=str(len(restock_orders) + 1),
        order_number=f"PO-{year}-{seq:04d}",
        items=line_items,
        total_cost=total_cost,
        budget=payload.budget,
        status="Processing",
        created_date=created_dt.isoformat(timespec="seconds"),
        expected_delivery=expected_dt.isoformat(timespec="seconds"),
        lead_time_days=max_lead_time
    )
    restock_orders.append(order.model_dump())
    return order

@app.get("/api/restock/orders", response_model=List[RestockOrder])
def get_restock_orders():
    """Get all submitted restocking orders, most recent first.

    Sorts by numeric id (strictly increasing on append) rather than
    created_date, since created_date has only second-level precision and
    orders placed within the same second would otherwise tie.
    """
    return sorted(restock_orders, key=lambda o: int(o["id"]), reverse=True)

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
