"""
Database initialization and query helpers for inventory/vendor validation.

Provides:
- SQLite database initialization with inventory and vendors tables
- Seed data for testing and development
- Query helpers for validation rules
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

    Returns dict with keys: item, stock, unit_price, category,
    min_order_qty, max_order_qty, active
    Returns None if item not found.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT item, stock, unit_price, category, min_order_qty, max_order_qty, active "
        "FROM inventory WHERE item = ?",
        (item,),
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "item": row[0],
        "stock": row[1],
        "unit_price": row[2],
        "category": row[3],
        "min_order_qty": row[4],
        "max_order_qty": row[5],
        "active": row[6],
    }


def get_vendor_info(
    vendor_name: str, db_path: str = "db/inventory.db"
) -> Optional[dict]:
    """
    Query vendors table for vendor information.

    Returns dict with keys: vendor_name, address, payment_terms, trusted
    Returns None if vendor not found.

    """
    return None


def check_stock_availability(
    item: str, quantity: int, db_path: str = "db/inventory.db"
) -> Tuple[bool, str]:
    """
    Check if requested quantity is available in stock.

    Returns (is_available, message)

    Examples:
    - Item not in DB: (False, "Item not found in inventory")
    - Negative qty: (False, "Invalid quantity: -5")
    - Qty > stock: (False, "Requested 20, only 5 in stock")
    - Stock == 0: (False, "Item out of stock")
    - Valid: (True, "OK")
    """
    # Check for negative quantity
    if quantity < 0:
        return (False, f"Invalid quantity: {quantity}")

    # Query inventory
    item_info = get_item_info(item, db_path)

    if item_info is None:
        return (False, "Item not found in inventory")

    stock = item_info["stock"]

    if stock == 0:
        return (False, "Item out of stock")

    if quantity > stock:
        return (False, f"Requested {quantity}, only {stock} in stock")

    return (True, "OK")
