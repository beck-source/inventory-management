"""
Mock data for the Factory Inventory Management System
This module loads sample data from JSON files for inventory items, orders, demand forecasts, and backlog items.
All data is from September 2025 and includes warehouse, category, and date fields for filtering.
"""

import json
import os
import tempfile

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

# Tasks created from the "My Tasks" modal (in memory only; restart reloads tasks.json)
tasks = load_json_file('tasks.json')

# Load restocking orders submitted from the Restocking tab.
# Unlike the other datasets this one is written back to disk (see save_submitted_orders)
# so submitted orders survive server restarts.
SUBMITTED_ORDERS_FILE = os.path.join(DATA_DIR, 'submitted_orders.json')
submitted_orders = load_json_file('submitted_orders.json') if os.path.exists(SUBMITTED_ORDERS_FILE) else []


def save_submitted_orders(path=None):
    """Persist submitted_orders atomically: write a temp file in the same dir, then os.replace,
    so a crash mid-write never leaves a truncated JSON file behind."""
    path = path or SUBMITTED_ORDERS_FILE
    fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(path), suffix='.tmp')
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(submitted_orders, f, indent=2)
            f.write('\n')
        os.replace(tmp_path, path)
    except Exception:
        os.unlink(tmp_path)
        raise

# All data is now loaded from JSON files in the data/ directory
# This allows for easier maintenance and updates of the sample data
