#!/usr/bin/env python3
"""
Smoke test for database initialization.

Tests that init_database() creates tables and seeds data correctly.

Usage:
    python3 tests/test_db_init.py
"""

import os
import sqlite3
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.inventory import init_database


def test_db_init():
    """Test database initialization with a clean test database."""
    test_db_path = "test_inventory.db"

    # Clean slate
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    print("🔧 Testing database initialization...")

    # Initialize DB
    init_database(test_db_path)
    print("✓ Database created successfully")

    # Verify DB file exists
    assert os.path.exists(test_db_path), f"DB file not found: {test_db_path}"
    print(f"✓ Database file exists: {test_db_path}")

    # Connect and verify tables
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()

    # Check inventory table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='inventory'"
    )
    assert cursor.fetchone() is not None, "inventory table not found"
    print("✓ inventory table created")

    # Check vendors table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='vendors'"
    )
    assert cursor.fetchone() is not None, "vendors table not found"
    print("✓ vendors table created")

    # Check inventory row count
    cursor.execute("SELECT COUNT(*) FROM inventory")
    inventory_count = cursor.fetchone()[0]
    assert inventory_count >= 4, f"Expected ≥4 inventory rows, got {inventory_count}"
    print(f"✓ Inventory rows: {inventory_count}")

    # Check vendors row count
    cursor.execute("SELECT COUNT(*) FROM vendors")
    vendor_count = cursor.fetchone()[0]
    assert vendor_count >= 4, f"Expected ≥4 vendor rows, got {vendor_count}"
    print(f"✓ Vendor rows: {vendor_count}")

    # Verify sample data (WidgetA)
    cursor.execute("SELECT stock, unit_price FROM inventory WHERE item = 'WidgetA'")
    result = cursor.fetchone()
    assert result == (15, 250.0), f"WidgetA data mismatch: {result}"
    print("✓ Sample data verified (WidgetA: stock=15, price=250.00)")

    # Verify sample data (Widgets Inc.)
    cursor.execute("SELECT trusted FROM vendors WHERE vendor_name = 'Widgets Inc.'")
    result = cursor.fetchone()
    assert result == (1,), f"Widgets Inc. data mismatch: {result}"
    print("✓ Sample data verified (Widgets Inc.: trusted=1)")

    # Test idempotency - call init again
    init_database(test_db_path)
    cursor.execute("SELECT COUNT(*) FROM inventory")
    new_count = cursor.fetchone()[0]
    assert (
        new_count == inventory_count
    ), f"Idempotency failed: count changed from {inventory_count} to {new_count}"
    print("✓ Idempotency test passed (no duplicate inserts)")

    conn.close()

    # Cleanup
    os.remove(test_db_path)
    print(f"✓ Cleanup: removed {test_db_path}")

    print("\n✅ All smoke tests passed!")


if __name__ == "__main__":
    try:
        test_db_init()
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
