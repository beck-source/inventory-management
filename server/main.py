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

# Category-based lead time mapping (in days)
CATEGORY_LEAD_TIMES = {
    'Circuit Boards': 7,
    'Sensors': 10,
    'Actuators': 14,
    'Controllers': 12,
    'Power Supplies': 5
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
    item_sku: Optional[str] = None
    item_name: Optional[str] = None
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

@app.get("/api/restocking/recommendations")
def get_restocking_recommendations(
    budget: float,
    warehouse: Optional[str] = None,
    category: Optional[str] = None
):
    """
    Generate restocking recommendations based on:
    - Low stock (below reorder point)
    - High forecasted demand
    - Available budget
    """
    # Filter inventory
    filtered_inventory = apply_filters(inventory_items, warehouse, category)

    # Create lookup for demand forecasts by SKU
    demand_lookup = {f['item_sku']: f for f in demand_forecasts}

    recommendations = []

    for item in filtered_inventory:
        # Check if item has demand forecast
        forecast = demand_lookup.get(item['sku'])
        if not forecast:
            continue

        # Calculate if item needs restocking
        is_low_stock = item['quantity_on_hand'] <= item['reorder_point']
        demand_increase = forecast['forecasted_demand'] - forecast['current_demand']

        # Skip if not low stock and no demand increase
        if not is_low_stock and demand_increase <= 0:
            continue

        # Calculate priority score (higher = more urgent)
        # Formula: (demand shortage / stock ratio) with penalties for low stock
        stock_ratio = item['quantity_on_hand'] / max(item['reorder_point'], 1)
        demand_score = demand_increase / max(forecast['current_demand'], 1)
        priority_score = (demand_score * 100) + (50 if is_low_stock else 0) + (30 / max(stock_ratio, 0.1))

        # Calculate recommended quantity
        # Restock to reorder point + forecasted demand increase
        shortfall = max(0, item['reorder_point'] - item['quantity_on_hand'])
        recommended_qty = shortfall + max(0, demand_increase)

        # Get lead time based on category
        lead_time = CATEGORY_LEAD_TIMES.get(item['category'], 14)

        recommendations.append({
            'item_sku': item['sku'],
            'item_name': item['name'],
            'category': item['category'],
            'warehouse': item['warehouse'],
            'current_stock': item['quantity_on_hand'],
            'reorder_point': item['reorder_point'],
            'forecasted_demand': forecast['forecasted_demand'],
            'current_demand': forecast['current_demand'],
            'recommended_quantity': recommended_qty,
            'unit_cost': item['unit_cost'],
            'total_cost': recommended_qty * item['unit_cost'],
            'priority_score': round(priority_score, 2),
            'lead_time_days': lead_time
        })

    # Sort by priority score (highest first)
    recommendations.sort(key=lambda x: x['priority_score'], reverse=True)

    # Filter recommendations to fit within budget
    budget_constrained = []
    running_total = 0.0

    for rec in recommendations:
        if running_total + rec['total_cost'] <= budget:
            budget_constrained.append(rec)
            running_total += rec['total_cost']

    return {
        'recommendations': budget_constrained,
        'total_cost': round(running_total, 2),
        'available_budget': budget,
        'remaining_budget': round(budget - running_total, 2),
        'items_count': len(budget_constrained)
    }

class RestockingRequest(BaseModel):
    budget: float
    recommendations: List[dict]

@app.post("/api/restocking/submit")
def submit_restocking_order(request: RestockingRequest):
    """
    Submit a restocking order based on selected recommendations.
    Creates purchase orders for selected items.
    """
    from datetime import datetime, timedelta

    created_orders = []
    total_cost = 0.0

    for item in request.recommendations:
        # Generate unique order ID
        order_id = f"PO-REST-{len(purchase_orders) + len(created_orders) + 1:04d}"

        # Calculate delivery date based on category lead time
        lead_time = CATEGORY_LEAD_TIMES.get(item['category'], 14)
        expected_delivery = (datetime.now() + timedelta(days=lead_time)).strftime('%Y-%m-%d')

        # Determine supplier based on category
        supplier_map = {
            'Circuit Boards': 'PCB Fabrication Corp',
            'Sensors': 'Sensor Solutions Inc',
            'Actuators': 'Motion Systems Ltd',
            'Controllers': 'Control Tech Industries',
            'Power Supplies': 'PowerTech Suppliers'
        }
        supplier = supplier_map.get(item['category'], 'General Supplier')

        purchase_order = {
            'id': order_id,
            'backlog_item_id': '',  # Not from backlog
            'item_sku': item['item_sku'],
            'item_name': item['item_name'],
            'supplier_name': supplier,
            'quantity': item['quantity'],
            'unit_cost': item['unit_cost'],
            'expected_delivery_date': expected_delivery,
            'status': 'Pending',
            'created_date': datetime.now().strftime('%Y-%m-%d'),
            'notes': f"Restocking order - Category: {item['category']}, Warehouse: {item['warehouse']}"
        }

        purchase_orders.append(purchase_order)
        created_orders.append(purchase_order)
        total_cost += item['quantity'] * item['unit_cost']

    return {
        'success': True,
        'orders_created': len(created_orders),
        'total_cost': round(total_cost, 2),
        'order_ids': [order['id'] for order in created_orders],
        'orders': created_orders
    }

@app.get("/api/purchase-orders", response_model=List[PurchaseOrder])
def get_all_purchase_orders():
    """Get all purchase orders including restocking orders."""
    return purchase_orders

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
