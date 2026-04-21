from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, date
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders

# In-memory store for submitted restocking orders.
restocking_orders: list[dict] = []

app = FastAPI(title="Factory Inventory Management System")

def _parse_quarter(key: str) -> Optional[list[str]]:
    """Parse a 'Q<N>-<YYYY>' key into its three YYYY-MM month prefixes.

    Returns None for any malformed or out-of-range input — callers treat
    that as 'no orders match' rather than silently passing the filter.
    """
    try:
        q_part, year_part = key.split('-')
        quarter_num = int(q_part[1:])
        year = int(year_part)
    except (ValueError, IndexError):
        return None
    if not 1 <= quarter_num <= 4:
        return None
    start = (quarter_num - 1) * 3 + 1
    return [f"{year}-{m:02d}" for m in range(start, start + 3)]

def filter_by_month(items: list, month: Optional[str]) -> list:
    """Filter items by month (YYYY-MM) or quarter (Q<N>-<YYYY>) based on order_date."""
    if not month or month == 'all':
        return items

    if month.startswith('Q'):
        months = _parse_quarter(month)
        if months is None:
            return []
        return [item for item in items if any(m in item.get('order_date', '') for m in months)]

    # Direct month match (YYYY-MM)
    return [item for item in items if month in item.get('order_date', '')]

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
    lead_time_days: int

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

class RestockingCandidate(BaseModel):
    sku: str
    name: str
    category: str
    warehouse: str
    quantity_on_hand: int
    forecasted_demand: int
    shortfall: int
    recommended_qty: int
    unit_cost: float
    estimated_cost: float
    lead_time_days: int
    trend: str

class RestockingOrderLine(BaseModel):
    sku: str
    name: str
    quantity: int = Field(gt=0)
    unit_cost: float = Field(ge=0)
    lead_time_days: int = Field(ge=0)
    subtotal: float = Field(ge=0)

class RestockingOrder(BaseModel):
    id: str
    submitted_date: str
    status: str
    items: List[RestockingOrderLine]
    total_cost: float
    max_lead_time_days: int
    expected_delivery_date: str

class CreateRestockingOrderRequest(BaseModel):
    items: List[RestockingOrderLine]

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
    """Get quarterly performance reports for every year present in the data."""
    quarters = {}

    for order in orders:
        order_date = order.get('order_date', '')
        if len(order_date) < 7:
            continue
        try:
            year = int(order_date[:4])
            month_num = int(order_date[5:7])
        except ValueError:
            continue
        if not 1 <= month_num <= 12:
            continue
        quarter = f"Q{(month_num - 1) // 3 + 1}-{year}"

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

@app.get("/api/restocking/candidates", response_model=List[RestockingCandidate])
def get_restocking_candidates(
    warehouse: Optional[str] = None,
    category: Optional[str] = None
):
    """Get restocking candidates by joining demand forecasts with inventory items.

    Returns inventory items where forecasted demand exceeds quantity on hand,
    sorted by shortfall descending.
    """
    # Build a lookup from SKU to inventory item for efficient joining.
    inventory_by_sku: dict[str, dict] = {item["sku"]: item for item in inventory_items}

    candidates = []
    for forecast in demand_forecasts:
        item_sku = forecast["item_sku"]
        if item_sku not in inventory_by_sku:
            continue

        inventory_item = inventory_by_sku[item_sku]
        shortfall = forecast["forecasted_demand"] - inventory_item["quantity_on_hand"]
        if shortfall <= 0:
            continue

        candidates.append({
            "sku": item_sku,
            "name": inventory_item["name"],
            "category": inventory_item["category"],
            "warehouse": inventory_item["warehouse"],
            "quantity_on_hand": inventory_item["quantity_on_hand"],
            "forecasted_demand": forecast["forecasted_demand"],
            "shortfall": shortfall,
            "recommended_qty": shortfall,
            "unit_cost": inventory_item["unit_cost"],
            "estimated_cost": round(shortfall * inventory_item["unit_cost"], 2),
            "lead_time_days": inventory_item["lead_time_days"],
            "trend": forecast["trend"],
        })

    # Apply warehouse and category filters on the inventory-side fields.
    candidates = apply_filters(candidates, warehouse, category)

    # Sort by shortfall descending so highest-priority items appear first.
    candidates.sort(key=lambda c: c["shortfall"], reverse=True)

    return candidates


@app.post("/api/restocking/orders", response_model=RestockingOrder)
def create_restocking_order(request: CreateRestockingOrderRequest):
    """Submit a new restocking order from the provided line items."""
    if not request.items:
        raise HTTPException(status_code=400, detail="No items provided")

    order_number = len(restocking_orders) + 1
    order_id = f"RO-{date.today().year}-{order_number:04d}"

    total_cost = round(sum(line.subtotal for line in request.items), 2)
    max_lead_time_days = max(line.lead_time_days for line in request.items)
    expected_delivery_date = (date.today() + timedelta(days=max_lead_time_days)).isoformat()

    order = {
        "id": order_id,
        "submitted_date": datetime.now().isoformat(),
        "status": "Submitted",
        "items": [line.model_dump() for line in request.items],
        "total_cost": total_cost,
        "max_lead_time_days": max_lead_time_days,
        "expected_delivery_date": expected_delivery_date,
    }

    restocking_orders.append(order)
    return order


@app.get("/api/restocking/orders", response_model=List[RestockingOrder])
def get_restocking_orders():
    """Get all submitted restocking orders, sorted by submitted date descending."""
    return sorted(restocking_orders, key=lambda o: o["submitted_date"], reverse=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
