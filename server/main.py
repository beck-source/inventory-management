import math
import random
import uuid
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders

app = FastAPI(title="Factory Inventory Management System")

# Restocking orders created at runtime (not loaded from JSON like everything else)
restocking_orders: list = []

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

class RestockingRecommendationItem(BaseModel):
    sku: str
    item_name: str
    category: str
    warehouse: str
    quantity_on_hand: int
    reorder_point: int
    unit_cost: float
    current_demand: int
    forecasted_demand: int
    trend: str
    target_quantity: int
    recommended_quantity: int
    line_cost: float
    fully_funded: bool
    urgency_score: int

class RestockingRecommendationResponse(BaseModel):
    budget: float
    allocated_cost: float
    remaining_budget: float
    items: List[RestockingRecommendationItem]

class RestockingOrderRequest(BaseModel):
    budget: float
    warehouse: Optional[str] = None
    category: Optional[str] = None

class RestockingOrderItem(BaseModel):
    sku: str
    item_name: str
    quantity: int
    unit_cost: float
    line_cost: float

class RestockingOrder(BaseModel):
    id: str
    order_number: str
    budget: float
    total_cost: float
    items: List[RestockingOrderItem]
    order_date: str
    lead_time_days: int
    expected_delivery: str
    status: str

# Restocking recommendation engine

def compute_restocking_recommendations(budget: float, warehouse: Optional[str] = None, category: Optional[str] = None) -> dict:
    """Cross-reference demand forecasts with inventory and greedily fund the most
    urgent (closest to/below reorder_point) items first within the given budget."""
    filtered_inventory = apply_filters(inventory_items, warehouse, category)
    inventory_by_sku = {item['sku']: item for item in filtered_inventory}

    candidates = []
    for forecast in demand_forecasts:
        inv = inventory_by_sku.get(forecast['item_sku'])
        if not inv:
            continue

        target_level = math.ceil(inv['reorder_point'] * 1.5)
        if inv['quantity_on_hand'] >= target_level:
            continue

        target_quantity = target_level - inv['quantity_on_hand']
        urgency_score = inv['quantity_on_hand'] - inv['reorder_point']
        demand_growth = forecast['forecasted_demand'] - forecast['current_demand']

        candidates.append({
            'sku': inv['sku'],
            'item_name': forecast['item_name'],
            'category': inv['category'],
            'warehouse': inv['warehouse'],
            'quantity_on_hand': inv['quantity_on_hand'],
            'reorder_point': inv['reorder_point'],
            'unit_cost': inv['unit_cost'],
            'current_demand': forecast['current_demand'],
            'forecasted_demand': forecast['forecasted_demand'],
            'trend': forecast['trend'],
            'target_quantity': target_quantity,
            'urgency_score': urgency_score,
            'demand_growth': demand_growth,
        })

    candidates.sort(key=lambda c: (c['urgency_score'], -c['demand_growth'], c['sku']))

    remaining_budget = budget
    items = []
    for c in candidates:
        unit_cost = c['unit_cost']
        if unit_cost <= 0:
            affordable_qty = c['target_quantity']
        else:
            affordable_qty = min(c['target_quantity'], math.floor(remaining_budget / unit_cost))

        if affordable_qty < 1:
            continue

        line_cost = round(affordable_qty * unit_cost, 2)
        remaining_budget = round(remaining_budget - line_cost, 2)

        items.append(RestockingRecommendationItem(
            sku=c['sku'],
            item_name=c['item_name'],
            category=c['category'],
            warehouse=c['warehouse'],
            quantity_on_hand=c['quantity_on_hand'],
            reorder_point=c['reorder_point'],
            unit_cost=unit_cost,
            current_demand=c['current_demand'],
            forecasted_demand=c['forecasted_demand'],
            trend=c['trend'],
            target_quantity=c['target_quantity'],
            recommended_quantity=affordable_qty,
            line_cost=line_cost,
            fully_funded=(affordable_qty == c['target_quantity']),
            urgency_score=c['urgency_score'],
        ))

    allocated_cost = round(budget - remaining_budget, 2)
    return {
        'budget': budget,
        'allocated_cost': allocated_cost,
        'remaining_budget': remaining_budget,
        'items': items,
    }

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

@app.get("/api/restocking/recommendations", response_model=RestockingRecommendationResponse)
def get_restocking_recommendations(
    budget: float,
    warehouse: Optional[str] = None,
    category: Optional[str] = None
):
    """Recommend items to restock within a budget, prioritized by urgency (closest to/below reorder point)"""
    if budget < 0:
        raise HTTPException(status_code=400, detail="Budget must be non-negative")
    return compute_restocking_recommendations(budget, warehouse, category)

@app.post("/api/restocking/orders", response_model=RestockingOrder, status_code=201)
def create_restocking_order(request: RestockingOrderRequest):
    """Place a restocking order for the current budget-constrained recommendation set.
    Recommendations are recomputed server-side rather than trusted from the client,
    since quantities are automatic-only (not user-editable)."""
    if request.budget <= 0:
        raise HTTPException(status_code=400, detail="Budget must be greater than zero")

    rec = compute_restocking_recommendations(request.budget, request.warehouse, request.category)
    if not rec['items']:
        raise HTTPException(status_code=400, detail="No items could be recommended for this budget")

    lead_time_days = random.randint(5, 14)
    order_date = datetime.now()
    expected_delivery = order_date + timedelta(days=lead_time_days)

    order = {
        "id": str(uuid.uuid4()),
        "order_number": f"RO-{len(restocking_orders) + 1:04d}",
        "budget": request.budget,
        "total_cost": rec['allocated_cost'],
        "items": [
            {
                "sku": item.sku,
                "item_name": item.item_name,
                "quantity": item.recommended_quantity,
                "unit_cost": item.unit_cost,
                "line_cost": item.line_cost,
            }
            for item in rec['items']
        ],
        "order_date": order_date.isoformat(),
        "lead_time_days": lead_time_days,
        "expected_delivery": expected_delivery.isoformat(),
        "status": "Ordered",
    }
    restocking_orders.append(order)
    return order

@app.get("/api/restocking/orders", response_model=List[RestockingOrder])
def get_restocking_orders():
    """Get all submitted restocking orders"""
    return restocking_orders

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
