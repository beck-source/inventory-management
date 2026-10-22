"""
Mock data for the Factory Inventory Management System
This module loads sample data from JSON files for inventory items, orders, demand forecasts, and backlog items.
All data is from September 2025 and includes warehouse, category, and date fields for filtering.
"""

import json
import os
from datetime import datetime

# Get the directory where this file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

def load_json_file(filename):
    """Load data from a JSON file in the data directory"""
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'r') as f:
        return json.load(f)

# Load all datasets from JSON files
inventory_items = load_json_file('inventory.json')
orders = load_json_file('orders.json')
demand_forecasts = load_json_file('demand_forecasts.json')
backlog_items = load_json_file('backlog_items.json')

# Load spending data
spending_data = load_json_file('spending.json')
spending_summary = spending_data['spending_summary']
monthly_spending = spending_data['monthly_spending']
category_spending = spending_data['category_spending']

# Load transactions
recent_transactions = load_json_file('transactions.json')

# Load purchase orders
purchase_orders = load_json_file('purchase_orders.json')

# All data is now loaded from JSON files in the data/ directory
# This allows for easier maintenance and updates of the sample data


def _parse_datetime(value):
    """Parse an ISO datetime string, returning None when it is missing or malformed."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def compute_category_lead_times(order_list):
    """
    Derive delivery lead time per category from historical orders.

    Nothing in the dataset records a supplier or a lead time, so the only available
    signal is the gap between order_date and expected_delivery on past orders.
    Returns (per-category whole-day means, overall mean) where the overall mean is
    the fallback for a category that has no orders at all.
    """
    gaps_by_category = {}
    all_gaps = []

    for order in order_list:
        ordered = _parse_datetime(order.get('order_date'))
        expected = _parse_datetime(order.get('expected_delivery'))
        if ordered is None or expected is None:
            continue
        gap_days = (expected - ordered).total_seconds() / 86400
        if gap_days < 0:
            continue
        category = order.get('category')
        if category:
            gaps_by_category.setdefault(category, []).append(gap_days)
        all_gaps.append(gap_days)

    def to_whole_days(gaps):
        # int(mean + 0.5) rather than round(): round() uses banker's rounding, so a
        # category averaging exactly 10.5 days would round down to 10 instead of up.
        return int(sum(gaps) / len(gaps) + 0.5)

    default_days = to_whole_days(all_gaps) if all_gaps else 10
    per_category = {category: to_whole_days(gaps) for category, gaps in gaps_by_category.items()}
    return per_category, default_days


CATEGORY_LEAD_TIME_DAYS, DEFAULT_LEAD_TIME_DAYS = compute_category_lead_times(orders)


def lead_time_for_category(category):
    """Delivery lead time in whole days for a category, falling back to the overall mean."""
    return CATEGORY_LEAD_TIME_DAYS.get(category, DEFAULT_LEAD_TIME_DAYS)


# Restocking orders submitted through the UI. In-memory only — never written back to
# disk, so these disappear when the server restarts. Always mutate in place
# (append/clear); rebinding this name would detach main.py's imported reference.
restock_orders = []

# Tasks created through the profile menu's task list. Same in-memory, mutate-in-place
# rules as restock_orders.
tasks = []
