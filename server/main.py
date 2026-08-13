from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders
import json
import os
from datetime import datetime, timedelta

app = FastAPI(title="Factory Inventory Management System")

# Data directory for persistent storage
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

def load_json_file(filename):
    """Load JSON data from file"""
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json_file(filename, data):
    """Save JSON data to file"""
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

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

class RestockingRecommendation(BaseModel):
    item_sku: str
    item_name: str
    current_stock: int
    recommended_quantity: int
    unit_cost: float
    total_cost: float
    demand_forecast: int
    trend: str
    urgency_score: float
    reason: str

class CreateRestockingOrderRequest(BaseModel):
    items: List[dict]
    budget: float
    warehouse: Optional[str] = None
    category: Optional[str] = None

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
def get_restocking_recommendations(
    budget: float,
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 20
):
    """Get smart restocking recommendations based on budget and filters"""
    recommendations = []

    # Find max forecasted demand for normalization
    max_demand = max([f.get('forecasted_demand', 0) for f in demand_forecasts], default=1)
    min_cost = min([i.get('unit_cost', float('inf')) for i in inventory_items], default=1)

    # Create a lookup for inventory items by SKU
    inventory_by_sku = {item['sku']: item for item in inventory_items}

    # Calculate recommendations by cross-referencing demand forecasts with inventory
    for forecast in demand_forecasts:
        forecast_sku = forecast.get('item_sku')
        if forecast_sku not in inventory_by_sku:
            continue

        inventory = inventory_by_sku[forecast_sku]

        # Apply warehouse filter
        if warehouse and warehouse != 'all' and inventory.get('warehouse') != warehouse:
            continue

        # Apply category filter
        if category and category != 'all' and inventory.get('category', '').lower() != category.lower():
            continue

        # Calculate component scores
        # Demand score (40% weight) - normalized and trend-adjusted
        demand_score = (forecast.get('forecasted_demand', 0) / max_demand) * 100
        trend = forecast.get('trend', 'stable')
        trend_multiplier = 1.2 if trend == 'increasing' else (0.7 if trend == 'decreasing' else 1.0)
        demand_score *= trend_multiplier

        # Stock score (35% weight) - how much below reorder point
        quantity_on_hand = inventory.get('quantity_on_hand', 0)
        reorder_point = inventory.get('reorder_point', 0)
        stock_deficit = max(0, (reorder_point - quantity_on_hand) / reorder_point) if reorder_point > 0 else 0
        stock_score = stock_deficit * 100

        # Cost score (25% weight) - inverse of cost (cheaper = higher score)
        unit_cost = inventory.get('unit_cost', 1)
        cost_score = (min_cost / unit_cost) * 100 if unit_cost > 0 else 0

        # Composite urgency score
        urgency_score = (0.40 * demand_score) + (0.35 * stock_score) + (0.25 * cost_score)

        # Recommended quantity: forecasted demand or enough to reach reorder point, whichever is higher
        recommended_quantity = max(
            forecast.get('forecasted_demand', 0),
            max(0, reorder_point - quantity_on_hand)
        )

        if recommended_quantity == 0:
            recommended_quantity = reorder_point or 10

        total_cost = recommended_quantity * unit_cost

        # Generate reason
        reasons = []
        if trend == 'increasing':
            reasons.append("High demand trend")
        if stock_deficit > 0.5:
            reasons.append("Critical stock level")
        elif stock_deficit > 0:
            reasons.append("Low stock")
        reasons.append(f"Cost: ${unit_cost:.2f}")
        reason = " + ".join(reasons)

        recommendations.append(RestockingRecommendation(
            item_sku=forecast_sku,
            item_name=forecast.get('item_name', 'Unknown'),
            current_stock=quantity_on_hand,
            recommended_quantity=recommended_quantity,
            unit_cost=unit_cost,
            total_cost=total_cost,
            demand_forecast=forecast.get('forecasted_demand', 0),
            trend=trend,
            urgency_score=round(urgency_score, 1),
            reason=reason
        ))

    # Sort by urgency score descending
    recommendations.sort(key=lambda x: x.urgency_score, reverse=True)

    # Apply budget constraint - greedy selection
    selected = []
    total_cost = 0
    for rec in recommendations:
        if total_cost + rec.total_cost <= budget:
            selected.append(rec)
            total_cost += rec.total_cost
            if len(selected) >= limit:
                break

    return selected

@app.post("/api/restocking-orders", response_model=Order, status_code=201)
def create_restocking_order(request: CreateRestockingOrderRequest):
    """Create and persist a new restocking order"""
    try:
        # Reload current orders from file to get fresh state
        orders_data = load_json_file('orders.json')
    except:
        orders_data = []

    # Generate next ID
    existing_ids = [int(o.get('id', '0')) for o in orders_data]
    next_id = str(max(existing_ids) + 1 if existing_ids else 100)

    # Generate order number
    order_number = f"RST-2025-{int(next_id):04d}"

    # Calculate total value
    total_value = sum(item.get('quantity', 0) * item.get('unit_price', 0) for item in request.items)

    # Calculate expected delivery: 30 days from now (from "Next 30 days" demand forecast period)
    order_date = datetime.now().isoformat()
    expected_delivery = (datetime.now() + timedelta(days=30)).isoformat()

    # Create order object
    order = {
        "id": next_id,
        "order_number": order_number,
        "customer": "Internal Restocking",
        "items": request.items,
        "status": "Restocking Order",
        "warehouse": request.warehouse or "all",
        "category": request.category or "all",
        "order_date": order_date,
        "expected_delivery": expected_delivery,
        "total_value": round(total_value, 2)
    }

    # Persist to file
    orders_data.append(order)
    save_json_file('orders.json', orders_data)

    # Update in-memory orders list
    orders.append(order)

    return order

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
