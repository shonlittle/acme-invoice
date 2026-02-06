#!/usr/bin/env python3
"""
Smoke test for database initialization and query helpers.

Tests that init_database() creates tables and seeds data correctly,
and that query helpers return expected results.

Usage:
    python3 tests/test_db_init.py
"""

import os
import sqlite3
import sys
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402

from db.inventory import (  # noqa: E402
    get_item_info,
    get_vendor_info,
    init_database,
    list_inventory,
    list_vendors,
)

# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture(scope="module")
def test_db():
    """Create a temporary DB for all tests in this module."""
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    db_path = db_file.name
    db_file.close()

    init_database(db_path)
    yield db_path

    os.remove(db_path)


# ------------------------------------------------------------------
# Schema / seed tests
# ------------------------------------------------------------------


def test_tables_created(test_db):
    """init_database creates inventory and vendors tables."""
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM sqlite_master " "WHERE type='table' AND name='inventory'"
    )
    assert cursor.fetchone() is not None

    cursor.execute(
        "SELECT name FROM sqlite_master " "WHERE type='table' AND name='vendors'"
    )
    assert cursor.fetchone() is not None

    conn.close()


def test_inventory_seeded(test_db):
    """Inventory table has at least 4 seed rows."""
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM inventory")
    count = cursor.fetchone()[0]
    conn.close()

    assert count >= 4


def test_vendors_seeded(test_db):
    """Vendors table has at least 4 seed rows."""
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM vendors")
    count = cursor.fetchone()[0]
    conn.close()

    assert count >= 4


def test_idempotency(test_db):
    """Calling init_database twice does not duplicate rows."""
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM inventory")
    before = cursor.fetchone()[0]
    conn.close()

    init_database(test_db)

    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM inventory")
    after = cursor.fetchone()[0]
    conn.close()

    assert before == after


# ------------------------------------------------------------------
# get_item_info tests
# ------------------------------------------------------------------


def test_get_item_info_found(test_db):
    """get_item_info returns dict for known item."""
    info = get_item_info("WidgetA", test_db)
    assert info is not None
    assert info["item"] == "WidgetA"
    assert info["stock"] == 15
    assert info["unit_price"] == 250.0


def test_get_item_info_not_found(test_db):
    """get_item_info returns None for unknown item."""
    info = get_item_info("NonExistent", test_db)
    assert info is None


# ------------------------------------------------------------------
# get_vendor_info tests
# ------------------------------------------------------------------


def test_get_vendor_info_found(test_db):
    """get_vendor_info returns dict for known vendor."""
    info = get_vendor_info("Widgets Inc.", test_db)
    assert info is not None
    assert info["vendor_name"] == "Widgets Inc."
    assert info["trusted"] == 1
    assert info["payment_terms"] == "Net 15"


def test_get_vendor_info_not_found(test_db):
    """get_vendor_info returns None for unknown vendor."""
    info = get_vendor_info("Ghost Corp", test_db)
    assert info is None


def test_get_vendor_info_untrusted(test_db):
    """get_vendor_info returns trusted=0 for flagged vendor."""
    info = get_vendor_info("NoProd Industries", test_db)
    assert info is not None
    assert info["trusted"] == 0


# ------------------------------------------------------------------
# list_inventory / list_vendors tests
# ------------------------------------------------------------------


def test_list_inventory(test_db):
    """list_inventory returns all rows as list of dicts."""
    items = list_inventory(test_db)
    assert len(items) >= 4
    names = [i["item"] for i in items]
    assert "WidgetA" in names
    assert "WidgetB" in names
    assert "GadgetX" in names


def test_list_vendors(test_db):
    """list_vendors returns all rows as list of dicts."""
    vendors = list_vendors(test_db)
    assert len(vendors) >= 4
    names = [v["vendor_name"] for v in vendors]
    assert "Widgets Inc." in names
    assert "Precision Parts Ltd." in names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
