
import sqlite3

from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtWidgets import (
    QWidget,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QAbstractItemView,
    QFrame,
)

from database import get_connection
from ui import BasePage


def money(value):
    return f"₹{float(value or 0):,.2f}"


def number(value):
    """Safely convert a database value to a number."""
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


class SelectOnFocusSpinBox(QDoubleSpinBox):
    """Select the existing number so typing replaces it."""

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.lineEdit().selectAll()


def spinbox(maximum=1_000_000_000, decimals=3, suffix=""):
    widget = SelectOnFocusSpinBox()
    widget.setRange(0, maximum)
    widget.setDecimals(decimals)
    widget.setKeyboardTracking(False)

    if suffix:
        widget.setSuffix(suffix)

    return widget


def get_table_columns(cursor, table):
    cursor.execute(f'PRAGMA table_info("{table}")')
    return {row[1] for row in cursor.fetchall()}


# ============================================================
# LEDGER POSTING
# ============================================================


def insert_sale_ledger_entries(
    cursor,
    transaction_id,
    customer_id,
    vendor_id,
    settlement,
    full_amount,
    fine_total,
    amount_to_store,
):
    """
    Store each sale as one Ledger row.

    Cash/Credit: amount only.
    Silver: fine silver and making charges in the same row.
    Gold: fine gold and making charges in the same row.

    Zero-value components are stored as NULL, so they can
    remain blank in the ledger display.
    """

    required_columns = {
        "Customer ID",
        "Vendor ID",
        "Other Account ID",
        "Transaction ID",
        "Display A/c Debit",
        "Amount Debit",
        "Silver Display Debit",
        "Silver Debit",
        "Gold Display Debit",
        "Gold Debit",
    }

    existing_columns = get_table_columns(cursor, "Ledger")

    if not existing_columns:
        raise RuntimeError("The Ledger table does not exist.")

    missing_columns = required_columns - existing_columns
    if missing_columns:
        raise RuntimeError(
            "The Ledger table is missing columns: "
            + ", ".join(sorted(missing_columns))
        )

    account_values = (
        customer_id,
        vendor_id,
        None,
        transaction_id,
    )

    # Cash and Credit: one amount entry, only if non-zero.
    if settlement in ("Cash", "Credit"):
        if full_amount <= 0:
            return

        description = (
            "Cash Sale" if settlement == "Cash"
            else "Credit Sale"
        )

        cursor.execute("""
            INSERT INTO Ledger (
                "Customer ID",
                "Vendor ID",
                "Other Account ID",
                "Transaction ID",
                "Display A/c Debit",
                "Amount Debit"
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (*account_values, description, full_amount))

        return

    # Silver: fine silver and making charges in ONE row.
    if settlement == "Silver":
        if fine_total <= 0 and amount_to_store <= 0:
            return

        cursor.execute("""
            INSERT INTO Ledger (
                "Customer ID",
                "Vendor ID",
                "Other Account ID",
                "Transaction ID",
                "Silver Display Debit",
                "Silver Debit",
                "Display A/c Debit",
                "Amount Debit"
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            *account_values,
            "Silver Sale" if fine_total > 0 else None,
            fine_total if fine_total > 0 else None,
            "Making Charges" if amount_to_store > 0 else None,
            amount_to_store if amount_to_store > 0 else None,
        ))

    # Gold: fine gold and making charges in ONE row.
    elif settlement == "Gold":
        if fine_total <= 0 and amount_to_store <= 0:
            return

        cursor.execute("""
            INSERT INTO Ledger (
                "Customer ID",
                "Vendor ID",
                "Other Account ID",
                "Transaction ID",
                "Gold Display Debit",
                "Gold Debit",
                "Display A/c Debit",
                "Amount Debit"
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            *account_values,
            "Gold Sale" if fine_total > 0 else None,
            fine_total if fine_total > 0 else None,
            "Making Charges" if amount_to_store > 0 else None,
            amount_to_store if amount_to_store > 0 else None,
        ))



def insert_purchase_ledger_entries(
    cursor,
    transaction_id,
    customer_id,
    vendor_id,
    settlement,
    full_amount,
    fine_total,
    amount_to_store,
):
    """Store a purchase in the Ledger credit columns."""
    required_columns = {
        "Customer ID", "Vendor ID", "Other Account ID", "Transaction ID",
        "Display A/c Credit", "Amount Credit",
        "Silver Display Credit", "Silver Credit",
        "Gold Display Credit", "Gold Credit",
    }
    existing_columns = get_table_columns(cursor, "Ledger")
    if not existing_columns:
        raise RuntimeError("The Ledger table does not exist.")
    missing_columns = required_columns - existing_columns
    if missing_columns:
        raise RuntimeError(
            "The Ledger table is missing columns: "
            + ", ".join(sorted(missing_columns))
        )

    account_values = (customer_id, vendor_id, None, transaction_id)

    if settlement in ("Cash", "Credit"):
        if full_amount <= 0:
            return
        description = "Cash Purchase" if settlement == "Cash" else "Credit Purchase"
        cursor.execute("""
            INSERT INTO Ledger (
                "Customer ID", "Vendor ID", "Other Account ID", "Transaction ID",
                "Display A/c Credit", "Amount Credit"
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (*account_values, description, full_amount))
        return

    if settlement == "Silver":
        if fine_total <= 0 and amount_to_store <= 0:
            return
        cursor.execute("""
            INSERT INTO Ledger (
                "Customer ID", "Vendor ID", "Other Account ID", "Transaction ID",
                "Silver Display Credit", "Silver Credit",
                "Display A/c Credit", "Amount Credit"
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            *account_values,
            "Silver Purchase" if fine_total > 0 else None,
            fine_total if fine_total > 0 else None,
            "Making Charges" if amount_to_store > 0 else None,
            amount_to_store if amount_to_store > 0 else None,
        ))
    elif settlement == "Gold":
        if fine_total <= 0 and amount_to_store <= 0:
            return
        cursor.execute("""
            INSERT INTO Ledger (
                "Customer ID", "Vendor ID", "Other Account ID", "Transaction ID",
                "Gold Display Credit", "Gold Credit",
                "Display A/c Credit", "Amount Credit"
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            *account_values,
            "Gold Purchase" if fine_total > 0 else None,
            fine_total if fine_total > 0 else None,
            "Making Charges" if amount_to_store > 0 else None,
            amount_to_store if amount_to_store > 0 else None,
        ))


# ============================================================
# TRANSACTIONS PAGE
# ============================================================

class TransactionsPage(BasePage):

    def __init__(self):
        super().__init__(
            title="Transactions",
            description="Create, view and manage business transactions.",
        )

        self.build_page()
        self.refresh_transactions()

    def build_page(self):
        container = QWidget()

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        buttons = QHBoxLayout()

        self.sale_button = QPushButton("New Sale")
        self.purchase_button = QPushButton("New Purchase")
        self.exchange_button = QPushButton("New Exchange")
        self.payment_button = QPushButton("New Payment")

        self.sale_button.clicked.connect(self.open_new_sale)

        self.purchase_button.clicked.connect(self.open_new_purchase)

        self.exchange_button.clicked.connect(
            lambda: self.not_implemented("Exchange")
        )

        self.payment_button.clicked.connect(
            lambda: self.not_implemented("Payment")
        )

        for button in (
            self.sale_button,
            self.purchase_button,
            self.exchange_button,
            self.payment_button,
        ):
            buttons.addWidget(button)

        buttons.addStretch()
        layout.addLayout(buttons)

        self.transactions_table = QTableWidget(0, 7)

        self.transactions_table.setHorizontalHeaderLabels([
            "ID",
            "Date",
            "Type",
            "Party",
            "Settlement",
            "Total Amount",
            "Action",
        ])

        # 1. Get the horizontal header object
        header = self.transactions_table.horizontalHeader()

        # 2. Set the default alignment to left (and vertically centered)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.transactions_table.setStyleSheet("""
            QHeaderView::section {
            }
        """)
        

        self.transactions_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.transactions_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.transactions_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.transactions_table.verticalHeader().setVisible(False)

        self.transactions_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        self.transactions_table.setAlternatingRowColors(True)

        layout.addWidget(self.transactions_table, 1)

        refresh_row = QHBoxLayout()
        refresh_row.addStretch()

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_transactions)

        refresh_row.addWidget(self.refresh_button)
        layout.addLayout(refresh_row)

        self.add_content(container)

    def not_implemented(self, transaction_type):
        QMessageBox.information(
            self,
            transaction_type,
            f"{transaction_type} transactions will be implemented next.",
        )

    def refresh_transactions(self):
        self.transactions_table.setRowCount(0)

        try:
            with get_connection() as conn:
                conn.row_factory = sqlite3.Row

                rows = conn.execute("""
                    SELECT
                        t.ID,
                        t.Date,
                        t."Transaction Type" AS transaction_type,
                        t.Settlement,
                        t."Total Amount" AS total_amount,
                        t."Customer ID" AS customer_id,
                        t."Vendor ID" AS vendor_id,
                        c.Name AS customer_name,
                        c."Shop Name" AS shop_name,
                        v.Name AS vendor_name,
                        v."Firm Name" AS firm_name
                    FROM Transactions t
                    LEFT JOIN Customers c
                        ON c."Customer ID" = t."Customer ID"
                    LEFT JOIN Vendors v
                        ON v.ID = t."Vendor ID"
                    ORDER BY t.ID DESC
                """).fetchall()

            self.transactions_table.setRowCount(len(rows))

            for index, row in enumerate(rows):
                if row["customer_id"] is not None:
                    party = (
                        row["shop_name"]
                        or row["customer_name"]
                        or "Customer"
                    )

                elif row["vendor_id"] is not None:
                    party = (
                        row["firm_name"]
                        or row["vendor_name"]
                        or "Vendor"
                    )

                else:
                    party = "—"

                values = [
                    str(row["ID"]),
                    str(row["Date"] or ""),
                    str(row["transaction_type"] or ""),
                    str(party),
                    str(row["Settlement"] or ""),
                    money(row["total_amount"]),
                ]

                for column, value in enumerate(values):
                    self.transactions_table.setItem(
                        index,
                        column,
                        QTableWidgetItem(value),
                    )

                view_button = QPushButton("View")
                view_button.setFixedSize(55, 26)

                view_button.setStyleSheet("""
                    QPushButton {
                        padding: 0 8px;
                        margin: 0px;
                    }
                """)

                view_button.clicked.connect(
                    lambda checked=False, transaction_id=row["ID"]:
                        self.view_transaction(transaction_id)
                )

                self.transactions_table.setCellWidget(
                    index,
                    6,
                    view_button,
                )

        except sqlite3.Error as exc:
            QMessageBox.critical(
                self,
                "Database Error",
                f"Could not load transactions:\n{exc}",
            )

    def open_new_sale(self):
        dialog = SaleDialog(self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_transactions()

    def open_new_purchase(self):
        dialog = PurchaseDialog(self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_transactions()

    def view_transaction(self, transaction_id):
        dialog = TransactionDetailsDialog(transaction_id, self)

        dialog.transaction_changed.connect(
            self.refresh_transactions
        )

        dialog.exec()


# ============================================================
# TRANSACTION DETAILS WINDOW
# ============================================================

class TransactionDetailsDialog(QDialog):

    transaction_changed = Signal()

    def __init__(self, transaction_id, parent=None):
        super().__init__(parent)

        self.transaction_id = transaction_id

        self.setWindowTitle(
            f"Transaction #{transaction_id}"
        )

        self.resize(1050, 650)

        self.layout_main = QVBoxLayout(self)

        self.load_details()

    def load_details(self):
        while self.layout_main.count():
            item = self.layout_main.takeAt(0)
            widget = item.widget()

            if widget:
                widget.deleteLater()

        try:
            with get_connection() as conn:
                conn.row_factory = sqlite3.Row

                transaction = conn.execute("""
                    SELECT
                        t.*,
                        c.Name AS customer_name,
                        c."Shop Name" AS shop_name,
                        v.Name AS vendor_name,
                        v."Firm Name" AS firm_name
                    FROM Transactions t
                    LEFT JOIN Customers c
                        ON c."Customer ID" = t."Customer ID"
                    LEFT JOIN Vendors v
                        ON v.ID = t."Vendor ID"
                    WHERE t.ID = ?
                """, (
                    self.transaction_id,
                )).fetchone()

                if transaction is None:
                    QMessageBox.warning(
                        self,
                        "Not Found",
                        "This transaction no longer exists.",
                    )
                    self.reject()
                    return

                item_rows = conn.execute("""
                    SELECT *
                    FROM Transaction_items
                    WHERE Transaction_ID = ?
                    ORDER BY ID
                """, (
                    self.transaction_id,
                )).fetchall()

                movement_rows = conn.execute("""
                    SELECT
                        i.Name,
                        inv."Item Movement",
                        inv.Weight
                    FROM Inventory inv
                    JOIN Items i
                        ON i.ID = inv."Item ID"
                    WHERE inv."Transaction ID" = ?
                """, (
                    self.transaction_id,
                )).fetchall()

        except sqlite3.Error as exc:
            QMessageBox.critical(
                self,
                "Database Error",
                f"Could not load transaction details:\n{exc}",
            )
            self.reject()
            return

        if transaction["Customer ID"] is not None:
            party_type = "Customer"
            party_name = (
                transaction["shop_name"]
                or transaction["customer_name"]
                or "Customer"
            )

        elif transaction["Vendor ID"] is not None:
            party_type = "Vendor"
            party_name = (
                transaction["firm_name"]
                or transaction["vendor_name"]
                or "Vendor"
            )

        else:
            party_type = "Unassigned"
            party_name = "—"

        details = QFrame()
        details.setFrameShape(QFrame.Shape.StyledPanel)

        grid = QGridLayout(details)

        fields = [
            ("Transaction ID", transaction["ID"]),
            ("Date", transaction["Date"] or ""),
            ("Type", transaction["Transaction Type"] or ""),
            ("Party Type", party_type),
            ("Party", party_name),
            ("Settlement", transaction["Settlement"] or ""),
            (
                "Total Weight",
                f'{number(transaction["Total Weight"]):,.2f} g',
            ),
            (
                "Total Amount",
                money(transaction["Total Amount"]),
            ),
            (
                "Fine Metal Weight",
                f'{number(transaction["Total Weight Exchange"]):,.2f} g',
            ),
            (
                "Direction",
                transaction["Direction"] or "—",
            ),
        ]

        for index, (label, value) in enumerate(fields):
            grid.addWidget(
                QLabel(f"<b>{label}</b>"),
                index // 2,
                (index % 2) * 2,
            )

            grid.addWidget(
                QLabel(str(value)),
                index // 2,
                (index % 2) * 2 + 1,
            )

        self.layout_main.addWidget(details)

        self.layout_main.addWidget(
            QLabel("<h3>Transaction Items</h3>")
        )

        table = QTableWidget(0, 8)

        table.setHorizontalHeaderLabels([
            "Item",
            "Rate (₹/kg)",
            "Gross (g)",
            "Touch (%)",
            "Fine (g)",
            "Making Rate (₹/kg)",
            "Discount (₹)",
            "Amount (₹)",
        ])

        table.verticalHeader().setVisible(False)

        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        table.setRowCount(len(item_rows))

        for index, row in enumerate(item_rows):
            values = [
                row["Item_name"] or "",
                f'₹{number(row["Rate"]):,.0f}',
                f'{number(row["Gross_weight"]):,.2f}',
                f'{number(row["Tounch"]):,.2f}%',
                f'{number(row["Net_weight"]):,.2f}',
                f'₹{number(row["Making"]):,.0f}',
                money(row["Discount"]),
                money(row["Amount"]),
            ]

            for column, value in enumerate(values):
                table.setItem(
                    index,
                    column,
                    QTableWidgetItem(value),
                )

        self.layout_main.addWidget(table, 1)

        if movement_rows:
            self.layout_main.addWidget(
                QLabel("<b>Inventory Movements</b>")
            )

            for movement in movement_rows:
                self.layout_main.addWidget(
                    QLabel(
                        f'{movement["Name"]}: '
                        f'{movement["Item Movement"]} '
                        f'({number(movement["Weight"]):,.2f} g)'
                    )
                )

        buttons = QHBoxLayout()
        buttons.addStretch()

        transaction_type = transaction["Transaction Type"]

        self.edit_button = QPushButton("Edit")
        self.delete_button = QPushButton("Delete")
        self.close_button = QPushButton("Close")

        self.edit_button.setEnabled(
            transaction_type in ("Sale", "Purchase")
        )

        self.edit_button.clicked.connect(
            self.edit_transaction
        )

        self.delete_button.clicked.connect(
            self.delete_transaction
        )

        self.close_button.clicked.connect(
            self.accept
        )

        buttons.addWidget(self.edit_button)
        buttons.addWidget(self.delete_button)
        buttons.addWidget(self.close_button)

        self.layout_main.addLayout(buttons)

    def edit_transaction(self):
        with get_connection() as conn:
            row = conn.execute(
                'SELECT "Transaction Type" FROM Transactions WHERE ID = ?',
                (self.transaction_id,),
            ).fetchone()
        if row is None:
            return
        dialog_class = PurchaseDialog if row[0] == "Purchase" else SaleDialog
        dialog = dialog_class(
            self,
            transaction_id=self.transaction_id,
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.transaction_changed.emit()
            self.load_details()

    def delete_transaction(self):
        answer = QMessageBox.question(
            self,
            "Delete Transaction",
            f"Delete transaction #{self.transaction_id}?\n\n"
            "Its item lines, ledger entries and linked inventory "
            "movements will also be deleted. This action cannot "
            "be undone.",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            with get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    'SELECT "Transaction Type" '
                    "FROM Transactions WHERE ID = ?",
                    (self.transaction_id,),
                )

                transaction = cursor.fetchone()

                if transaction is None:
                    QMessageBox.warning(
                        self,
                        "Not Found",
                        "This transaction has already been deleted.",
                    )

                    self.accept()
                    self.transaction_changed.emit()
                    return

                # Delete ledger entries before the transaction they reference.
                if get_table_columns(cursor, "Ledger"):
                    cursor.execute(
                        'DELETE FROM Ledger WHERE "Transaction ID" = ?',
                        (self.transaction_id,),
                    )

                cursor.execute(
                    'DELETE FROM Inventory WHERE "Transaction ID" = ?',
                    (self.transaction_id,),
                )

                cursor.execute(
                    "DELETE FROM Transaction_items "
                    "WHERE Transaction_ID = ?",
                    (self.transaction_id,),
                )

                cursor.execute(
                    "DELETE FROM Transactions WHERE ID = ?",
                    (self.transaction_id,),
                )

                conn.commit()

            QMessageBox.information(
                self,
                "Deleted",
                "The transaction was deleted.",
            )

            self.transaction_changed.emit()
            self.accept()

        except sqlite3.Error as exc:
            QMessageBox.critical(
                self,
                "Delete Failed",
                f"Could not delete this transaction:\n{exc}",
            )


# ============================================================
# SALE ENTRY / EDIT DIALOG
# ============================================================

class SaleDialog(QDialog):

    def __init__(self, parent=None, transaction_id=None):
        super().__init__(parent)

        self.transaction_id = transaction_id
        self.read_only = False
        self.item_rows = []
        self.saved = False

        self.setWindowTitle(
            "Edit Sale" if transaction_id else "New Sale"
        )

        self.resize(1250, 760)
        self.setMinimumSize(950, 600)

        self.build_form()

        if transaction_id is not None:
            self.load_transaction(transaction_id)

        else:
            self.add_item_row()

        self.recalculate_totals()

    def build_form(self):
        layout = QVBoxLayout(self)

        layout.addWidget(
            QLabel("<h2>Sale Transaction</h2>")
        )

        layout.addWidget(
            QLabel(
                "Weights are in grams. Rate and making are in rupees per kg."
            )
        )

        details = QFrame()
        details.setFrameShape(QFrame.Shape.StyledPanel)

        form = QFormLayout(details)

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("dd MMM yyyy")
        self.date_input.setDate(QDate.currentDate())

        self.party_type = QComboBox()
        self.party_type.addItems([
            "Customer",
            "Vendor",
        ])

        self.party_type.currentIndexChanged.connect(
            self.refresh_parties
        )

        self.party_input = QComboBox()

        self.settlement_input = QComboBox()
        self.settlement_input.addItems([
            "Cash",
            "Credit",
            "Silver",
            "Gold",
        ])

        self.settlement_input.currentIndexChanged.connect(
            self.recalculate_totals
        )

        self.settlement_input.currentTextChanged.connect(
            self.update_rate_fields
        )

        form.addRow("Date", self.date_input)
        form.addRow("Party Type", self.party_type)
        form.addRow("Party", self.party_input)
        form.addRow("Settlement", self.settlement_input)

        layout.addWidget(details)

        self.refresh_parties()

        heading_row = QHBoxLayout()
        heading_row.addWidget(
            QLabel("<h3>Items</h3>")
        )
        heading_row.addStretch()

        self.add_button = QPushButton("+ Add Item")
        self.add_button.clicked.connect(
            self.add_item_row
        )

        heading_row.addWidget(self.add_button)
        layout.addLayout(heading_row)

        self.items_table = QTableWidget(0, 11)

        self.items_table.setHorizontalHeaderLabels([
            "Item",
            "Rate ₹/kg",
            "Gross g",
            "Touch %",
            "Fine g",
            "Making ₹/kg",
            "Making ₹",
            "Calculated ₹",
            "Actual Sale ₹",
            "Discount ₹",
            "Action",
        ])

        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setWordWrap(False)

        self.items_table.setHorizontalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel
        )

        self.items_table.setVerticalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel
        )

        self.items_table.verticalHeader().setDefaultSectionSize(48)

        header = self.items_table.horizontalHeader()
        header.setMinimumSectionSize(75)
        header.setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )

        for column, width in enumerate((
            145, 95, 90, 85, 80, 110, 100, 120, 120, 105, 95
        )):
            self.items_table.setColumnWidth(
                column,
                width,
            )

        header.setStretchLastSection(True)
        layout.addWidget(self.items_table, 1)

        totals = QFrame()
        totals.setFrameShape(QFrame.Shape.StyledPanel)

        grid = QGridLayout(totals)

        self.gross_label = QLabel("0.00 g")
        self.fine_label = QLabel("0.00 g")
        self.silver_label = QLabel("₹0.00")
        self.making_label = QLabel("₹0.00")
        self.discount_label = QLabel("₹0.00")
        self.amount_label = QLabel("₹0.00")
        self.metal_label = QLabel("0.00 g")

        total_fields = [
            (0, 0, "Gross Weight", self.gross_label),
            (0, 2, "Fine Weight", self.fine_label),
            (1, 0, "Silver Value", self.silver_label),
            (1, 2, "Making Charges", self.making_label),
            (2, 0, "Discount", self.discount_label),
            (2, 2, "Money Due", self.amount_label),
            (3, 0, "Metal Due", self.metal_label),
        ]

        for row, column, label, value in total_fields:
            grid.addWidget(
                QLabel(f"<b>{label}</b>"),
                row,
                column,
            )

            grid.addWidget(
                value,
                row,
                column + 1,
            )

        layout.addWidget(totals)

        note = QLabel(
            "Fine weight = gross × touch ÷ 100. "
            "Silver value = fine weight × rate ÷ 1,000. "
            "Making charge = gross × making rate ÷ 1,000."
        )

        note.setWordWrap(True)
        layout.addWidget(note)

        buttons = QHBoxLayout()
        buttons.addStretch()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(
            self.reject
        )

        self.save_button = QPushButton("Save Sale")
        self.save_button.clicked.connect(
            self.save_sale
        )

        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.save_button)

        layout.addLayout(buttons)

    def refresh_parties(self, *_):
        self.party_input.clear()

        try:
            with get_connection() as conn:
                if self.party_type.currentText() == "Customer":
                    rows = conn.execute("""
                        SELECT
                            "Customer ID",
                            Name,
                            "Shop Name"
                        FROM Customers
                        ORDER BY "Shop Name", Name
                    """).fetchall()

                else:
                    rows = conn.execute("""
                        SELECT
                            ID,
                            Name,
                            "Firm Name"
                        FROM Vendors
                        ORDER BY "Firm Name", Name
                    """).fetchall()

            for party_id, name, firm in rows:
                display = (
                    (firm or "").strip()
                    or (name or "").strip()
                )

                if (
                    name
                    and firm
                    and name.casefold() != firm.casefold()
                ):
                    display = f"{display} — {name}"

                self.party_input.addItem(
                    display or "Unnamed",
                    party_id,
                )

        except sqlite3.Error as exc:
            QMessageBox.critical(
                self,
                "Database Error",
                f"Could not load parties:\n{exc}",
            )

    def add_item_row(self, *_):
        if self.read_only:
            return False

        try:
            with get_connection() as conn:
                items = conn.execute("""
                    SELECT ID, Name
                    FROM Items
                    ORDER BY Name COLLATE NOCASE
                """).fetchall()

        except sqlite3.Error as exc:
            QMessageBox.critical(
                self,
                "Database Error",
                f"Could not load items:\n{exc}",
            )
            return False

        if not items:
            QMessageBox.information(
                self,
                "No Items",
                "Add at least one item in Inventory before creating a sale.",
            )
            return False

        row_index = self.items_table.rowCount()
        self.items_table.insertRow(row_index)

        item = QComboBox()
        item.addItem("Select item...", None)

        for item_id, item_name in items:
            item.addItem(item_name, item_id)

        rate = spinbox(decimals=0)
        gross = spinbox(decimals=2, suffix=" g")
        touch = spinbox(maximum=100, decimals=2, suffix="%")

        fine = QTableWidgetItem("0.00")
        fine.setFlags(
            fine.flags() & ~Qt.ItemFlag.ItemIsEditable
        )

        making_rate = spinbox(decimals=0)

        making_amount = QTableWidgetItem("₹0.00")
        making_amount.setFlags(
            making_amount.flags() & ~Qt.ItemFlag.ItemIsEditable
        )

        calculated_amount = QTableWidgetItem("₹0.00")
        calculated_amount.setFlags(
            calculated_amount.flags() & ~Qt.ItemFlag.ItemIsEditable
        )

        actual_amount = spinbox(decimals=2)
        actual_amount.setProperty("actual_touched", False)

        discount = QTableWidgetItem("₹0.00")
        discount.setFlags(
            discount.flags() & ~Qt.ItemFlag.ItemIsEditable
        )

        remove = QPushButton("Remove")
        remove.setMinimumHeight(32)
        remove.setMinimumWidth(78)

        for widget in (
            item,
            rate,
            gross,
            touch,
            making_rate,
            actual_amount,
        ):
            widget.setMinimumHeight(34)
            widget.setMinimumWidth(75)

        for widget in (
            fine,
            making_amount,
            calculated_amount,
            discount,
        ):
            widget.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

        self.items_table.setCellWidget(row_index, 0, item)
        self.items_table.setCellWidget(row_index, 1, rate)
        self.items_table.setCellWidget(row_index, 2, gross)
        self.items_table.setCellWidget(row_index, 3, touch)
        self.items_table.setItem(row_index, 4, fine)
        self.items_table.setCellWidget(row_index, 5, making_rate)
        self.items_table.setItem(row_index, 6, making_amount)
        self.items_table.setItem(row_index, 7, calculated_amount)
        self.items_table.setCellWidget(row_index, 8, actual_amount)
        self.items_table.setItem(row_index, 9, discount)
        self.items_table.setCellWidget(row_index, 10, remove)

        record = {
            "item": item,
            "rate": rate,
            "gross": gross,
            "touch": touch,
            "fine": fine,
            "making_rate": making_rate,
            "making_amount": making_amount,
            "calculated_amount": calculated_amount,
            "actual_amount": actual_amount,
            "actual_touched": False,
            "discount": discount,
            "remove": remove,
        }

        self.item_rows.append(record)

        for widget in (
            rate,
            gross,
            touch,
            making_rate,
            actual_amount,
        ):
            widget.setValue(0)

        self.update_rate_fields()

        for widget in (
            rate,
            gross,
            touch,
            making_rate,
        ):
            widget.valueChanged.connect(
                self.recalculate_totals
            )

        actual_amount.valueChanged.connect(
            lambda _value, record=record:
                self.mark_actual_amount_edited(record)
        )

        item.currentIndexChanged.connect(
            self.recalculate_totals
        )

        remove.clicked.connect(
            lambda checked=False, target=row_index:
                self.remove_item_row(target)
        )

        self.recalculate_totals()
        return True

    def update_rate_fields(self, *_):
        """Gold and Silver settlements do not use a rate in this sale form."""
        settlement = self.settlement_input.currentText()
        lock_rate = settlement in ("Gold", "Silver")

        for row in self.item_rows:
            rate = row["rate"]

            if lock_rate and rate.value() != 0:
                rate.setValue(0)

            rate.setEnabled(
                not lock_rate and not self.read_only
            )

    def remove_item_row(self, target):
        if len(self.item_rows) <= 1:
            QMessageBox.information(
                self,
                "Sale Items",
                "A sale must contain at least one item.",
            )
            return

        self.items_table.removeRow(target)
        self.rebuild_rows()
        self.recalculate_totals()

    def rebuild_rows(self):
        self.item_rows = []

        for row_index in range(self.items_table.rowCount()):
            record = {
                "item": self.items_table.cellWidget(row_index, 0),
                "rate": self.items_table.cellWidget(row_index, 1),
                "gross": self.items_table.cellWidget(row_index, 2),
                "touch": self.items_table.cellWidget(row_index, 3),
                "fine": self.items_table.item(row_index, 4),
                "making_rate": self.items_table.cellWidget(row_index, 5),
                "making_amount": self.items_table.item(row_index, 6),
                "calculated_amount": self.items_table.item(row_index, 7),
                "actual_amount": self.items_table.cellWidget(row_index, 8),
                "actual_touched": bool(
                    self.items_table.cellWidget(
                        row_index, 8
                    ).property("actual_touched")
                ),
                "discount": self.items_table.item(row_index, 9),
                "remove": self.items_table.cellWidget(row_index, 10),
            }

            self.item_rows.append(record)

            button = record["remove"]

            try:
                button.clicked.disconnect()
            except RuntimeError:
                pass

            button.clicked.connect(
                lambda checked=False, target=row_index:
                    self.remove_item_row(target)
            )

    def mark_actual_amount_edited(self, record):
        record["actual_touched"] = True

        record["actual_amount"].setProperty(
            "actual_touched",
            True,
        )

        self.recalculate_totals()

    def calculate_line(self, row):
        gross = row["gross"].value()
        touch = row["touch"].value()
        rate = row["rate"].value()
        making_rate = row["making_rate"].value()

        fine = gross * touch / 100
        silver_value = fine * rate / 1000
        making = gross * making_rate / 1000

        calculated_amount = silver_value + making

        actual_widget = row["actual_amount"]

        if not row.get("actual_touched", False):
            actual_widget.blockSignals(True)
            actual_widget.setValue(calculated_amount)
            actual_widget.blockSignals(False)

        actual_amount = actual_widget.value()

        discount = round(
            calculated_amount - actual_amount,
            2,
        )

        return {
            "item_id": row["item"].currentData(),
            "item_name": row["item"].currentText(),
            "gross": gross,
            "touch": touch,
            "fine": fine,
            "rate": rate,
            "making_rate": making_rate,
            "making": making,
            "silver_value": silver_value,
            "discount": discount,
            "calculated_amount": calculated_amount,
            "amount": actual_amount,
        }

    def recalculate_totals(self, *_):
        lines = [
            self.calculate_line(row)
            for row in self.item_rows
        ]

        gross = sum(line["gross"] for line in lines)
        fine = sum(line["fine"] for line in lines)
        silver_value = sum(line["silver_value"] for line in lines)
        making = sum(line["making"] for line in lines)
        discount = sum(line["discount"] for line in lines)
        full_amount = sum(line["amount"] for line in lines)

        for row, line in zip(self.item_rows, lines):
            row["fine"].setText(
                f'{line["fine"]:,.2f}'
            )

            row["making_amount"].setText(
                money(line["making"])
            )

            row["calculated_amount"].setText(
                money(line["calculated_amount"])
            )

            row["discount"].setText(
                money(line["discount"])
            )

        self.gross_label.setText(
            f"{gross:,.2f} g"
        )

        self.fine_label.setText(
            f"{fine:,.2f} g"
        )

        self.silver_label.setText(
            money(silver_value)
        )

        self.making_label.setText(
            money(making)
        )

        self.discount_label.setText(
            money(discount)
        )

        if self.settlement_input.currentText() in ("Silver", "Gold"):
            money_due = max(
                0,
                full_amount - silver_value,
            )

            self.amount_label.setText(
                money(money_due)
            )

            self.metal_label.setText(
                f'{fine:,.2f} g '
                f'{self.settlement_input.currentText().lower()}'
            )

        else:
            self.amount_label.setText(
                money(full_amount)
            )

            self.metal_label.setText("0.00 g")

    def load_transaction(self, transaction_id):
        with get_connection() as conn:
            conn.row_factory = sqlite3.Row

            transaction = conn.execute(
                "SELECT * FROM Transactions WHERE ID = ?",
                (transaction_id,),
            ).fetchone()

            if transaction is None:
                QMessageBox.warning(
                    self,
                    "Not Found",
                    "This sale no longer exists.",
                )
                self.reject()
                return

            saved_items = conn.execute("""
                SELECT *
                FROM Transaction_items
                WHERE Transaction_ID = ?
                ORDER BY ID
            """, (
                transaction_id,
            )).fetchall()

        parsed_date = QDate.fromString(
            str(transaction["Date"] or ""),
            "yyyy-MM-dd",
        )

        if parsed_date.isValid():
            self.date_input.setDate(parsed_date)

        if transaction["Customer ID"] is not None:
            self.party_type.setCurrentText("Customer")
            self.refresh_parties()
            party_id = transaction["Customer ID"]

        else:
            self.party_type.setCurrentText("Vendor")
            self.refresh_parties()
            party_id = transaction["Vendor ID"]

        party_index = self.party_input.findData(party_id)

        if party_index >= 0:
            self.party_input.setCurrentIndex(party_index)

        settlement_index = self.settlement_input.findText(
            transaction["Settlement"] or "Cash"
        )

        if settlement_index >= 0:
            self.settlement_input.setCurrentIndex(
                settlement_index
            )

        self.items_table.setRowCount(0)
        self.item_rows.clear()

        for saved in saved_items:
            if not self.add_item_row():
                break

            row = self.item_rows[-1]

            item_index = row["item"].findData(
                saved["Item_ID"]
            )

            if item_index < 0:
                item_index = row["item"].findText(
                    saved["Item_name"] or ""
                )

            if item_index >= 0:
                row["item"].setCurrentIndex(item_index)

            row["rate"].setValue(
                number(saved["Rate"])
            )

            row["gross"].setValue(
                number(saved["Gross_weight"])
            )

            row["touch"].setValue(
                number(saved["Tounch"])
            )

            row["making_rate"].setValue(
                number(saved["Making"])
            )

            row["actual_amount"].setValue(
                number(saved["Amount"])
            )

            row["actual_touched"] = True

            row["actual_amount"].setProperty(
                "actual_touched",
                True,
            )

        self.update_rate_fields()

        if not saved_items:
            self.add_item_row()

        self.recalculate_totals()

    def set_read_only(self, read_only):
        """Enable or disable editable fields when showing a sale."""
        self.read_only = read_only

        for widget in (
            self.date_input,
            self.party_type,
            self.party_input,
            self.settlement_input,
            self.add_button,
        ):
            widget.setEnabled(not read_only)

        for row in self.item_rows:
            for key in (
                "item",
                "rate",
                "gross",
                "touch",
                "making_rate",
                "actual_amount",
                "remove",
            ):
                row[key].setEnabled(not read_only)

        self.update_rate_fields()

        self.save_button.setVisible(
            not read_only
        )

        self.cancel_button.setText(
            "Close" if read_only else "Cancel"
        )

    def save_sale(self):
        if self.read_only:
            self.accept()
            return

        if self.party_input.currentData() is None:
            QMessageBox.warning(
                self,
                "Select Party",
                "Please select a customer or vendor.",
            )
            return

        lines = []

        try:
            for row in self.item_rows:
                line = self.calculate_line(row)

                if line["item_id"] is None:
                    raise ValueError(
                        "Select an item in every row."
                    )

                if line["gross"] <= 0:
                    raise ValueError(
                        "Gross weight must be greater than zero."
                    )

                if (
                    self.settlement_input.currentText()
                    not in ("Gold", "Silver")
                    and line["rate"] <= 0
                ):
                    raise ValueError(
                        "Rate must be greater than zero."
                    )

                if not 0 < line["touch"] <= 100:
                    raise ValueError(
                        "Touch must be above 0% and at most 100%."
                    )

                if line["amount"] < 0:
                    raise ValueError(
                        "Actual sale amount cannot be negative."
                    )

                lines.append(line)

            if not lines:
                raise ValueError(
                    "Add at least one item."
                )

        except ValueError as exc:
            QMessageBox.warning(
                self,
                "Check Sale",
                str(exc),
            )
            return

        settlement = self.settlement_input.currentText()

        customer_id = (
            self.party_input.currentData()
            if self.party_type.currentText() == "Customer"
            else None
        )

        vendor_id = (
            self.party_input.currentData()
            if self.party_type.currentText() == "Vendor"
            else None
        )

        gross_total = sum(
            line["gross"] for line in lines
        )

        fine_total = sum(
            line["fine"] for line in lines
        )

        making_total = sum(
            line["making"] for line in lines
        )

        discount_total = sum(
            line["discount"] for line in lines
        )

        full_amount = sum(
            line["amount"] for line in lines
        )

        if settlement in ("Silver", "Gold"):
            amount_to_store = max(
                0,
                making_total - discount_total,
            )

            metal_weight = fine_total
            direction = settlement

        else:
            amount_to_store = full_amount
            metal_weight = 0
            direction = None

        try:
            with get_connection() as conn:
                cursor = conn.cursor()

                required = {
                    "Date",
                    "Transaction Type",
                    "Customer ID",
                    "Vendor ID",
                    "Settlement",
                    "Total Weight",
                    "Total Amount",
                    "Total Weight Exchange",
                    "Direction",
                    "Exchange Fee",
                }

                missing = required - get_table_columns(
                    cursor,
                    "Transactions",
                )

                if missing:
                    raise RuntimeError(
                        "Transactions table is missing columns: "
                        + ", ".join(sorted(missing))
                    )

                if self.transaction_id is None:
                    cursor.execute("""
                        INSERT INTO Transactions (
                            Date,
                            "Transaction Type",
                            "Customer ID",
                            "Vendor ID",
                            Settlement,
                            "Total Weight",
                            "Total Amount",
                            "Total Weight Exchange",
                            Direction,
                            "Exchange Fee"
                        )
                        VALUES (
                            ?, 'Sale', ?, ?, ?, ?, ?, ?, ?, ?
                        )
                    """, (
                        self.date_input.date().toString("yyyy-MM-dd"),
                        customer_id,
                        vendor_id,
                        settlement,
                        gross_total,
                        amount_to_store,
                        metal_weight,
                        direction,
                        making_total,
                    ))

                    transaction_id = cursor.lastrowid

                else:
                    transaction_id = self.transaction_id

                    cursor.execute("""
                        SELECT ID
                        FROM Transactions
                        WHERE ID = ?
                          AND "Transaction Type" = 'Sale'
                    """, (
                        transaction_id,
                    ))

                    if cursor.fetchone() is None:
                        raise RuntimeError(
                            "The sale could not be found."
                        )

                    # Editing a sale rebuilds its ledger entries.
                    if get_table_columns(cursor, "Ledger"):
                        cursor.execute(
                            'DELETE FROM Ledger WHERE "Transaction ID" = ?',
                            (transaction_id,),
                        )

                    # Remove this sale's previous outgoing stock movements.
                    cursor.execute("""
                        DELETE FROM Inventory
                        WHERE "Transaction ID" = ?
                          AND "Item Movement" = 'Sale'
                    """, (
                        transaction_id,
                    ))

                    cursor.execute("""
                        UPDATE Transactions
                        SET Date = ?,
                            "Customer ID" = ?,
                            "Vendor ID" = ?,
                            Settlement = ?,
                            "Total Weight" = ?,
                            "Total Amount" = ?,
                            "Total Weight Exchange" = ?,
                            Direction = ?,
                            "Exchange Fee" = ?
                        WHERE ID = ?
                    """, (
                        self.date_input.date().toString("yyyy-MM-dd"),
                        customer_id,
                        vendor_id,
                        settlement,
                        gross_total,
                        amount_to_store,
                        metal_weight,
                        direction,
                        making_total,
                        transaction_id,
                    ))

                    cursor.execute(
                        "DELETE FROM Transaction_items "
                        "WHERE Transaction_ID = ?",
                        (transaction_id,),
                    )

                for line in lines:
                    cursor.execute("""
                        INSERT INTO Transaction_items (
                            Transaction_ID,
                            Item_name,
                            Rate,
                            Gross_weight,
                            Tounch,
                            Making,
                            Net_weight,
                            Calculated_amount,
                            Amount,
                            Discount,
                            Type,
                            Section,
                            Item_ID
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        transaction_id,
                        line["item_name"],
                        line["rate"],
                        line["gross"],
                        line["touch"],
                        line["making_rate"],
                        line["fine"],
                        line["calculated_amount"],
                        line["amount"],
                        line["discount"],
                        "Sale",
                        settlement,
                        line["item_id"],
                    ))

                    # Inventory stores physical gross weight in grams.
                    cursor.execute("""
                        INSERT INTO Inventory (
                            "Item ID",
                            "Transaction ID",
                            "Item Movement",
                            Weight
                        )
                        VALUES (?, ?, 'Sale', ?)
                    """, (
                        line["item_id"],
                        transaction_id,
                        -abs(line["gross"]),
                    ))

                # Ledger entries are saved in the same transaction.
                # Any error rolls back the sale, items, stock and ledger.
                insert_sale_ledger_entries(
                    cursor=cursor,
                    transaction_id=transaction_id,
                    customer_id=customer_id,
                    vendor_id=vendor_id,
                    settlement=settlement,
                    full_amount=full_amount,
                    fine_total=fine_total,
                    amount_to_store=amount_to_store,
                )

                conn.commit()

            self.saved = True

            QMessageBox.information(
                self,
                "Sale Saved",
                f"Sale #{transaction_id} saved successfully.",
            )

            self.accept()

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Could Not Save Sale",
                "The sale was not saved. Database changes were rolled back.\n\n"
                f"Details: {exc}",
            )


# ============================================================
# PURCHASE ENTRY / EDIT DIALOG
# ============================================================

class PurchaseDialog(QDialog):

    def __init__(self, parent=None, transaction_id=None):
        super().__init__(parent)

        self.transaction_id = transaction_id
        self.read_only = False
        self.item_rows = []
        self.saved = False

        self.setWindowTitle(
            "Edit Purchase" if transaction_id else "New Purchase"
        )

        self.resize(1250, 760)
        self.setMinimumSize(950, 600)

        self.build_form()

        if transaction_id is not None:
            self.load_transaction(transaction_id)

        else:
            self.add_item_row()

        self.recalculate_totals()

    def build_form(self):
        layout = QVBoxLayout(self)

        layout.addWidget(
            QLabel("<h2>Purchase Transaction</h2>")
        )

        layout.addWidget(
            QLabel(
                "Weights are in grams. Rate and making are in rupees per kg."
            )
        )

        details = QFrame()
        details.setFrameShape(QFrame.Shape.StyledPanel)

        form = QFormLayout(details)

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("dd MMM yyyy")
        self.date_input.setDate(QDate.currentDate())

        self.party_type = QComboBox()
        self.party_type.addItems([
            "Customer",
            "Vendor",
        ])

        self.party_type.currentIndexChanged.connect(
            self.refresh_parties
        )

        self.party_input = QComboBox()

        self.settlement_input = QComboBox()
        self.settlement_input.addItems([
            "Cash",
            "Credit",
            "Silver",
            "Gold",
        ])

        self.settlement_input.currentIndexChanged.connect(
            self.recalculate_totals
        )

        self.settlement_input.currentTextChanged.connect(
            self.update_rate_fields
        )

        form.addRow("Date", self.date_input)
        form.addRow("Party Type", self.party_type)
        form.addRow("Party", self.party_input)
        form.addRow("Settlement", self.settlement_input)

        layout.addWidget(details)

        self.refresh_parties()

        heading_row = QHBoxLayout()
        heading_row.addWidget(
            QLabel("<h3>Items</h3>")
        )
        heading_row.addStretch()

        self.add_button = QPushButton("+ Add Item")
        self.add_button.clicked.connect(
            self.add_item_row
        )

        heading_row.addWidget(self.add_button)
        layout.addLayout(heading_row)

        self.items_table = QTableWidget(0, 11)

        self.items_table.setHorizontalHeaderLabels([
            "Item",
            "Rate ₹/kg",
            "Gross g",
            "Touch %",
            "Fine g",
            "Making ₹/kg",
            "Making ₹",
            "Calculated ₹",
            "Actual Purchase ₹",
            "Discount ₹",
            "Action",
        ])

        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setWordWrap(False)

        self.items_table.setHorizontalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel
        )

        self.items_table.setVerticalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel
        )

        self.items_table.verticalHeader().setDefaultSectionSize(48)

        header = self.items_table.horizontalHeader()
        header.setMinimumSectionSize(75)
        header.setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )

        for column, width in enumerate((
            145, 95, 90, 85, 80, 110, 100, 120, 120, 105, 95
        )):
            self.items_table.setColumnWidth(
                column,
                width,
            )

        header.setStretchLastSection(True)
        layout.addWidget(self.items_table, 1)

        totals = QFrame()
        totals.setFrameShape(QFrame.Shape.StyledPanel)

        grid = QGridLayout(totals)

        self.gross_label = QLabel("0.00 g")
        self.fine_label = QLabel("0.00 g")
        self.silver_label = QLabel("₹0.00")
        self.making_label = QLabel("₹0.00")
        self.discount_label = QLabel("₹0.00")
        self.amount_label = QLabel("₹0.00")
        self.metal_label = QLabel("0.00 g")

        total_fields = [
            (0, 0, "Gross Weight", self.gross_label),
            (0, 2, "Fine Weight", self.fine_label),
            (1, 0, "Silver Value", self.silver_label),
            (1, 2, "Making Charges", self.making_label),
            (2, 0, "Discount", self.discount_label),
            (2, 2, "Money Due", self.amount_label),
            (3, 0, "Metal Due", self.metal_label),
        ]

        for row, column, label, value in total_fields:
            grid.addWidget(
                QLabel(f"<b>{label}</b>"),
                row,
                column,
            )

            grid.addWidget(
                value,
                row,
                column + 1,
            )

        layout.addWidget(totals)

        note = QLabel(
            "Fine weight = gross × touch ÷ 100. "
            "Silver value = fine weight × rate ÷ 1,000. "
            "Making charge = gross × making rate ÷ 1,000."
        )

        note.setWordWrap(True)
        layout.addWidget(note)

        buttons = QHBoxLayout()
        buttons.addStretch()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(
            self.reject
        )

        self.save_button = QPushButton("Save Purchase")
        self.save_button.clicked.connect(
            self.save_purchase
        )

        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.save_button)

        layout.addLayout(buttons)

    def refresh_parties(self, *_):
        self.party_input.clear()

        try:
            with get_connection() as conn:
                if self.party_type.currentText() == "Customer":
                    rows = conn.execute("""
                        SELECT
                            "Customer ID",
                            Name,
                            "Shop Name"
                        FROM Customers
                        ORDER BY "Shop Name", Name
                    """).fetchall()

                else:
                    rows = conn.execute("""
                        SELECT
                            ID,
                            Name,
                            "Firm Name"
                        FROM Vendors
                        ORDER BY "Firm Name", Name
                    """).fetchall()

            for party_id, name, firm in rows:
                display = (
                    (firm or "").strip()
                    or (name or "").strip()
                )

                if (
                    name
                    and firm
                    and name.casefold() != firm.casefold()
                ):
                    display = f"{display} — {name}"

                self.party_input.addItem(
                    display or "Unnamed",
                    party_id,
                )

        except sqlite3.Error as exc:
            QMessageBox.critical(
                self,
                "Database Error",
                f"Could not load parties:\n{exc}",
            )

    def add_item_row(self, *_):
        if self.read_only:
            return False

        try:
            with get_connection() as conn:
                items = conn.execute("""
                    SELECT ID, Name
                    FROM Items
                    ORDER BY Name COLLATE NOCASE
                """).fetchall()

        except sqlite3.Error as exc:
            QMessageBox.critical(
                self,
                "Database Error",
                f"Could not load items:\n{exc}",
            )
            return False

        if not items:
            QMessageBox.information(
                self,
                "No Items",
                "Add at least one item in Inventory before creating a purchase.",
            )
            return False

        row_index = self.items_table.rowCount()
        self.items_table.insertRow(row_index)

        item = QComboBox()
        item.addItem("Select item...", None)

        for item_id, item_name in items:
            item.addItem(item_name, item_id)

        rate = spinbox(decimals=0)
        gross = spinbox(decimals=2, suffix=" g")
        touch = spinbox(maximum=100, decimals=2, suffix="%")

        fine = QTableWidgetItem("0.00")
        fine.setFlags(
            fine.flags() & ~Qt.ItemFlag.ItemIsEditable
        )

        making_rate = spinbox(decimals=0)

        making_amount = QTableWidgetItem("₹0.00")
        making_amount.setFlags(
            making_amount.flags() & ~Qt.ItemFlag.ItemIsEditable
        )

        calculated_amount = QTableWidgetItem("₹0.00")
        calculated_amount.setFlags(
            calculated_amount.flags() & ~Qt.ItemFlag.ItemIsEditable
        )

        actual_amount = spinbox(decimals=2)
        actual_amount.setProperty("actual_touched", False)

        discount = QTableWidgetItem("₹0.00")
        discount.setFlags(
            discount.flags() & ~Qt.ItemFlag.ItemIsEditable
        )

        remove = QPushButton("Remove")
        remove.setMinimumHeight(32)
        remove.setMinimumWidth(78)

        for widget in (
            item,
            rate,
            gross,
            touch,
            making_rate,
            actual_amount,
        ):
            widget.setMinimumHeight(34)
            widget.setMinimumWidth(75)

        for widget in (
            fine,
            making_amount,
            calculated_amount,
            discount,
        ):
            widget.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

        self.items_table.setCellWidget(row_index, 0, item)
        self.items_table.setCellWidget(row_index, 1, rate)
        self.items_table.setCellWidget(row_index, 2, gross)
        self.items_table.setCellWidget(row_index, 3, touch)
        self.items_table.setItem(row_index, 4, fine)
        self.items_table.setCellWidget(row_index, 5, making_rate)
        self.items_table.setItem(row_index, 6, making_amount)
        self.items_table.setItem(row_index, 7, calculated_amount)
        self.items_table.setCellWidget(row_index, 8, actual_amount)
        self.items_table.setItem(row_index, 9, discount)
        self.items_table.setCellWidget(row_index, 10, remove)

        record = {
            "item": item,
            "rate": rate,
            "gross": gross,
            "touch": touch,
            "fine": fine,
            "making_rate": making_rate,
            "making_amount": making_amount,
            "calculated_amount": calculated_amount,
            "actual_amount": actual_amount,
            "actual_touched": False,
            "discount": discount,
            "remove": remove,
        }

        self.item_rows.append(record)

        for widget in (
            rate,
            gross,
            touch,
            making_rate,
            actual_amount,
        ):
            widget.setValue(0)

        self.update_rate_fields()

        for widget in (
            rate,
            gross,
            touch,
            making_rate,
        ):
            widget.valueChanged.connect(
                self.recalculate_totals
            )

        actual_amount.valueChanged.connect(
            lambda _value, record=record:
                self.mark_actual_amount_edited(record)
        )

        item.currentIndexChanged.connect(
            self.recalculate_totals
        )

        remove.clicked.connect(
            lambda checked=False, target=row_index:
                self.remove_item_row(target)
        )

        self.recalculate_totals()
        return True

    def update_rate_fields(self, *_):
        """Gold and Silver settlements do not use a rate in this purchase form."""
        settlement = self.settlement_input.currentText()
        lock_rate = settlement in ("Gold", "Silver")

        for row in self.item_rows:
            rate = row["rate"]

            if lock_rate and rate.value() != 0:
                rate.setValue(0)

            rate.setEnabled(
                not lock_rate and not self.read_only
            )

    def remove_item_row(self, target):
        if len(self.item_rows) <= 1:
            QMessageBox.information(
                self,
                "Purchase Items",
                "A purchase must contain at least one item.",
            )
            return

        self.items_table.removeRow(target)
        self.rebuild_rows()
        self.recalculate_totals()

    def rebuild_rows(self):
        self.item_rows = []

        for row_index in range(self.items_table.rowCount()):
            record = {
                "item": self.items_table.cellWidget(row_index, 0),
                "rate": self.items_table.cellWidget(row_index, 1),
                "gross": self.items_table.cellWidget(row_index, 2),
                "touch": self.items_table.cellWidget(row_index, 3),
                "fine": self.items_table.item(row_index, 4),
                "making_rate": self.items_table.cellWidget(row_index, 5),
                "making_amount": self.items_table.item(row_index, 6),
                "calculated_amount": self.items_table.item(row_index, 7),
                "actual_amount": self.items_table.cellWidget(row_index, 8),
                "actual_touched": bool(
                    self.items_table.cellWidget(
                        row_index, 8
                    ).property("actual_touched")
                ),
                "discount": self.items_table.item(row_index, 9),
                "remove": self.items_table.cellWidget(row_index, 10),
            }

            self.item_rows.append(record)

            button = record["remove"]

            try:
                button.clicked.disconnect()
            except RuntimeError:
                pass

            button.clicked.connect(
                lambda checked=False, target=row_index:
                    self.remove_item_row(target)
            )

    def mark_actual_amount_edited(self, record):
        record["actual_touched"] = True

        record["actual_amount"].setProperty(
            "actual_touched",
            True,
        )

        self.recalculate_totals()

    def calculate_line(self, row):
        gross = row["gross"].value()
        touch = row["touch"].value()
        rate = row["rate"].value()
        making_rate = row["making_rate"].value()

        fine = gross * touch / 100
        silver_value = fine * rate / 1000
        making = gross * making_rate / 1000

        calculated_amount = silver_value + making

        actual_widget = row["actual_amount"]

        if not row.get("actual_touched", False):
            actual_widget.blockSignals(True)
            actual_widget.setValue(calculated_amount)
            actual_widget.blockSignals(False)

        actual_amount = actual_widget.value()

        discount = round(
            calculated_amount - actual_amount,
            2,
        )

        return {
            "item_id": row["item"].currentData(),
            "item_name": row["item"].currentText(),
            "gross": gross,
            "touch": touch,
            "fine": fine,
            "rate": rate,
            "making_rate": making_rate,
            "making": making,
            "silver_value": silver_value,
            "discount": discount,
            "calculated_amount": calculated_amount,
            "amount": actual_amount,
        }

    def recalculate_totals(self, *_):
        lines = [
            self.calculate_line(row)
            for row in self.item_rows
        ]

        gross = sum(line["gross"] for line in lines)
        fine = sum(line["fine"] for line in lines)
        silver_value = sum(line["silver_value"] for line in lines)
        making = sum(line["making"] for line in lines)
        discount = sum(line["discount"] for line in lines)
        full_amount = sum(line["amount"] for line in lines)

        for row, line in zip(self.item_rows, lines):
            row["fine"].setText(
                f'{line["fine"]:,.2f}'
            )

            row["making_amount"].setText(
                money(line["making"])
            )

            row["calculated_amount"].setText(
                money(line["calculated_amount"])
            )

            row["discount"].setText(
                money(line["discount"])
            )

        self.gross_label.setText(
            f"{gross:,.2f} g"
        )

        self.fine_label.setText(
            f"{fine:,.2f} g"
        )

        self.silver_label.setText(
            money(silver_value)
        )

        self.making_label.setText(
            money(making)
        )

        self.discount_label.setText(
            money(discount)
        )

        if self.settlement_input.currentText() in ("Silver", "Gold"):
            money_due = max(
                0,
                full_amount - silver_value,
            )

            self.amount_label.setText(
                money(money_due)
            )

            self.metal_label.setText(
                f'{fine:,.2f} g '
                f'{self.settlement_input.currentText().lower()}'
            )

        else:
            self.amount_label.setText(
                money(full_amount)
            )

            self.metal_label.setText("0.00 g")

    def load_transaction(self, transaction_id):
        with get_connection() as conn:
            conn.row_factory = sqlite3.Row

            transaction = conn.execute(
                "SELECT * FROM Transactions WHERE ID = ?",
                (transaction_id,),
            ).fetchone()

            if transaction is None:
                QMessageBox.warning(
                    self,
                    "Not Found",
                    "This purchase no longer exists.",
                )
                self.reject()
                return

            saved_items = conn.execute("""
                SELECT *
                FROM Transaction_items
                WHERE Transaction_ID = ?
                ORDER BY ID
            """, (
                transaction_id,
            )).fetchall()

        parsed_date = QDate.fromString(
            str(transaction["Date"] or ""),
            "yyyy-MM-dd",
        )

        if parsed_date.isValid():
            self.date_input.setDate(parsed_date)

        if transaction["Customer ID"] is not None:
            self.party_type.setCurrentText("Customer")
            self.refresh_parties()
            party_id = transaction["Customer ID"]

        else:
            self.party_type.setCurrentText("Vendor")
            self.refresh_parties()
            party_id = transaction["Vendor ID"]

        party_index = self.party_input.findData(party_id)

        if party_index >= 0:
            self.party_input.setCurrentIndex(party_index)

        settlement_index = self.settlement_input.findText(
            transaction["Settlement"] or "Cash"
        )

        if settlement_index >= 0:
            self.settlement_input.setCurrentIndex(
                settlement_index
            )

        self.items_table.setRowCount(0)
        self.item_rows.clear()

        for saved in saved_items:
            if not self.add_item_row():
                break

            row = self.item_rows[-1]

            item_index = row["item"].findData(
                saved["Item_ID"]
            )

            if item_index < 0:
                item_index = row["item"].findText(
                    saved["Item_name"] or ""
                )

            if item_index >= 0:
                row["item"].setCurrentIndex(item_index)

            row["rate"].setValue(
                number(saved["Rate"])
            )

            row["gross"].setValue(
                number(saved["Gross_weight"])
            )

            row["touch"].setValue(
                number(saved["Tounch"])
            )

            row["making_rate"].setValue(
                number(saved["Making"])
            )

            row["actual_amount"].setValue(
                number(saved["Amount"])
            )

            row["actual_touched"] = True

            row["actual_amount"].setProperty(
                "actual_touched",
                True,
            )

        self.update_rate_fields()

        if not saved_items:
            self.add_item_row()

        self.recalculate_totals()

    def set_read_only(self, read_only):
        """Enable or disable editable fields when showing a purchase."""
        self.read_only = read_only

        for widget in (
            self.date_input,
            self.party_type,
            self.party_input,
            self.settlement_input,
            self.add_button,
        ):
            widget.setEnabled(not read_only)

        for row in self.item_rows:
            for key in (
                "item",
                "rate",
                "gross",
                "touch",
                "making_rate",
                "actual_amount",
                "remove",
            ):
                row[key].setEnabled(not read_only)

        self.update_rate_fields()

        self.save_button.setVisible(
            not read_only
        )

        self.cancel_button.setText(
            "Close" if read_only else "Cancel"
        )

    def save_purchase(self):
        if self.read_only:
            self.accept()
            return

        if self.party_input.currentData() is None:
            QMessageBox.warning(
                self,
                "Select Party",
                "Please select a customer or vendor.",
            )
            return

        lines = []

        try:
            for row in self.item_rows:
                line = self.calculate_line(row)

                if line["item_id"] is None:
                    raise ValueError(
                        "Select an item in every row."
                    )

                if line["gross"] <= 0:
                    raise ValueError(
                        "Gross weight must be greater than zero."
                    )

                if (
                    self.settlement_input.currentText()
                    not in ("Gold", "Silver")
                    and line["rate"] <= 0
                ):
                    raise ValueError(
                        "Rate must be greater than zero."
                    )

                if not 0 < line["touch"] <= 100:
                    raise ValueError(
                        "Touch must be above 0% and at most 100%."
                    )

                if line["amount"] < 0:
                    raise ValueError(
                        "Actual purchase amount cannot be negative."
                    )

                lines.append(line)

            if not lines:
                raise ValueError(
                    "Add at least one item."
                )

        except ValueError as exc:
            QMessageBox.warning(
                self,
                "Check Purchase",
                str(exc),
            )
            return

        settlement = self.settlement_input.currentText()

        customer_id = (
            self.party_input.currentData()
            if self.party_type.currentText() == "Customer"
            else None
        )

        vendor_id = (
            self.party_input.currentData()
            if self.party_type.currentText() == "Vendor"
            else None
        )

        gross_total = sum(
            line["gross"] for line in lines
        )

        fine_total = sum(
            line["fine"] for line in lines
        )

        making_total = sum(
            line["making"] for line in lines
        )

        discount_total = sum(
            line["discount"] for line in lines
        )

        full_amount = sum(
            line["amount"] for line in lines
        )

        if settlement in ("Silver", "Gold"):
            amount_to_store = max(
                0,
                making_total - discount_total,
            )

            metal_weight = fine_total
            direction = settlement

        else:
            amount_to_store = full_amount
            metal_weight = 0
            direction = None

        try:
            with get_connection() as conn:
                cursor = conn.cursor()

                required = {
                    "Date",
                    "Transaction Type",
                    "Customer ID",
                    "Vendor ID",
                    "Settlement",
                    "Total Weight",
                    "Total Amount",
                    "Total Weight Exchange",
                    "Direction",
                    "Exchange Fee",
                }

                missing = required - get_table_columns(
                    cursor,
                    "Transactions",
                )

                if missing:
                    raise RuntimeError(
                        "Transactions table is missing columns: "
                        + ", ".join(sorted(missing))
                    )

                if self.transaction_id is None:
                    cursor.execute("""
                        INSERT INTO Transactions (
                            Date,
                            "Transaction Type",
                            "Customer ID",
                            "Vendor ID",
                            Settlement,
                            "Total Weight",
                            "Total Amount",
                            "Total Weight Exchange",
                            Direction,
                            "Exchange Fee"
                        )
                        VALUES (
                            ?, 'Purchase', ?, ?, ?, ?, ?, ?, ?, ?
                        )
                    """, (
                        self.date_input.date().toString("yyyy-MM-dd"),
                        customer_id,
                        vendor_id,
                        settlement,
                        gross_total,
                        amount_to_store,
                        metal_weight,
                        direction,
                        making_total,
                    ))

                    transaction_id = cursor.lastrowid

                else:
                    transaction_id = self.transaction_id

                    cursor.execute("""
                        SELECT ID
                        FROM Transactions
                        WHERE ID = ?
                          AND "Transaction Type" = 'Purchase'
                    """, (
                        transaction_id,
                    ))

                    if cursor.fetchone() is None:
                        raise RuntimeError(
                            "The purchase could not be found."
                        )

                    # Editing a purchase rebuilds its ledger entries.
                    if get_table_columns(cursor, "Ledger"):
                        cursor.execute(
                            'DELETE FROM Ledger WHERE "Transaction ID" = ?',
                            (transaction_id,),
                        )

                    # Remove this purchase's previous incoming stock movements.
                    cursor.execute("""
                        DELETE FROM Inventory
                        WHERE "Transaction ID" = ?
                          AND "Item Movement" = 'Purchase'
                    """, (
                        transaction_id,
                    ))

                    cursor.execute("""
                        UPDATE Transactions
                        SET Date = ?,
                            "Customer ID" = ?,
                            "Vendor ID" = ?,
                            Settlement = ?,
                            "Total Weight" = ?,
                            "Total Amount" = ?,
                            "Total Weight Exchange" = ?,
                            Direction = ?,
                            "Exchange Fee" = ?
                        WHERE ID = ?
                    """, (
                        self.date_input.date().toString("yyyy-MM-dd"),
                        customer_id,
                        vendor_id,
                        settlement,
                        gross_total,
                        amount_to_store,
                        metal_weight,
                        direction,
                        making_total,
                        transaction_id,
                    ))

                    cursor.execute(
                        "DELETE FROM Transaction_items "
                        "WHERE Transaction_ID = ?",
                        (transaction_id,),
                    )

                for line in lines:
                    cursor.execute("""
                        INSERT INTO Transaction_items (
                            Transaction_ID,
                            Item_name,
                            Rate,
                            Gross_weight,
                            Tounch,
                            Making,
                            Net_weight,
                            Calculated_amount,
                            Amount,
                            Discount,
                            Type,
                            Section,
                            Item_ID
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        transaction_id,
                        line["item_name"],
                        line["rate"],
                        line["gross"],
                        line["touch"],
                        line["making_rate"],
                        line["fine"],
                        line["calculated_amount"],
                        line["amount"],
                        line["discount"],
                        "Purchase",
                        settlement,
                        line["item_id"],
                    ))

                    # Purchases add physical gross weight to inventory, in grams.
                    cursor.execute("""
                        INSERT INTO Inventory (
                            "Item ID",
                            "Transaction ID",
                            "Item Movement",
                            Weight
                        )
                        VALUES (?, ?, 'Purchase', ?)
                    """, (
                        line["item_id"],
                        transaction_id,
                        abs(line["gross"]),
                    ))

                # Ledger entries are saved in the same transaction.
                # Any error rolls back the purchase, items, stock and ledger.
                insert_purchase_ledger_entries(
                    cursor=cursor,
                    transaction_id=transaction_id,
                    customer_id=customer_id,
                    vendor_id=vendor_id,
                    settlement=settlement,
                    full_amount=full_amount,
                    fine_total=fine_total,
                    amount_to_store=amount_to_store,
                )

                conn.commit()

            self.saved = True

            QMessageBox.information(
                self,
                "Purchase Saved",
                f"Purchase #{transaction_id} saved successfully.",
            )

            self.accept()

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Could Not Save Purchase",
                "The purchase was not saved. Database changes were rolled back.\n\n"
                f"Details: {exc}",
            )
