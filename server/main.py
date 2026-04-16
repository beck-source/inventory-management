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
    source: Optional[str] = None  # "restocking" for orders placed via the Restocking tab

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
    quantity_on_hand: int
    reorder_point: int
    quantity_to_order: int
    unit_cost: float
    total_cost: float
    trend: str
    forecasted_demand: int

class SubmitRestockingOrderRequest(BaseModel):
    items: List[dict]
    total_value: float

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

@app.get("/api/restocking/recommendations", response_model=List[RestockingRecommendation])
def get_restocking_recommendations(budget: float = 0):
    """Recommend inventory items to restock within the given budget.

    Algorithm:
    1. Primary candidates: Items below reorder point (critical shortage)
    2. Secondary candidates: Items with increasing demand trend not yet captured (proactive)
    3. Prioritization: Items sorted by trend priority (increasing > stable > decreasing), then by shortage gap
    4. Selection: Greedy algorithm - include items in priority order until budget exhausted

    Returns: Recommended items sorted by priority, each fitting within remaining budget.
    """
    from datetime import datetime, timedelta

    # Build demand forecast lookup by SKU for O(1) access
    demand_by_sku = {f['item_sku']: f for f in demand_forecasts}

    # Trend sort order: increasing demand is highest priority, followed by stable, then decreasing
    # This ensures we restock items with rising demand first (proactive planning)
    trend_priority = {'increasing': 0, 'stable': 1, 'decreasing': 2}

    candidates = []
    seen_skus = set()

    # PHASE 1: Primary candidates - inventory items currently below their reorder point (critical)
    for item in inventory_items:
        qty_to_order = item['reorder_point'] - item['quantity_on_hand']
        if qty_to_order <= 0:
            continue

        forecast = demand_by_sku.get(item['sku'])
        trend = forecast['trend'] if forecast else 'stable'
        forecasted_demand = forecast['forecasted_demand'] if forecast else item['reorder_point']

        candidates.append({
            'sku': item['sku'],
            'name': item['name'],
            'category': item['category'],
            'warehouse': item['warehouse'],
            'quantity_on_hand': item['quantity_on_hand'],
            'reorder_point': item['reorder_point'],
            'quantity_to_order': qty_to_order,
            'unit_cost': item['unit_cost'],
            'total_cost': round(qty_to_order * item['unit_cost'], 2),
            'trend': trend,
            'forecasted_demand': forecasted_demand,
            '_priority': trend_priority.get(trend, 1),
            '_shortage': qty_to_order,
        })
        seen_skus.add(item['sku'])

    # PHASE 2: Secondary candidates - items with increasing demand trend not already captured
    # This enables proactive restocking to meet rising demand before stock falls below reorder point
    inventory_by_sku = {item['sku']: item for item in inventory_items}
    for forecast in demand_forecasts:
        # Skip if already captured in phase 1 or trend is not increasing
        if forecast['item_sku'] in seen_skus or forecast['trend'] != 'increasing':
            continue
        inv_item = inventory_by_sku.get(forecast['item_sku'])
        if not inv_item:
            continue
        # Proactively restock to reorder_point level to meet rising demand
        qty_to_order = inv_item['reorder_point']
        if qty_to_order <= 0:
            continue
        candidates.append({
            'sku': inv_item['sku'],
            'name': inv_item['name'],
            'category': inv_item['category'],
            'warehouse': inv_item['warehouse'],
            'quantity_on_hand': inv_item['quantity_on_hand'],
            'reorder_point': inv_item['reorder_point'],
            'quantity_to_order': qty_to_order,
            'unit_cost': inv_item['unit_cost'],
            'total_cost': round(qty_to_order * inv_item['unit_cost'], 2),
            'trend': 'increasing',
            'forecasted_demand': forecast['forecasted_demand'],
            '_priority': 0,
            '_shortage': qty_to_order,
        })
        seen_skus.add(inv_item['sku'])

    # Sort by trend priority first (increasing > stable > decreasing), then by largest shortage gap
    # This ensures items with rising demand and critical shortages are recommended first
    candidates.sort(key=lambda x: (x['_priority'], -x['_shortage']))

    # PHASE 3: Greedy selection - include items in priority order until budget exhausted
    # This maximizes impact by fitting as many high-priority items as possible within budget
    result = []
    remaining = budget
    for c in candidates:
        if c['total_cost'] <= remaining:
            result.append({k: v for k, v in c.items() if not k.startswith('_')})
            remaining -= c['total_cost']

    return result


@app.post("/api/restocking/orders", response_model=Order)
def submit_restocking_order(request: SubmitRestockingOrderRequest):
    """Submit a restocking order. Appended to the shared orders list so it appears in Orders tab."""
    from datetime import datetime, timedelta

    now = datetime.now()
    # Use a prefix and running count to generate a collision-resistant order number
    restocking_count = sum(1 for o in orders if o.get('source') == 'restocking')
    order_number = f"RST-{now.year}-{str(restocking_count + 1).zfill(4)}"
    order_id = f"rst-{now.strftime('%Y%m%d%H%M%S')}-{restocking_count + 1}"

    new_order = {
        'id': order_id,
        'order_number': order_number,
        'customer': 'Internal - Restocking',
        'items': request.items,
        'status': 'Processing',
        'order_date': now.isoformat(),
        'expected_delivery': (now + timedelta(days=14)).isoformat(),
        'total_value': request.total_value,
        'actual_delivery': None,
        'warehouse': None,
        'category': None,
        'source': 'restocking',  # tag so the Orders tab can show a dedicated section
    }

    orders.append(new_order)
    return new_order


@app.get("/api/restocking/orders", response_model=List[Order])
def get_restocking_orders():
    """Return all submitted restocking orders (unfiltered, always current-date data)."""
    return [o for o in orders if o.get('source') == 'restocking']


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
