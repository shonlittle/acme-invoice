"""
Database initialization and query helpers for inventory/vendor validation.

Provides:
- SQLite database initialization with inventory and vendors tables
- Seed data for testing and development
- Query helpers for validation rules
- Context-managed connection handling
"""

import sqlite3
from contextlib import contextmanager
from typing import Dict, List, Optional, Tuple

from db.schema import (
    INVENTORY_SEED_DATA,
    INVENTORY_TABLE_SQL,
    VENDORS_SEED_DATA,
    VENDORS_TABLE_SQL,
)

DEFAULT_DB_PATH = "db/inventory.db"


@contextmanager
def get_connection(db_path: str = DEFAULT_DB_PATH):
    """
    Context manager for SQLite connections.

    Yields a connection with row_factory set to sqlite3.Row
    for dict-like access. Automatically closes on exit.

    Usage:
        with get_connection() as conn:
            row = conn.execute("SELECT ...").fetchone()
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_database(db_path: str = DEFAULT_DB_PATH) -> None:
    """
    Initialize the inventory database with schema and seed data.

    Creates inventory.db if missing, creates tables (inventory, vendors)
    if they don't exist, and seeds initial data only if tables are empty.

    This function is idempotent - safe to call multiple times.

    Args:
        db_path: Path to SQLite database file
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
                "INSERT INTO vendors VALUES (?, ?, ?, ?)",
                VENDORS_SEED_DATA,
            )

        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------


def get_item_info(
    item: str, db_path: str = DEFAULT_DB_PATH
) -> Optional[Dict[str, object]]:
    """
    Query inventory for an item by name.

    Returns dict with keys: item, stock, unit_price, category,
    min_order_qty, max_order_qty, active.
    Returns None if not found.
    """
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT item, stock, unit_price, category, "
            "min_order_qty, max_order_qty, active "
            "FROM inventory WHERE item = ?",
            (item,),
        ).fetchone()

    if row is None:
        return None

    return dict(row)


def get_vendor_info(
    vendor_name: str, db_path: str = DEFAULT_DB_PATH
) -> Optional[Dict[str, object]]:
    """
    Query vendors table for vendor information.

    Returns dict with keys: vendor_name, address, payment_terms,
    trusted. Returns None if vendor not found.
    """
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT vendor_name, address, payment_terms, trusted "
            "FROM vendors WHERE vendor_name = ?",
            (vendor_name,),
        ).fetchone()

    if row is None:
        return None

    return dict(row)


def check_stock_availability(
    item: str,
    quantity: int,
    db_path: str = DEFAULT_DB_PATH,
) -> Tuple[bool, str]:
    """
    Check if requested quantity is available in stock.

    Returns (is_available, message).

    Examples:
    - Item not in DB: (False, "Item not found in inventory")
    - Negative qty: (False, "Invalid quantity: -5")
    - Qty > stock: (False, "Requested 20, only 5 in stock")
    - Stock == 0: (False, "Item out of stock")
    - Valid: (True, "OK")
    """
    if quantity < 0:
        return (False, f"Invalid quantity: {quantity}")

    item_info = get_item_info(item, db_path)

    if item_info is None:
        return (False, "Item not found in inventory")

    stock = item_info["stock"]

    if stock == 0:
        return (False, "Item out of stock")

    if quantity > stock:
        return (
            False,
            f"Requested {quantity}, only {stock} in stock",
        )

    return (True, "OK")


# ---------------------------------------------------------------------------
# Debug / listing helpers
# ---------------------------------------------------------------------------


def list_inventory(
    db_path: str = DEFAULT_DB_PATH,
) -> List[Dict[str, object]]:
    """
    Return all inventory rows as a list of dicts.

    Useful for debugging and test assertions.
    """
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT item, stock, unit_price, category, "
            "min_order_qty, max_order_qty, active "
            "FROM inventory ORDER BY item"
        ).fetchall()

    return [dict(r) for r in rows]


def list_vendors(
    db_path: str = DEFAULT_DB_PATH,
) -> List[Dict[str, object]]:
    """
    Return all vendor rows as a list of dicts.

    Useful for debugging and test assertions.
    """
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT vendor_name, address, payment_terms, trusted "
            "FROM vendors ORDER BY vendor_name"
        ).fetchall()

    return [dict(r) for r in rows]
