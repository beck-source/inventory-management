import uuid
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel, Field
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders

app = FastAPI(title="Factory Inventory Management System")

# Approximate supplier lead time per category, used to estimate delivery dates
# for restocking orders (server/data has no real supplier data to derive this from).
CATEGORY_LEAD_TIMES = {
    'Circuit Boards': 21,
    'Sensors': 10,
    'Actuators': 18,
    'Controllers': 15,
    'Power Supplies': 12,
}
DEFAULT_LEAD_TIME_DAYS = 14

# Restocking orders are internal purchases, not customer sales. They live in their own
# list so the sales/revenue endpoints that iterate `orders` never count them as revenue.
restock_orders: List[dict] = []
MAX_RESTOCK_BUDGET = 10_000_000

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
    is_restock: Optional[bool] = False
    lead_time_days: Optional[int] = None

class DemandForecast(BaseModel):
    id: str
    item_sku: str
    item_name: str
    current_demand: int
    forecasted_demand: int
    trend: str
    period: str
    category: Optional[str] = None
    unit_cost: Optional[float] = None
    warehouse: Optional[str] = None

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
    category: Optional[str] = None
    unit_cost: Optional[float] = None
    warehouse: Optional[str] = None

class RestockRecommendation(BaseModel):
    sku: str
    name: str
    category: Optional[str] = None
    warehouse: Optional[str] = None
    unit_cost: float
    quantity: int
    subtotal: float
    source: str  # 'backlog' or 'demand'
    days_delayed: Optional[int] = None
    priority: Optional[str] = None
    demand_gap: Optional[int] = None
    trend: Optional[str] = None

class RestockRecommendationsResponse(BaseModel):
    budget: float
    allocated: float
    remaining: float
    items: List[RestockRecommendation]

class RestockOrderItem(BaseModel):
    sku: str
    name: str
    category: Optional[str] = None
    warehouse: Optional[str] = None
    unit_cost: float = Field(gt=0)
    quantity: int = Field(gt=0)

class CreateRestockOrderRequest(BaseModel):
    budget: float = Field(ge=0, le=MAX_RESTOCK_BUDGET)
    items: List[RestockOrderItem] = Field(min_length=1)

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

def build_restock_candidates() -> List[dict]:
    """Build a priority-ordered list of restock candidates: backlogged items
    first (most delayed first), then items with increasing demand forecasts
    that aren't already backlogged (most severe gap first)."""
    candidates = []
    seen_skus = set()

    for item in sorted(backlog_items, key=lambda b: b['days_delayed'], reverse=True):
        shortfall = max(item['quantity_needed'] - item['quantity_available'], 1)
        candidates.append({
            'sku': item['item_sku'],
            'name': item['item_name'],
            'category': item.get('category'),
            'warehouse': item.get('warehouse'),
            'unit_cost': item.get('unit_cost', 0),
            'quantity': shortfall,
            'source': 'backlog',
            'days_delayed': item['days_delayed'],
            'priority': item['priority'],
        })
        seen_skus.add(item['item_sku'])

    increasing = [f for f in demand_forecasts if f['trend'] == 'increasing' and f['item_sku'] not in seen_skus]
    increasing.sort(key=lambda f: f['forecasted_demand'] - f['current_demand'], reverse=True)
    for forecast in increasing:
        gap = forecast['forecasted_demand'] - forecast['current_demand']
        candidates.append({
            'sku': forecast['item_sku'],
            'name': forecast['item_name'],
            'category': forecast.get('category'),
            'warehouse': forecast.get('warehouse'),
            'unit_cost': forecast.get('unit_cost', 0),
            'quantity': gap,
            'source': 'demand',
            'demand_gap': gap,
            'trend': forecast['trend'],
        })

    return candidates

@app.get("/api/restocking/recommendations", response_model=RestockRecommendationsResponse)
def get_restock_recommendations(budget: float = Query(ge=0, le=MAX_RESTOCK_BUDGET)):
    """Recommend items to restock within budget, prioritizing backlog urgency then rising demand.
    Budget bounds also reject nan/inf, which would otherwise crash the quantity math."""
    remaining = budget
    recommendations = []

    for candidate in build_restock_candidates():
        if remaining <= 0:
            break
        unit_cost = candidate['unit_cost'] or 0
        if unit_cost <= 0:
            continue

        quantity = candidate['quantity']
        full_cost = quantity * unit_cost
        if full_cost > remaining:
            # Divide + epsilon instead of float `//`, which can drop a unit (0.3 // 0.1 == 2.0)
            quantity = int(remaining / unit_cost + 1e-9)
        if quantity <= 0:
            continue

        subtotal = round(quantity * unit_cost, 2)
        remaining = round(remaining - subtotal, 2)
        recommendations.append({**candidate, 'quantity': quantity, 'subtotal': subtotal})

    return {
        'budget': budget,
        'allocated': round(budget - remaining, 2),
        'remaining': remaining,
        'items': recommendations,
    }

@app.get("/api/restocking/orders", response_model=List[Order])
def get_restock_orders():
    """List submitted restocking orders (kept separate from sales orders)."""
    return restock_orders

@app.post("/api/restocking/orders", response_model=Order)
def create_restock_order(request: CreateRestockOrderRequest):
    """Submit a restocking order built from recommended items; stored in restock_orders, not the sales orders list."""
    total_value = round(sum(item.quantity * item.unit_cost for item in request.items), 2)
    # Small tolerance for float rounding between the recommendation and the submitted order
    if total_value > request.budget + 0.01:
        raise HTTPException(status_code=400, detail="Order total exceeds budget")

    lead_time_days = max(
        CATEGORY_LEAD_TIMES.get(item.category, DEFAULT_LEAD_TIME_DAYS) for item in request.items
    )

    # Naive local timestamp without microseconds, matching the format of orders.json
    order_date = datetime.now().replace(microsecond=0)
    expected_delivery = order_date + timedelta(days=lead_time_days)

    categories = {item.category for item in request.items if item.category}
    warehouses = {item.warehouse for item in request.items if item.warehouse}

    new_order = {
        'id': f"restock-{uuid.uuid4().hex[:8]}",
        'order_number': f"RESTOCK-{uuid.uuid4().hex[:6].upper()}",
        'customer': 'Internal Restocking',
        'items': [
            {'sku': item.sku, 'name': item.name, 'quantity': item.quantity, 'unit_price': item.unit_cost}
            for item in request.items
        ],
        'status': 'Processing',
        'order_date': order_date.isoformat(),
        'expected_delivery': expected_delivery.isoformat(),
        'total_value': total_value,
        'actual_delivery': None,
        'warehouse': next(iter(warehouses)) if len(warehouses) == 1 else 'Multiple',
        'category': next(iter(categories)) if len(categories) == 1 else 'Multiple',
        'is_restock': True,
        'lead_time_days': lead_time_days,
    }
    restock_orders.append(new_order)
    return new_order

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
