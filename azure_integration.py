# ============================================================
# azure_integration.py (USER-BASED VERSION)
# Azure Table Storage integration for Spendwise
# ============================================================

import os
import uuid
from azure.data.tables import TableServiceClient

# ------------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------------
CONNECTION_STRING = os.environ.get("AZURE_STORAGE_CONNECTION_STRING", "")
TABLE_NAME = "expenses"


# ------------------------------------------------------------------
# CONNECTION
# ------------------------------------------------------------------
def get_table_client():
    service = TableServiceClient.from_connection_string(CONNECTION_STRING)
    service.create_table_if_not_exists(TABLE_NAME)
    return service.get_table_client(TABLE_NAME)


# ------------------------------------------------------------------
# ADD EXPENSE
# ------------------------------------------------------------------
def add_expense_azure(user_id: int, amount: float, category: str, note: str, date: str):
    client = get_table_client()

    entity = {
        # 🔥 Partition by USER (IMPORTANT)
        "PartitionKey": str(user_id),

        # Unique ID
        "RowKey": str(uuid.uuid4()),

        "Amount": float(amount),
        "Category": category,
        "Note": note,
        "Date": date,
    }

    client.create_entity(entity)


# ------------------------------------------------------------------
# GET EXPENSES (USER-SPECIFIC)
# ------------------------------------------------------------------
def get_expenses_azure(user_id: int, category_filter: str = ""):
    client = get_table_client()

    # Filter by user
    query = f"PartitionKey eq '{user_id}'"

    # Optional category filter
    if category_filter:
        query += f" and Category eq '{category_filter}'"

    rows = list(client.query_entities(query))

    # Sort newest first
    rows.sort(key=lambda r: r.get("Date", ""), reverse=True)

    # Convert to Flask-friendly format
    expenses = []
    for r in rows:
        expenses.append({
            "id": r["RowKey"],
            "user_id": int(r["PartitionKey"]),
            "amount": r.get("Amount", 0),
            "category": r.get("Category", ""),
            "note": r.get("Note", ""),
            "date": r.get("Date", "")
        })

    return expenses


# ------------------------------------------------------------------
# DELETE EXPENSE
# ------------------------------------------------------------------
def delete_expense_azure(user_id: int, row_key: str):
    client = get_table_client()

    client.delete_entity(
        partition_key=str(user_id),
        row_key=row_key
    )


# ------------------------------------------------------------------
# OPTIONAL: GET SUMMARY (for dashboard)
# ------------------------------------------------------------------
def get_summary_azure(user_id: int):
    expenses = get_expenses_azure(user_id)

    total = sum(e["amount"] for e in expenses)

    by_category = {}
    for e in expenses:
        by_category[e["category"]] = by_category.get(e["category"], 0) + e["amount"]

    return {
        "total_spent": total,
        "by_category": by_category
    }


# ------------------------------------------------------------------
# HOW TO USE IN app.py
# ------------------------------------------------------------------
"""
Replace SQLite calls with:

from azure_integration import (
    add_expense_azure,
    get_expenses_azure,
    delete_expense_azure
)

Example:

# ADD
add_expense_azure(user_id, amount, category, note, date)

# GET
expenses = get_expenses_azure(user_id)

# DELETE
delete_expense_azure(user_id, expense_id)

IMPORTANT:
- expense_id = RowKey (string, not int)
"""