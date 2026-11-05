from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime, timedelta
import math
from pydantic import BaseModel, Field
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
    # Restocking inputs; defaults keep older data without these fields valid
    unit_cost: float = 0
    quantity_on_hand: int = 0
    lead_time_days: int = 0

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


class RestockOrderItem(BaseModel):
    sku: str
    name: str
    quantity: int = Field(gt=0)
    unit_cost: float

class CreateRestockOrderRequest(BaseModel):
    budget: float = Field(ge=0)
    items: List[RestockOrderItem]

class RestockOrder(BaseModel):
    id: str
    order_number: str
    items: List[RestockOrderItem]
    total_value: float
    budget: float
    status: str
    order_date: str
    lead_time_days: int
    expected_delivery: str

# Submitted restocking orders live in memory only and reset when the server restarts
restock_orders: List[dict] = []

# Lower rank = restocked first when the budget cannot cover everything
TREND_RANK = {'increasing': 0, 'stable': 1, 'decreasing': 2}

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

@app.get("/api/restocking/recommendations")
def get_restock_recommendations(budget: float = Query(..., ge=0)):
    """Recommend forecast items to restock within a budget, greedy by trend then shortfall"""
    candidates = []
    for f in demand_forecasts:
        shortfall = f["forecasted_demand"] - f.get("quantity_on_hand", 0)
        if shortfall > 0 and f.get("unit_cost", 0) > 0:
            candidates.append({**f, "shortfall": shortfall})

    # Growing items first so a small budget goes to the demand that is rising; biggest gap breaks ties
    candidates.sort(key=lambda f: (TREND_RANK.get(f["trend"], 3), -f["shortfall"]))

    remaining = budget
    items = []
    for f in candidates:
        # Buy as much of the shortfall as the remaining budget allows (partial fills are intended)
        quantity = min(f["shortfall"], math.floor(remaining / f["unit_cost"]))
        if quantity <= 0:
            continue
        line_total = round(quantity * f["unit_cost"], 2)
        remaining -= line_total
        items.append({
            "sku": f["item_sku"],
            "name": f["item_name"],
            "trend": f["trend"],
            "quantity_on_hand": f["quantity_on_hand"],
            "forecasted_demand": f["forecasted_demand"],
            "shortfall": f["shortfall"],
            "quantity": quantity,
            "unit_cost": f["unit_cost"],
            "line_total": line_total,
            "lead_time_days": f["lead_time_days"],
        })

    total_cost = round(sum(i["line_total"] for i in items), 2)
    return {
        "budget": budget,
        "items": items,
        "total_cost": total_cost,
        "remaining_budget": round(budget - total_cost, 2),
        "lead_time_days": max((i["lead_time_days"] for i in items), default=0),
    }

@app.post("/api/restocking/orders", response_model=RestockOrder, status_code=201)
def create_restock_order(request: CreateRestockOrderRequest):
    """Submit a restocking order; costs and lead time come from server data, not the client"""
    if not request.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")

    forecasts_by_sku = {f["item_sku"]: f for f in demand_forecasts}
    items = []
    for item in request.items:
        forecast = forecasts_by_sku.get(item.sku)
        if not forecast:
            raise HTTPException(status_code=400, detail=f"Unknown SKU: {item.sku}")
        # Trusting client-supplied prices would let a request undercut the budget check
        items.append({"sku": item.sku, "name": forecast["item_name"],
                      "quantity": item.quantity, "unit_cost": forecast["unit_cost"]})

    total_value = round(sum(i["quantity"] * i["unit_cost"] for i in items), 2)
    if total_value > request.budget:
        raise HTTPException(status_code=400, detail="Order total exceeds budget")

    # The slowest item gates the whole order's delivery
    lead_time_days = max(forecasts_by_sku[i["sku"]]["lead_time_days"] for i in items)
    now = datetime.now().replace(microsecond=0)
    order = {
        "id": str(len(restock_orders) + 1),
        "order_number": f"RST-{now.year}-{len(restock_orders) + 1:04d}",
        "items": items,
        "total_value": total_value,
        "budget": request.budget,
        "status": "Submitted",
        "order_date": now.isoformat(),
        "lead_time_days": lead_time_days,
        "expected_delivery": (now + timedelta(days=lead_time_days)).isoformat(),
    }
    restock_orders.append(order)
    return order

@app.get("/api/restocking/orders", response_model=List[RestockOrder])
def get_restock_orders():
    """Get submitted restocking orders, newest first"""
    return list(reversed(restock_orders))

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
