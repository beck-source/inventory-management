"""
Mock data for the Factory Inventory Management System
This module loads sample data from JSON files for inventory items, orders, demand forecasts, and backlog items.
All data is from September 2025 and includes warehouse, category, and date fields for filtering.
"""

import json
import os
import threading

# Get the directory where this file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

def load_json_file(filename):
    """Load data from a JSON file in the data directory"""
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json_file(filename, data):
    """Write data to a JSON file in the data directory.

    Writes to a temp file and then os.replace()s it onto the target, which is an
    atomic swap - a crash mid-write can never leave a truncated, unparseable JSON
    file behind. DATA_DIR is looked up on each call rather than captured as a
    default argument, so tests can redirect writes away from the real data dir.
    """
    filepath = os.path.join(DATA_DIR, filename)
    tmp_path = filepath + '.tmp'
    with open(tmp_path, 'w') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_path, filepath)

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

# Load restock orders - the only dataset that is mutated at runtime
restock_orders = load_json_file('restock_orders.json')

# FastAPI runs sync `def` endpoints in a threadpool, so two concurrent POSTs could
# interleave their read-modify-write of restock_orders and hand out duplicate ids.
# Serializing the whole append (id assignment included) rules that out.
_restock_lock = threading.Lock()

def add_restock_order(order):
    """Assign an id and order number to a restock order, persist it, then publish it.

    Writing to disk before appending to the in-memory list means a failed write
    can never leave an order visible in the API but missing from the file.
    """
    with _restock_lock:
        next_id = max(
            (int(o['id']) for o in restock_orders if str(o['id']).isdigit()),
            default=0
        ) + 1
        stored = {
            **order,
            'id': str(next_id),
            # RST- prefix keeps these distinguishable from the ORD- customer orders
            'order_number': 'RST-{}-{:04d}'.format(order['submitted_at'][:4], next_id)
        }
        save_json_file('restock_orders.json', restock_orders + [stored])
        restock_orders.append(stored)
    return stored

# All data is now loaded from JSON files in the data/ directory
# This allows for easier maintenance and updates of the sample data
