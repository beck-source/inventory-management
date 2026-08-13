from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders, restock_orders, add_restock_order

app = FastAPI(title="Factory Inventory Management System")

# Quarter mapping for date filtering
QUARTER_MAP = {
    'Q1-2025': ['2025-01', '2025-02', '2025-03'],
    'Q2-2025': ['2025-04', '2025-05', '2025-06'],
    'Q3-2025': ['2025-07', '2025-08', '2025-09'],
    'Q4-2025': ['2025-10', '2025-11', '2025-12']
}

# Supplier lead time in days, by inventory category. An order's lead time is the
# max across its line items, since the whole shipment arrives together.
LEAD_TIME_DAYS = {
    'Circuit Boards': 14,
    'Sensors': 10,
    'Actuators': 21,
    'Controllers': 18,
    'Power Supplies': 12
}
DEFAULT_LEAD_TIME_DAYS = 14  # fallback if inventory.json gains a new category

# Restock target stock level. Mirrors the "adequate" threshold in Inventory.vue
# (quantity_on_hand <= reorder_point * 1.5) so the Restocking and Inventory tabs
# agree on what counts as adequately stocked. Keep the two in step.
TARGET_STOCK_MULTIPLIER = 1.5

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
    name: str
    category: str
    warehouse: str
    unit_cost: float
    quantity_on_hand: int
    reorder_point: int
    target_quantity: int
    shortfall: int
    recommended_quantity: int
    line_cost: float
    lead_time_days: int
    priority: str                        # "critical" | "low"
    fully_covered: bool                  # recommended_quantity == shortfall
    demand_trend: Optional[str] = None   # present only when a forecast exists for this SKU

class RestockRecommendationsResponse(BaseModel):
    budget: float
    budget_used: float
    budget_remaining: float
    # The next three are budget-independent, so a single request gives the client
    # everything it needs to size its slider and explain an empty result.
    total_shortfall_cost: float
    candidate_count: int
    cheapest_unit_cost: Optional[float] = None
    recommendations: List[RestockRecommendation]

class RestockOrderLine(BaseModel):
    sku: str
    name: str
    category: str
    quantity: int
    unit_cost: float   # procurement cost, deliberately not `unit_price` like customer Orders
    line_cost: float

class RestockOrder(BaseModel):
    id: str
    order_number: str
    status: str
    budget: float
    total_value: float
    items: List[RestockOrderLine]
    lead_time_days: int
    submitted_at: str
    expected_delivery: str

class RestockOrderLineRequest(BaseModel):
    sku: str
    quantity: int = Field(gt=0)

class CreateRestockOrderRequest(BaseModel):
    budget: float = Field(ge=0)
    items: List[RestockOrderLineRequest] = Field(min_length=1)

def build_restock_candidates(warehouse: Optional[str] = None,
                            category: Optional[str] = None) -> list:
    """Rank inventory items that need restocking, worst first.

    Ranking is critical items first (at or below their reorder point), then by
    shortfall descending. A demand forecast is attached as `demand_trend` when one
    exists for the SKU and acts only as a tiebreaker - today just PSU-501 overlaps
    the forecast set, so it is informational rather than load-bearing.
    """
    trends = {f['item_sku']: f['trend'] for f in demand_forecasts}
    candidates = []

    for item in apply_filters(inventory_items, warehouse, category):
        # int() is defensive: every reorder_point is currently even so * 1.5 is a
        # whole number, but a future odd value must not produce a fractional target.
        target = int(item['reorder_point'] * TARGET_STOCK_MULTIPLIER)
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
            'target_quantity': target,
            'shortfall': shortfall,
            # <= matches the lowStock test in Inventory.vue, not <
            'priority': 'critical' if item['quantity_on_hand'] <= item['reorder_point'] else 'low',
            'lead_time_days': LEAD_TIME_DAYS.get(item['category'], DEFAULT_LEAD_TIME_DAYS),
            'demand_trend': trends.get(item['sku'])
        })

    trend_rank = {'increasing': 0, 'stable': 1, 'decreasing': 2}
    candidates.sort(key=lambda c: (
        c['priority'] != 'critical',
        -c['shortfall'],
        trend_rank.get(c['demand_trend'], 1),
        -c['shortfall'] * c['unit_cost'],
        # Final tiebreak on sku keeps the order deterministic: HMD-202 and PSU-507
        # match on every preceding key, so without this their order is arbitrary.
        c['sku']
    ))
    return candidates

def fill_budget(candidates: list, budget: float) -> list:
    """Greedily allocate a budget across ranked candidates, partially filling the
    last affordable line.

    Arithmetic is in integer cents because float division misbehaves at exactly the
    boundaries that matter here - floor(8950.0 / 89.5) can yield 99 rather than 100.

    An unaffordable candidate is skipped rather than ending the loop, so leftover
    budget can still go to a cheaper item further down the ranking. The feature
    promises to spend the budget well, and stopping early would leave money unspent
    while an item is still short.
    """
    remaining_cents = int(round(budget * 100))
    picked = []

    for candidate in candidates:
        if remaining_cents <= 0:
            break

        unit_cents = int(round(candidate['unit_cost'] * 100))
        quantity = min(candidate['shortfall'], remaining_cents // unit_cents)
        if quantity <= 0:
            continue

        line_cents = quantity * unit_cents
        remaining_cents -= line_cents
        picked.append({
            **candidate,
            'recommended_quantity': quantity,
            'line_cost': round(line_cents / 100, 2),
            'fully_covered': quantity == candidate['shortfall']
        })

    return picked

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

@app.get("/api/restocking/recommendations", response_model=RestockRecommendationsResponse)
def get_restock_recommendations(
    budget: float = Query(..., ge=0),
    warehouse: Optional[str] = None,
    category: Optional[str] = None
):
    """Recommend inventory items to restock within a budget, worst shortfall first."""
    candidates = build_restock_candidates(warehouse, category)
    recommendations = fill_budget(candidates, budget)

    budget_used = round(sum(r['line_cost'] for r in recommendations), 2)

    return {
        'budget': budget,
        'budget_used': budget_used,
        'budget_remaining': round(budget - budget_used, 2),
        'total_shortfall_cost': round(
            sum(c['shortfall'] * c['unit_cost'] for c in candidates), 2
        ),
        'candidate_count': len(candidates),
        'cheapest_unit_cost': min((c['unit_cost'] for c in candidates), default=None),
        'recommendations': recommendations
    }

@app.get("/api/restocking/orders", response_model=List[RestockOrder])
def get_restock_orders():
    """Get submitted restock orders, newest first.

    Deliberately unfiltered, unlike /api/orders. Every global filter would
    spuriously empty this list: the period filter only offers 2025 months while
    these are submitted now, the status filter has no "Submitted" option, and a
    single restock order can span several warehouses and categories.
    """
    return sorted(restock_orders, key=lambda o: o['submitted_at'], reverse=True)

@app.post("/api/restocking/orders", response_model=RestockOrder, status_code=201)
def create_restock_order(request: CreateRestockOrderRequest):
    """Submit a restock order, pricing every line from inventory and persisting it."""
    seen_skus = set()
    lines = []

    for line in request.items:
        if line.sku in seen_skus:
            raise HTTPException(status_code=400, detail=f"Duplicate sku in order: {line.sku}")
        seen_skus.add(line.sku)

        item = next((i for i in inventory_items if i['sku'] == line.sku), None)
        if not item:
            raise HTTPException(status_code=404, detail=f"Item {line.sku} not found")

        # Price from inventory rather than from the request: a client must not be
        # able to set its own unit cost and slip an order past the budget check.
        lines.append({
            'sku': item['sku'],
            'name': item['name'],
            'category': item['category'],
            'quantity': line.quantity,
            'unit_cost': item['unit_cost'],
            'line_cost': round(line.quantity * item['unit_cost'], 2)
        })

    total_value = round(sum(line['line_cost'] for line in lines), 2)
    # Staying within budget is the whole point of the feature, so an over-budget
    # order is rejected rather than recorded. The tolerance absorbs float noise.
    if total_value > request.budget + 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"Order total {total_value} exceeds budget {request.budget}"
        )

    lead_time_days = max(
        LEAD_TIME_DAYS.get(line['category'], DEFAULT_LEAD_TIME_DAYS) for line in lines
    )
    # Second precision with no timezone, matching the existing date strings in the
    # JSON data (e.g. "2025-09-30T10:30:00").
    submitted_at = datetime.now().replace(microsecond=0)

    return add_restock_order({
        'status': 'Submitted',
        'budget': request.budget,
        'total_value': total_value,
        'items': lines,
        'lead_time_days': lead_time_days,
        'submitted_at': submitted_at.isoformat(),
        'expected_delivery': (submitted_at + timedelta(days=lead_time_days)).isoformat()
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
