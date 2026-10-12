from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders, submitted_restock_orders

app = FastAPI(title="Factory Inventory Management System")

# Supplier delivery lead time in days, keyed by item category.
# Fixed per category (not random) so the same recommendation always yields the same delivery date.
CATEGORY_LEAD_TIME_DAYS = {
    'Seals': 7,
    'Filtration': 9,
    'Sensors': 10,
    'Components': 10,
    'Power Supplies': 12,
    'Circuit Boards': 14,
    'Controllers': 18,
    'Mechanical': 21,
    'Actuators': 21,
    'Valves': 24,
    'Motors': 28,
}
DEFAULT_LEAD_TIME_DAYS = 14

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
    category: Optional[str] = None
    unit_cost: Optional[float] = None

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

class RestockRecommendationItem(BaseModel):
    item_sku: str
    item_name: str
    category: str
    trend: str
    forecasted_demand: int
    quantity_on_hand: int
    shortfall: int
    recommended_quantity: int
    unit_cost: float
    line_total: float
    lead_time_days: int
    fully_funded: bool

class RestockRecommendation(BaseModel):
    budget: float
    items: List[RestockRecommendationItem]
    total_cost: float
    remaining_budget: float
    total_units: int
    max_lead_time_days: int
    unfunded_items: List[dict]

class CreateRestockOrderRequest(BaseModel):
    budget: float
    items: List[RestockRecommendationItem]

class SubmittedRestockOrder(BaseModel):
    id: str
    order_number: str
    status: str
    budget: float
    order_date: str
    expected_delivery: str
    lead_time_days: int
    total_value: float
    total_units: int
    items: List[dict]

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

def _lead_time_for(category: Optional[str]) -> int:
    """Supplier lead time in days for a category, falling back to the default."""
    return CATEGORY_LEAD_TIME_DAYS.get(category or '', DEFAULT_LEAD_TIME_DAYS)

def _on_hand_for(sku: str) -> int:
    """Total quantity on hand for a SKU across all warehouses (0 if the SKU is not stocked)."""
    return sum(item['quantity_on_hand'] for item in inventory_items if item['sku'] == sku)

@app.get("/api/restock/recommendations", response_model=RestockRecommendation)
def get_restock_recommendations(budget: float = Query(0, ge=0)):
    """Recommend restock quantities from the demand forecast that fit within a budget.

    Gap-priority greedy allocation: rank items by shortfall (forecasted demand minus quantity on
    hand), then buy the full shortfall for each item top-down until the budget runs out. The first
    item that cannot be fully funded gets a partial quantity for whatever budget remains.
    """
    candidates = []
    for forecast in demand_forecasts:
        unit_cost = forecast.get('unit_cost') or 0
        if unit_cost <= 0:
            continue

        on_hand = _on_hand_for(forecast['item_sku'])
        shortfall = forecast['forecasted_demand'] - on_hand
        if shortfall <= 0:
            continue

        candidates.append({
            'item_sku': forecast['item_sku'],
            'item_name': forecast['item_name'],
            'category': forecast.get('category') or 'Uncategorized',
            'trend': forecast['trend'],
            'forecasted_demand': forecast['forecasted_demand'],
            'quantity_on_hand': on_hand,
            'shortfall': shortfall,
            'unit_cost': unit_cost,
        })

    # Biggest shortfall first; increasing-trend items win ties since their gap is still widening
    candidates.sort(key=lambda c: (-c['shortfall'], c['trend'] != 'increasing', c['item_sku']))

    remaining = budget
    recommended = []
    unfunded = []

    for candidate in candidates:
        affordable_qty = int(remaining // candidate['unit_cost'])
        quantity = min(candidate['shortfall'], affordable_qty)

        if quantity <= 0:
            unfunded.append({
                'item_sku': candidate['item_sku'],
                'item_name': candidate['item_name'],
                'shortfall': candidate['shortfall'],
                'unit_cost': candidate['unit_cost'],
                'shortfall_cost': round(candidate['shortfall'] * candidate['unit_cost'], 2),
            })
            continue

        line_total = round(quantity * candidate['unit_cost'], 2)
        remaining -= line_total
        recommended.append({
            **candidate,
            'recommended_quantity': quantity,
            'line_total': line_total,
            'lead_time_days': _lead_time_for(candidate['category']),
            'fully_funded': quantity == candidate['shortfall'],
        })

    total_cost = round(sum(item['line_total'] for item in recommended), 2)

    return {
        'budget': budget,
        'items': recommended,
        'total_cost': total_cost,
        'remaining_budget': round(budget - total_cost, 2),
        'total_units': sum(item['recommended_quantity'] for item in recommended),
        # Order-level lead time is the slowest line: the order is not complete until every item lands
        'max_lead_time_days': max((item['lead_time_days'] for item in recommended), default=0),
        'unfunded_items': unfunded,
    }

@app.get("/api/restock-orders", response_model=List[SubmittedRestockOrder])
def get_submitted_restock_orders():
    """Get all submitted restocking orders, newest first"""
    return list(reversed(submitted_restock_orders))

@app.post("/api/restock-orders", response_model=SubmittedRestockOrder, status_code=201)
def create_restock_order(request: CreateRestockOrderRequest):
    """Submit a restocking order built from budget-based recommendations"""
    if not request.items:
        raise HTTPException(status_code=400, detail="Cannot submit a restocking order with no items")

    items = []
    for item in request.items:
        lead_time = _lead_time_for(item.category)
        items.append({
            'sku': item.item_sku,
            'name': item.item_name,
            'category': item.category,
            'quantity': item.recommended_quantity,
            'unit_price': item.unit_cost,
            'line_total': round(item.recommended_quantity * item.unit_cost, 2),
            'lead_time_days': lead_time,
            'expected_delivery': (datetime.now() + timedelta(days=lead_time)).isoformat(timespec='seconds'),
        })

    order_lead_time = max(item['lead_time_days'] for item in items)
    now = datetime.now()

    order = {
        'id': str(len(submitted_restock_orders) + 1),
        'order_number': f"RST-{now.year}-{len(submitted_restock_orders) + 1:04d}",
        'status': 'Submitted',
        'budget': request.budget,
        'order_date': now.isoformat(timespec='seconds'),
        'expected_delivery': (now + timedelta(days=order_lead_time)).isoformat(timespec='seconds'),
        'lead_time_days': order_lead_time,
        'total_value': round(sum(item['line_total'] for item in items), 2),
        'total_units': sum(item['quantity'] for item in items),
        'items': items,
    }

    submitted_restock_orders.append(order)
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
