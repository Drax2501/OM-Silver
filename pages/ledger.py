
import sqlite3

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDialog,
    QDialogButtonBox,
    QMessageBox,
)

from database import get_connection
from ui import BasePage


# ==========================================================
# HELPERS
# ==========================================================

def format_number(value, decimals=2):
    value = float(value or 0)
    return f"{value:,.{decimals}f}"


def format_balance(value, kind):
    """Display a debit-positive balance as Dr or Cr."""
    value = float(value or 0)

    if kind == "Amount":
        number = f"₹{abs(value):,.2f}"
    else:
        number = f"{abs(value):,.3f} g"

    if value > 0:
        return f"{number} Dr"
    elif value < 0:
        return f"{number} Cr"

    return number


def make_table(headers):
    table = QTableWidget()
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)

    table.setEditTriggers(
        QTableWidget.EditTrigger.NoEditTriggers
    )
    table.setSelectionBehavior(
        QTableWidget.SelectionBehavior.SelectRows
    )
    table.setSelectionMode(
        QTableWidget.SelectionMode.SingleSelection
    )
    table.setAlternatingRowColors(True)
    table.verticalHeader().setVisible(False)

    header = table.horizontalHeader()
    header.setSectionResizeMode(
        QHeaderView.ResizeMode.ResizeToContents
    )
    header.setStretchLastSection(True)

    return table


def put_cell(table, row, column, value, align=None):
    item = QTableWidgetItem(str(value))

    if align is not None:
        item.setTextAlignment(align)

    table.setItem(row, column, item)


# ==========================================================
# INDIVIDUAL ACCOUNT LEDGER WINDOW
# ==========================================================

class AccountLedgerDialog(QDialog):

    LEDGER_FIELDS = {
        "Amount": {
            "debit": "Amount Debit",
            "credit": "Amount Credit",
            "display_debit": "Display A/c Debit",
            "display_credit": "Display A/c Credit",
            "decimals": 2,
        },
        "Silver": {
            "debit": "Silver Debit",
            "credit": "Silver Credit",
            "display_debit": "Silver Display Debit",
            "display_credit": "Silver Display Credit",
            "decimals": 3,
        },
        "Gold": {
            "debit": "Gold Debit",
            "credit": "Gold Credit",
            "display_debit": "Gold Display Debit",
            "display_credit": "Gold Display Credit",
            "decimals": 3,
        },
        
    }

    def __init__(self, account, parent=None):
        super().__init__(parent)

        self.account = account

        self.setWindowTitle(
            f"Ledger - {account['name']} "
            f"({account['type']} ID: {account['id']})"
        )
        self.resize(1100, 650)

        layout = QVBoxLayout(self)

        title = QLabel(
            f"{account['name']}  |  "
            f"{account['type']} ID: {account['id']}"
        )
        title.setStyleSheet(
            "font-size: 18px; font-weight: bold; padding: 6px;"
        )
        layout.addWidget(title)

        balance_layout = QHBoxLayout()

        self.amount_balance = QLabel("Amount: —")
        self.silver_balance = QLabel("Silver: —")
        self.gold_balance = QLabel("Gold: —")

        for label in (
            self.amount_balance,
            self.silver_balance,
            self.gold_balance,
        ):
            label.setStyleSheet(
                "font-size: 14px; font-weight: bold; "
                "padding: 10px; border: 1px solid #888; "
                "border-radius: 5px;"
            )
            balance_layout.addWidget(label)

        layout.addLayout(balance_layout)

        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Ledger:"))

        self.ledger_selector = QComboBox()
        self.ledger_selector.addItems(
            ["Amount", "Silver", "Gold"]
        )
        self.ledger_selector.currentTextChanged.connect(
            self.load_entries
        )

        selector_layout.addWidget(self.ledger_selector)
        selector_layout.addStretch()
        layout.addLayout(selector_layout)

        # Traditional ledger layout: debit on the left, credit on the right.
        ledger_layout = QHBoxLayout()
        ledger_layout.setSpacing(12)

        debit_layout = QVBoxLayout()
        debit_heading = QLabel("DEBIT (Dr)")
        debit_heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        debit_heading.setStyleSheet(
            "font-size: 15px; font-weight: bold; padding: 8px; "
            "background-color: #E8D9D5; border: 1px solid #D4C0BC;"
        )
        debit_layout.addWidget(debit_heading)

        self.debit_table = make_table(["Date", "Transaction ID", "Particulars", "Debit"])
        self.debit_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        debit_layout.addWidget(self.debit_table)

        self.debit_total = QLabel("Total Debit: ₹0.00")
        self.debit_total.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.debit_total.setStyleSheet(
            "font-size: 14px; font-weight: bold; padding: 10px; border-top: 2px solid #555;"
        )
        debit_layout.addWidget(self.debit_total)

        credit_layout = QVBoxLayout()
        credit_heading = QLabel("CREDIT (Cr)")
        credit_heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credit_heading.setStyleSheet(
            "font-size: 15px; font-weight: bold; padding: 8px; "
            "background-color: #E8D9D5; border: 1px solid #D4C0BC;"
        )
        credit_layout.addWidget(credit_heading)

        self.credit_table = make_table(["Date", "Transaction ID", "Particulars", "Credit"])
        self.credit_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        credit_layout.addWidget(self.credit_table)

        self.credit_total = QLabel("Total Credit: ₹0.00")
        self.credit_total.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.credit_total.setStyleSheet(
            "font-size: 14px; font-weight: bold; padding: 10px; border-top: 2px solid #555;"
        )
        credit_layout.addWidget(self.credit_total)

        ledger_layout.addLayout(debit_layout, 1)
        ledger_layout.addLayout(credit_layout, 1)
        layout.addLayout(ledger_layout)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close
        )
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

        self.load_balances()
        self.load_entries()


    def account_filter(self):
        account_type = self.account["type"]
        account_id = self.account["id"]

        if account_type == "Customer":
            return 'l."Customer ID" = ?', account_id

        if account_type == "Vendor":
            return 'l."Vendor ID" = ?', account_id

        return 'l."Other Account ID" = ?', account_id


    def load_balances(self):
        condition, account_id = self.account_filter()

        query = f"""
            SELECT
                COALESCE(SUM("Amount Debit"), 0),
                COALESCE(SUM("Amount Credit"), 0),
                COALESCE(SUM("Silver Debit"), 0),
                COALESCE(SUM("Silver Credit"), 0),
                COALESCE(SUM("Gold Debit"), 0),
                COALESCE(SUM("Gold Credit"), 0)
                    FROM "Ledger" AS l
                    WHERE {condition}
        """

        conn = get_connection()

        try:
            row = conn.execute(
                query, (account_id,)
            ).fetchone()
        finally:
            conn.close()

        amount = row[0] - row[1]
        silver = row[2] - row[3]
        gold = row[4] - row[5]

        self.amount_balance.setText(
            "Amount: " + format_balance(amount, "Amount")
        )
        self.silver_balance.setText(
            "Silver: " + format_balance(silver, "Silver")
        )
        self.gold_balance.setText(
            "Gold: " + format_balance(gold, "Gold")
        )

    def load_entries(self, *_):
        ledger_type = self.ledger_selector.currentText()
        fields = self.LEDGER_FIELDS[ledger_type]

        condition, account_id = self.account_filter()

        query = f"""
            SELECT
                t."Date",
                l."Transaction ID",
                l."{fields['display_debit']}",
                l."{fields['display_credit']}",
                l."{fields['debit']}",
                l."{fields['credit']}",
                l."ID"
            FROM "Ledger" AS l
            LEFT JOIN "Transactions" AS t
                ON t."ID" = l."Transaction ID"
            WHERE {condition}
                AND (
                    COALESCE(l."{fields['debit']}", 0) != 0
                    OR COALESCE(l."{fields['credit']}", 0) != 0
                )
            ORDER BY
                CASE WHEN t."Date" IS NULL THEN 1 ELSE 0 END,
                t."Date" ASC,
                l."ID" ASC
        """

        conn = get_connection()

        try:
            rows = conn.execute(
                query, (account_id,)
            ).fetchall()
        except sqlite3.Error as error:
            QMessageBox.critical(
                self,
                "Ledger Error",
                f"Could not load ledger entries:\n{error}",
            )
            return
        finally:
            conn.close()

        self.debit_table.setRowCount(0)
        self.credit_table.setRowCount(0)

        debit_total = 0.0
        credit_total = 0.0

        for (
            date, transaction_id, display_debit, display_credit,
            debit, credit, entry_id,
        ) in rows:
            debit = float(debit or 0)
            credit = float(credit or 0)
            transaction_label = transaction_id if transaction_id is not None else "—"

            if debit != 0:
                row = self.debit_table.rowCount()
                self.debit_table.insertRow(row)
                put_cell(self.debit_table, row, 0, date or "—")
                put_cell(self.debit_table, row, 1, transaction_label)
                put_cell(self.debit_table, row, 2, display_debit or "")
                put_cell(
                    self.debit_table, row, 3,
                    format_number(debit, fields["decimals"]),
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                )
                debit_total += debit

            if credit != 0:
                row = self.credit_table.rowCount()
                self.credit_table.insertRow(row)
                put_cell(self.credit_table, row, 0, date or "—")
                put_cell(self.credit_table, row, 1, transaction_label)
                put_cell(self.credit_table, row, 2, display_credit or "")
                put_cell(
                    self.credit_table, row, 3,
                    format_number(credit, fields["decimals"]),
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                )
                credit_total += credit

        if self.debit_table.rowCount() == 0:
            self.debit_table.setRowCount(1)
            item = QTableWidgetItem("No debit entries")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.debit_table.setItem(0, 0, item)
            self.debit_table.setSpan(0, 0, 1, 4)

        if self.credit_table.rowCount() == 0:
            self.credit_table.setRowCount(1)
            item = QTableWidgetItem("No credit entries")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.credit_table.setItem(0, 0, item)
            self.credit_table.setSpan(0, 0, 1, 4)

        unit = "₹" if ledger_type == "Amount" else ""
        suffix = "" if ledger_type == "Amount" else " g"
        self.debit_total.setText(
            f"Total Debit: {unit}{debit_total:,.{fields['decimals']}f}{suffix}"
        )
        self.credit_total.setText(
            f"Total Credit: {unit}{credit_total:,.{fields['decimals']}f}{suffix}"
        )


class LedgerPage(BasePage):

    def __init__(self):
        # Use the existing BasePage header and content area.
        super().__init__(
            title="Ledger",
            description=(
                "Search customers, vendors and other accounts "
                "to open their ledgers."
            ),
        )

        # IMPORTANT:
        # Add page controls to BasePage's content_layout.
        # Do not use self.layout() to add a second page heading.
        layout = self.content_layout

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(
            "Search by account name, ID or account type..."
        )
        self.search_box.textChanged.connect(
            self.load_accounts
        )
        layout.addWidget(self.search_box)

        self.accounts_table = make_table([
            "Account ID",
            "Account Name",
            "Account Type",
            "Action",
        ])
        layout.addWidget(self.accounts_table)

        self.load_accounts()

    def load_accounts(self, *_):
        search = self.search_box.text().strip()
        conn = get_connection()

        try:
            customers = conn.execute("""
                SELECT
                    "Customer ID",
                    "Name",
                    "Shop Name"
                FROM "Customers"
                ORDER BY "Name" COLLATE NOCASE
            """).fetchall()

            vendors = conn.execute("""
                SELECT
                    "ID",
                    "Name",
                    "Firm Name"
                FROM "Vendors"
                ORDER BY "Name" COLLATE NOCASE
            """).fetchall()

            others = conn.execute("""
                SELECT
                    "ID",
                    "Name",
                    "Account Type"
                FROM "Other_Accounts"
                ORDER BY "Name" COLLATE NOCASE
            """).fetchall()

        except sqlite3.Error as error:
            QMessageBox.critical(
                self,
                "Accounts Error",
                f"Could not load accounts:\n{error}",
            )
            return
        finally:
            conn.close()

        accounts = []

        for account_id, name, shop_name in customers:
            accounts.append({
                "id": account_id,
                "name": name or shop_name or "Unnamed customer",
                "type": "Customer",
                "extra": shop_name or "",
            })

        for account_id, name, firm_name in vendors:
            accounts.append({
                "id": account_id,
                "name": name or firm_name or "Unnamed vendor",
                "type": "Vendor",
                "extra": firm_name or "",
            })

        for account_id, name, account_type in others:
            accounts.append({
                "id": account_id,
                "name": name or "Unnamed account",
                "type": "Other Account",
                "extra": account_type or "",
            })

        search_lower = search.casefold()

        if search:
            accounts = [
                account
                for account in accounts
                if search_lower in str(account["id"]).casefold()
                or search_lower in account["name"].casefold()
                or search_lower in account["type"].casefold()
                or search_lower in account["extra"].casefold()
            ]

        accounts.sort(
            key=lambda account: (
                account["name"].casefold(),
                account["type"],
                str(account["id"]),
            )
        )

        self.accounts_table.setRowCount(0)

        for account in accounts:
            row = self.accounts_table.rowCount()
            self.accounts_table.insertRow(row)

            prefix = {
                "Customer": "C",
                "Vendor": "V",
                "Other Account": "O",
            }[account["type"]]

            put_cell(
                self.accounts_table,
                row,
                0,
                f"{prefix}-{account['id']}",
            )
            put_cell(
                self.accounts_table,
                row,
                1,
                account["name"],
            )
            put_cell(
                self.accounts_table,
                row,
                2,
                account["type"],
            )

            view_button = QPushButton("View")
            view_button.setMinimumWidth(40)
            view_button.setStyleSheet("""
                QPushButton {
                    padding: 0 8px;
                    margin: 0px;
                    border-radius: 4px;
                }
            """)
            view_button.clicked.connect(
                lambda checked=False, a=account:
                    self.open_ledger(a)
            )
            self.accounts_table.setCellWidget(
                row, 3, view_button
            )

    def open_ledger(self, account):
        dialog = AccountLedgerDialog(account, self)
        dialog.exec()
