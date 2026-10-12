"""
Pytest configuration and fixtures for backend API tests.
"""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add server directory to path
server_path = Path(__file__).parent.parent.parent / "server"
sys.path.insert(0, str(server_path))

from main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def restock_store(tmp_path, monkeypatch):
    """Isolate restock order writes from the repo's data directory.

    POST /api/restocking/orders is the only endpoint that mutates state, and two
    things leak without this fixture:

    1. It writes server/data/restock_orders.json for real. That file is tracked in
       git, so an unisolated test run leaves a modified data file in the working
       tree. Redirecting DATA_DIR sends the write to tmp_path instead - which only
       works because save_json_file() resolves DATA_DIR at call time rather than
       capturing it as a default argument.
    2. main.py holds a reference to mock_data.restock_orders and the test client
       shares one imported module, so appends survive into later tests. Restoring
       with slice assignment mutates that same list object; rebinding the name
       would leave main.py pointing at the old one.
    """
    import mock_data

    original = list(mock_data.restock_orders)
    monkeypatch.setattr(mock_data, 'DATA_DIR', str(tmp_path))
    yield tmp_path
    mock_data.restock_orders[:] = original


@pytest.fixture
def sample_inventory_item():
    """Sample inventory item for testing."""
    return {
        "id": "1",
        "sku": "PCB-001",
        "name": "Single Layer PCB Assembly",
        "category": "Circuit Boards",
        "warehouse": "San Francisco",
        "quantity_on_hand": 450,
        "reorder_point": 200,
        "unit_cost": 24.99,
        "location": "Warehouse A-12",
        "last_updated": "2025-09-30T10:30:00"
    }


@pytest.fixture
def sample_order():
    """Sample order for testing."""
    return {
        "id": "1",
        "order_number": "ORD-2025-0001",
        "customer": "MegaCorp Industries",
        "items": [
            {
                "sku": "SPR-602",
                "name": "Compression Spring",
                "quantity": 981,
                "unit_price": 89.5
            }
        ],
        "status": "Delivered",
        "warehouse": "Tokyo",
        "category": "Sensors",
        "order_date": "2025-01-08T10:19:00",
        "expected_delivery": "2025-01-21T10:19:00",
        "total_value": 87799.5,
        "actual_delivery": "2025-01-20T10:19:00"
    }
