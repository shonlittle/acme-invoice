"""
Database initialization and query helpers for inventory/vendor validation.

TODO: [Slice 2] Implement actual database initialization
TODO: [Slice 3] Implement query helpers for validation rules
"""

import sqlite3
from typing import Optional, Tuple

from db.schema import (
    INVENTORY_SEED_DATA,
    INVENTORY_TABLE_SQL,
    VENDORS_SEED_DATA,
    VENDORS_TABLE_SQL,
)


def init_database(db_path: str = "db/inventory.db") -> None:
    """
    Initialize the inventory database with schema and seed data.

    Creates inventory.db if missing, creates tables (inventory, vendors) if they
    don't exist, and seeds initial data only if tables are empty.

    This function is idempotent - safe to call multiple times.

    Args:
        db_path: Path to SQLite database file (default: inventory.db)
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Create tables if they don't exist
        cursor.execute(INVENTORY_TABLE_SQL)
        cursor.execute(VENDORS_TABLE_SQL)

        # Seed inventory table if empty
        cursor.execute("SELECT COUNT(*) FROM inventory")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO inventory VALUES (?, ?, ?, ?, ?, ?, ?)",
                INVENTORY_SEED_DATA,
            )

        # Seed vendors table if empty
        cursor.execute("SELECT COUNT(*) FROM vendors")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO vendors VALUES (?, ?, ?, ?)", VENDORS_SEED_DATA
            )

        conn.commit()
    finally:
        conn.close()


def get_item_info(item: str, db_path: str = "db/inventory.db") -> Optional[dict]:
    """
    Query inventory for an item.

    Returns dict with keys: item, stock, unit_price, category, etc.
    Returns None if item not found.

    TODO: [Slice 3] Implement actual query logic
    """
    return None


def get_vendor_info(
    vendor_name: str, db_path: str = "db/inventory.db"
) -> Optional[dict]:
    """
    Query vendors table for vendor information.

    Returns dict with keys: vendor_name, address, payment_terms, trusted
    Returns None if vendor not found.

    TODO: [Slice 3] Implement actual query logic
    """
    return None


def check_stock_availability(
    item: str, quantity: int, db_path: str = "db/inventory.db"
) -> Tuple[bool, str]:
    """
    Check if requested quantity is available in stock.

    Returns (is_available, message)

    TODO: [Slice 3] Implement actual stock check logic
    Examples:
    - Item not in DB: (False, "Item not found in inventory")
    - Negative qty: (False, "Invalid quantity: -5")
    - Qty > stock: (False, "Requested 20, only 5 in stock")
    - Stock == 0: (False, "Item out of stock")
    - Valid: (True, "OK")
    """
    return (True, "OK")
