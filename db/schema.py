"""
Database schema definitions for inventory and vendor tracking.

Enhanced schema supports:
- Price validation (unit_price in inventory)
- Stock constraints (min/max order quantities)
- Vendor trust flags (whitelist/blacklist)
- Item categorization and active status
"""

# Enhanced inventory table with pricing and constraints
INVENTORY_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS inventory (
    item TEXT PRIMARY KEY,
    stock INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    category TEXT,
    min_order_qty INTEGER DEFAULT 1,
    max_order_qty INTEGER DEFAULT 1000,
    active INTEGER DEFAULT 1
)
"""

# Vendor whitelist/blacklist table
VENDORS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS vendors (
    vendor_name TEXT PRIMARY KEY,
    address TEXT,
    payment_terms TEXT DEFAULT 'Net 30',
    trusted INTEGER DEFAULT 1
)
"""

# Seed data for inventory (matches sample invoices)
INVENTORY_SEED_DATA = [
    ("WidgetA", 15, 250.00, "Widgets", 1, 100, 1),
    ("WidgetB", 10, 500.00, "Widgets", 1, 50, 1),
    ("GadgetX", 5, 400.00, "Gadgets", 1, 20, 1),
    ("FakeItem", 0, 0.00, "Unknown", 1, 0, 0),  # Discontinued/suspicious
]

# Seed data for vendors (matches sample invoices)
VENDORS_SEED_DATA = [
    ("Widgets Inc.", "100 Main St, Chicago, IL 60601", "Net 15", 1),
    (
        "Precision Parts Ltd.",
        "742 Evergreen Terrace, Springfield, IL 62704",
        "Net 30",
        1,
    ),
    ("Acme Industrial Supplies", None, "Net 15", 1),
    ("NoProd Industries", None, "Net 30", 0),  # Flagged as suspicious
]
