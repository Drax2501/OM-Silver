
import sqlite3
from pathlib import Path


# Always use the database stored beside this file.
DB_PATH = Path(__file__).resolve().parent / "Data.db"


def get_connection():
    """Create a connection to the application's database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create missing tables and safely update existing tables."""

    conn = get_connection()

    try:
        cursor = conn.cursor()

        # ==================================================
        # CUSTOMERS
        # ==================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS "Customers" (
                "Customer ID" INTEGER PRIMARY KEY AUTOINCREMENT,
                "Name" TEXT,
                "Shop Name" TEXT,
                "Contact Number" TEXT,
                "GST IN" TEXT,
                "Address" TEXT
            )
        """)

        # ==================================================
        # VENDORS
        # ==================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS "Vendors" (
                "ID" INTEGER PRIMARY KEY AUTOINCREMENT,
                "Name" TEXT,
                "Firm Name" TEXT,
                "Contact Number" TEXT,
                "GST IN" TEXT,
                "Address" TEXT
            )
        """)

        # ==================================================
        # OTHER ACCOUNTS
        # ==================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS "Other_Accounts" (
                "ID" INTEGER PRIMARY KEY AUTOINCREMENT,
                "Name" TEXT,
                "Account Type" TEXT
            )
        """)

        # ==================================================
        # TRANSACTIONS
        # One record per complete transaction.
        # ==================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS "Transactions" (
                "ID" INTEGER PRIMARY KEY AUTOINCREMENT,
                "Date" TEXT,
                "Transaction Type" TEXT,
                "Customer ID" INTEGER,
                "Vendor ID" INTEGER,
                "Settlement" TEXT,
                "Total Weight" NUMERIC,
                "Total Amount" NUMERIC,
                "Total Weight Exchange" NUMERIC,
                "Direction" TEXT,
                "Exchange Fee" NUMERIC
            )
        """)

        # ==================================================
        # TRANSACTION ITEMS
        # Multiple item rows can belong to one transaction.
        # ==================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS "Transaction_items" (
                "ID" INTEGER PRIMARY KEY AUTOINCREMENT,
                "Transaction_ID" INTEGER,
                "Item_name" TEXT,
                "Rate" NUMERIC,
                "Gross_weight" NUMERIC,
                "Tounch" NUMERIC,
                "Making" NUMERIC,
                "Net_weight" NUMERIC,
                "Calculated_amount" NUMERIC,
                "Amount" NUMERIC,
                "Discount" NUMERIC,
                "Type" TEXT,
                "Section" TEXT,
                FOREIGN KEY ("Transaction_ID")
                    REFERENCES "Transactions"("ID")
            )
        """)

        # ==================================================
        # ITEMS
        # Master list of item names.
        # ==================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS "Items" (
                "ID" INTEGER PRIMARY KEY AUTOINCREMENT,
                "Name" TEXT NOT NULL COLLATE NOCASE UNIQUE
            )
        """)

        # ==================================================
        # INVENTORY
        # Records opening balances and stock movements.
        # ==================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS "Inventory" (
                "ID" INTEGER PRIMARY KEY AUTOINCREMENT,
                "Item ID" INTEGER NOT NULL,
                "Transaction ID" INTEGER,
                "Item Movement" TEXT NOT NULL,
                "Weight" NUMERIC NOT NULL DEFAULT 0,

                FOREIGN KEY ("Item ID")
                    REFERENCES "Items"("ID"),

                FOREIGN KEY ("Transaction ID")
                    REFERENCES "Transactions"("ID")
            )
        """)

        
        # ==================================================
        # LEDGER
        # One entry belongs to exactly one account type.
        # ==================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS "Ledger" (
                "ID" INTEGER PRIMARY KEY AUTOINCREMENT,

                "Customer ID" INTEGER,
                "Vendor ID" INTEGER,
                "Other Account ID" INTEGER,

                "Transaction ID" INTEGER,

                "Display A/c Debit" TEXT,
                "Display A/c Credit" TEXT,
                "Amount Debit" NUMERIC NOT NULL DEFAULT 0,
                "Amount Credit" NUMERIC NOT NULL DEFAULT 0,

                "Silver Display Debit" TEXT,
                "Silver Display Credit" TEXT,
                "Silver Debit" NUMERIC NOT NULL DEFAULT 0,
                "Silver Credit" NUMERIC NOT NULL DEFAULT 0,

                "Gold Display Debit" TEXT,
                "Gold Display Credit" TEXT,
                "Gold Debit" NUMERIC NOT NULL DEFAULT 0,
                "Gold Credit" NUMERIC NOT NULL DEFAULT 0,

                CHECK (
                    ("Customer ID" IS NOT NULL) +
                    ("Vendor ID" IS NOT NULL) +
                    ("Other Account ID" IS NOT NULL) = 1
                ),

                FOREIGN KEY ("Customer ID")
                    REFERENCES "Customers"("Customer ID"),

                FOREIGN KEY ("Vendor ID")
                    REFERENCES "Vendors"("ID"),

                FOREIGN KEY ("Other Account ID")
                    REFERENCES "Other_Accounts"("ID"),

                FOREIGN KEY ("Transaction ID")
                    REFERENCES "Transactions"("ID")
            )
        """)

        # Speed up account-ledger lookups.
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS "idx_ledger_customer"
            ON "Ledger"("Customer ID")
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS "idx_ledger_vendor"
            ON "Ledger"("Vendor ID")
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS "idx_ledger_other_account"
            ON "Ledger"("Other Account ID")
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS "idx_ledger_transaction"
            ON "Ledger"("Transaction ID")
        """)


        # ==================================================
        # SAFE DATABASE UPDATE
        # Add Item_ID to existing transaction-item tables.
        # Existing rows and columns are preserved.
        # ==================================================

        cursor.execute('PRAGMA table_info("Transaction_items")')
        existing_columns = {
            row[1] for row in cursor.fetchall()
        }

        if "Item_ID" not in existing_columns:
            cursor.execute("""
                ALTER TABLE "Transaction_items"
                ADD COLUMN "Item_ID" INTEGER
                REFERENCES "Items"("ID")
            """)

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
    print(f"Database location: {DB_PATH}")
