
import sqlite3

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QDoubleSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QHeaderView,
)

from database import get_connection
from ui import BasePage, AppDialog


class InventoryPage(BasePage):
    def __init__(self):
        super().__init__(
            "Inventory",
            "Manage item names and opening stock."
        )

        self.create_interface()
        self.refresh_items()

    def create_interface(self):
        main_layout = QVBoxLayout()

        # Top bar
        top_bar = QHBoxLayout()

        description = QLabel(
            "Items and their current recorded stock weights"
        )

        add_button = QPushButton("+ Add Item")
        add_button.clicked.connect(self.open_add_item_dialog)

        top_bar.addWidget(description)
        top_bar.addStretch()
        top_bar.addWidget(add_button)

        main_layout.addLayout(top_bar)

        # Items table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
            "Item ID",
            "Item Name",
            "Current Stock Weight"
        ])

        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )

        main_layout.addWidget(self.table)

        container = QWidget()
        container.setLayout(main_layout)

        self.add_content(container)

    def refresh_items(self):
        conn = get_connection()

        try:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    Items.ID,
                    Items.Name,
                    COALESCE(SUM(Inventory.Weight), 0)
                FROM Items
                LEFT JOIN Inventory
                    ON Inventory."Item ID" = Items.ID
                GROUP BY Items.ID, Items.Name
                ORDER BY Items.Name COLLATE NOCASE
            """)

            rows = cursor.fetchall()

        finally:
            conn.close()

        self.table.setRowCount(0)

        for item_id, name, stock_weight in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)

            id_cell = QTableWidgetItem(str(item_id))
            id_cell.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            name_cell = QTableWidgetItem(name)

            weight_cell = QTableWidgetItem(
                f"{float(stock_weight):,.3f} g"
            )
            weight_cell.setTextAlignment(
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter
            )

            self.table.setItem(row, 0, id_cell)
            self.table.setItem(row, 1, name_cell)
            self.table.setItem(row, 2, weight_cell)

    def open_add_item_dialog(self):
        dialog = AppDialog(
            title="Add Item",
            parent=self,
            show_footer=False
        )

        layout = QVBoxLayout()

        form = QFormLayout()

        name_input = QLineEdit()
        name_input.setPlaceholderText("Enter item name")

        opening_weight = QDoubleSpinBox()
        opening_weight.setRange(0, 1000000000)
        opening_weight.setDecimals(3)
        opening_weight.setSingleStep(0.100)
        opening_weight.setSuffix(" g")

        form.addRow("Item Name:", name_input)
        form.addRow("Opening Balance:", opening_weight)

        layout.addLayout(form)

        buttons = QHBoxLayout()

        cancel_button = QPushButton("Cancel")
        save_button = QPushButton("Save Item")
        save_button.setDefault(True)

        buttons.addStretch()
        buttons.addWidget(cancel_button)
        buttons.addWidget(save_button)

        layout.addLayout(buttons)

        content = QWidget()
        content.setLayout(layout)
        dialog.add_content(content)

        cancel_button.clicked.connect(dialog.reject)

        def save_item():
            name = name_input.text().strip()
            weight = opening_weight.value()

            if not name:
                QMessageBox.warning(
                    dialog,
                    "Missing Item Name",
                    "Please enter an item name."
                )
                name_input.setFocus()
                return

            conn = get_connection()

            try:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO Items ("Name")
                    VALUES (?)
                """, (name,))

                item_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO Inventory (
                        "Item ID",
                        "Transaction ID",
                        "Item Movement",
                        "Weight"
                    )
                    VALUES (?, NULL, 'Opening Balance', ?)
                """, (item_id, weight))

                conn.commit()

            except sqlite3.IntegrityError:
                conn.rollback()

                QMessageBox.warning(
                    dialog,
                    "Item Already Exists",
                    "An item with this name already exists. "
                    "Please use a different name."
                )
                name_input.setFocus()
                return

            except sqlite3.Error as error:
                conn.rollback()

                QMessageBox.critical(
                    dialog,
                    "Database Error",
                    f"Could not save the item:\n{error}"
                )
                return

            finally:
                conn.close()

            self.refresh_items()
            dialog.accept()

        save_button.clicked.connect(save_item)
        name_input.returnPressed.connect(save_item)

        dialog.exec()
