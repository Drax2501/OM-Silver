
import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QComboBox,
    QPushButton,
    QScrollArea,
    QMessageBox,
)

from ui import BasePage, AddButton, AppDialog
from database import get_connection


DIRECTORIES = {
    "Customers": {
        "table": "Customers",
        "id_column": "Customer ID",
        "fields": [
            ("Name", True),
            ("Shop Name", True),
            ("Contact Number", False),
            ("GST IN", False),
            ("Address", False),
        ],
    },
    "Vendors": {
        "table": "Vendors",
        "id_column": "ID",
        "fields": [
            ("Name", True),
            ("Firm Name", True),
            ("Contact Number", False),
            ("GST IN", False),
            ("Address", False),
        ],
    },
    "Other Accounts": {
        "table": "Other_Accounts",
        "id_column": "ID",
        "fields": [
            ("Name", True),
            ("Account Type", True),
        ],
    },
}

ACCOUNT_TYPES = [
    "Expense",
    "Income",
    "Asset",
    "Liability",
]


class DirectoryPage(BasePage):
    def __init__(self, parent=None):
        super().__init__(
            "Directory",
            "Manage customers, vendors, and other accounts.",
            parent,
        )

        self.columns = {}

        self.build_page()
        self.refresh_all()

    def build_page(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(16)

        for directory_name, config in DIRECTORIES.items():
            column = self.create_column(directory_name, config)
            main_layout.addWidget(column, 1)

        self.add_content(main_widget)

    def create_column(self, directory_name, config):
        column = QWidget()
        column.setObjectName("directoryColumn")
        column.setStyleSheet("""
            QWidget#directoryColumn {
                background-color: white;
                border: 1px solid #E2E5E9;
                border-radius: 10px;
            }
        """)

        layout = QVBoxLayout(column)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        header_layout = QHBoxLayout()

        heading = QLabel(directory_name)
        heading.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #222831;
            border: none;
        """)

        add_button = AddButton("+ Add")
        add_button.clicked.connect(
            lambda checked=False, name=directory_name:
                self.open_record_dialog(name)
        )

        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(add_button)

        layout.addLayout(header_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        records_widget = QWidget()
        records_widget.setStyleSheet("border: none;")

        records_layout = QVBoxLayout(records_widget)
        records_layout.setContentsMargins(0, 0, 0, 0)
        records_layout.setSpacing(8)
        records_layout.addStretch()

        scroll_area.setWidget(records_widget)
        layout.addWidget(scroll_area)

        self.columns[directory_name] = {
            "config": config,
            "records_layout": records_layout,
            "records_widget": records_widget,
        }

        return column

    def refresh_all(self):
        for directory_name in DIRECTORIES:
            self.refresh_column(directory_name)

    def refresh_column(self, directory_name):
        column_data = self.columns[directory_name]
        config = column_data["config"]
        layout = column_data["records_layout"]

        while layout.count() > 1:
            item = layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        conn = get_connection()

        try:
            cursor = conn.cursor()
            cursor.execute(
                f'SELECT * FROM "{config["table"]}" '
                f'ORDER BY "{config["id_column"]}" DESC'
            )

            records = cursor.fetchall()
            column_names = [
                description[0]
                for description in cursor.description
            ]

        except Exception as error:
            QMessageBox.critical(
                self,
                "Database Error",
                f"Could not load {directory_name}:\n{error}",
            )
            return

        finally:
            conn.close()

        if not records:
            empty_label = QLabel(
                f"No {directory_name.lower()} yet."
            )
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("""
                color: #777777;
                padding: 18px 4px;
                border: none;
            """)

            layout.insertWidget(0, empty_label)
            return

        for record in records:
            record_data = dict(zip(column_names, record))

            card = QWidget()
            card.setObjectName("recordCard")
            card.setStyleSheet("""
                QWidget#recordCard {
                    background-color: #F7F8FA;
                    border: 1px solid #E5E7EB;
                    border-radius: 8px;
                }
            """)

            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(10, 9, 10, 9)
            card_layout.setSpacing(5)

            name_label = QLabel(
                str(record_data.get("Name", "Unnamed"))
            )
            name_label.setWordWrap(True)
            name_label.setStyleSheet("""
                font-weight: 600;
                font-size: 14px;
                color: #222831;
                border: none;
            """)

            card_layout.addWidget(name_label)

            if directory_name == "Customers":
                detail = record_data.get("Shop Name", "")
            elif directory_name == "Vendors":
                detail = record_data.get("Firm Name", "")
            else:
                detail = record_data.get("Account Type", "")

            if detail:
                detail_label = QLabel(str(detail))
                detail_label.setWordWrap(True)
                detail_label.setStyleSheet("""
                    color: #626A73;
                    font-size: 12px;
                    border: none;
                """)

                card_layout.addWidget(detail_label)

            view_button = QPushButton("View")
            view_button.setCursor(
                Qt.CursorShape.PointingHandCursor
            )
            view_button.setStyleSheet("""
                QPushButton {
                    background-color: #E9EDF3;
                    color: #263445;
                    border: none;
                    border-radius: 5px;
                    padding: 7px;
                }
                QPushButton:hover {
                    background-color: #DCE3EC;
                }
            """)

            view_button.clicked.connect(
                lambda checked=False,
                name=directory_name,
                data=record_data.copy():
                    self.open_view_dialog(name, data)
            )

            card_layout.addWidget(view_button)
            layout.insertWidget(layout.count() - 1, card)

    def open_view_dialog(self, directory_name, record):
        config = DIRECTORIES[directory_name]

        if directory_name == "Customers":
            title = "Customer Details"
        elif directory_name == "Vendors":
            title = "Vendor Details"
        else:
            title = "Account Details"

        dialog = AppDialog(
            title=title,
            parent=self,
            show_footer=False,
        )

        content = QWidget()
        layout = QFormLayout(content)
        layout.setSpacing(12)

        layout.addRow(
            "ID",
            QLabel(str(record[config["id_column"]])),
        )

        for field, required in config["fields"]:
            value = record.get(field, "")
            value_label = QLabel(str(value or "—"))
            value_label.setWordWrap(True)
            layout.addRow(field, value_label)

        dialog.add_content(content)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_button = QPushButton("Close")
        close_button.setStyleSheet("""
            QPushButton {

                border-radius: 6px;
                padding: 9px 18px;
            }
        """)

        close_button.clicked.connect(dialog.accept)
        button_layout.addWidget(close_button)

        edit_button = QPushButton("Edit")
        edit_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        edit_button.setStyleSheet("""
            QPushButton {
                background-color: #263445;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 9px 18px;
            }
            QPushButton:hover {
                background-color: #364B63;
            }
        """)

        edit_button.clicked.connect(
            lambda checked=False:
                self.open_edit_from_view(
                    directory_name,
                    record,
                    dialog,
                )
        )

        button_layout.addWidget(edit_button)

        dialog.add_content(self._button_widget(button_layout))
        dialog.exec()

    def open_edit_from_view(
        self,
        directory_name,
        record,
        view_dialog,
    ):
        view_dialog.accept()
        self.open_record_dialog(directory_name, record)

    def open_record_dialog(self, directory_name, record=None):
        config = DIRECTORIES[directory_name]
        is_editing = record is not None

        if directory_name == "Other Accounts":
            singular_name = "Other Account"
        else:
            singular_name = directory_name[:-1]

        title = (
            f"Edit {singular_name}"
            if is_editing
            else f"Add {singular_name}"
        )

        dialog = AppDialog(
            title=title,
            parent=self,
            show_footer=False,
        )

        content = QWidget()
        form_layout = QFormLayout(content)
        form_layout.setSpacing(12)

        inputs = {}

        if is_editing:
            id_label = QLabel(
                str(record[config["id_column"]])
            )
            id_label.setStyleSheet("color: #777777;")
            form_layout.addRow("ID", id_label)

        for field, required in config["fields"]:

            # Address gets a multiline text editor.
            if field == "Address":
                input_widget = QPlainTextEdit()
                input_widget.setPlaceholderText(
                    "Enter the full address..."
                )
                input_widget.setMinimumWidth(280)
                input_widget.setMinimumHeight(100)
                input_widget.setTabChangesFocus(True)

            # Account Type gets a dropdown.
            elif (
                directory_name == "Other Accounts"
                and field == "Account Type"
            ):
                input_widget = QComboBox()
                input_widget.addItems(ACCOUNT_TYPES)
                input_widget.setMinimumWidth(220)

            else:
                input_widget = QLineEdit()
                input_widget.setMinimumWidth(220)

                if field == "Contact Number":
                    input_widget.setPlaceholderText(
                        "10-digit contact number"
                    )
                elif field == "GST IN":
                    input_widget.setPlaceholderText(
                        "GSTIN (optional)"
                    )

            inputs[field] = input_widget

            label = f"{field}{' *' if required else ''}"
            form_layout.addRow(label, input_widget)

            if is_editing:
                value = record.get(field, "")

                if isinstance(input_widget, QComboBox):
                    index = input_widget.findText(
                        str(value or "")
                    )

                    if index >= 0:
                        input_widget.setCurrentIndex(index)
                    elif value:
                        input_widget.addItem(str(value))
                        input_widget.setCurrentText(str(value))

                elif isinstance(input_widget, QPlainTextEdit):
                    input_widget.setPlainText(str(value or ""))

                else:
                    input_widget.setText(str(value or ""))

        dialog.add_content(content)

        button_layout = QHBoxLayout()

        if is_editing:
            delete_button = QPushButton("Delete")
            delete_button.setAutoDefault(False)
            delete_button.setDefault(False)
            delete_button.setStyleSheet("""
                QPushButton {
                    color: #B42318;
                    background-color: #FEE4E2;
                    border: none;
                    border-radius: 6px;
                    padding: 9px 16px;
                }
                QPushButton:hover {
                    background-color: #FECDCA;
                }
            """)

            delete_button.clicked.connect(
                lambda checked=False:
                    self.delete_record(
                        directory_name,
                        record[config["id_column"]],
                        dialog,
                    )
            )

            button_layout.addWidget(delete_button)

        button_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.setAutoDefault(False)
        cancel_button.setDefault(False)
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_button)

        save_button = QPushButton("Save")
        save_button.setDefault(True)
        save_button.setAutoDefault(True)
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #263445;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 9px 18px;
            }
            QPushButton:hover {
                background-color: #364B63;
            }
        """)

        # One shared save action for both clicking Save and pressing Enter.
        def save_current_record():
            self.save_record(
                directory_name,
                inputs,
                dialog,
                record,
            )

        save_button.clicked.connect(save_current_record)

        # Pressing Enter in a single-line field saves the form.
        # Address is multiline, so Enter there inserts a new line.
        for input_widget in inputs.values():
            if isinstance(input_widget, QLineEdit):
                input_widget.returnPressed.connect(
                    save_current_record
                )

        button_layout.addWidget(save_button)

        dialog.add_content(self._button_widget(button_layout))
        dialog.exec()

    def _button_widget(self, layout):
        widget = QWidget()
        widget.setLayout(layout)
        return widget

    def save_record(
        self,
        directory_name,
        inputs,
        dialog,
        record=None,
    ):
        config = DIRECTORIES[directory_name]
        values = {}

        for field, widget in inputs.items():
            if isinstance(widget, QComboBox):
                values[field] = widget.currentText().strip()

            elif isinstance(widget, QPlainTextEdit):
                values[field] = widget.toPlainText().strip()

            else:
                values[field] = widget.text().strip()

        # Validate required fields.
        for field, required in config["fields"]:
            if required and not values.get(field):
                QMessageBox.warning(
                    dialog,
                    "Missing Information",
                    f"Please enter or select {field}.",
                )
                return

        # Validate contact number if provided.
        contact = values.get("Contact Number", "")

        if contact and not re.fullmatch(r"\d{10}", contact):
            QMessageBox.warning(
                dialog,
                "Invalid Contact Number",
                "Please enter a 10-digit contact number.",
            )
            return

        # Validate GSTIN format if provided.
        gstin = values.get("GST IN", "").strip().upper()

        if gstin:
            gstin_pattern = (
                r"\d{2}[A-Z]{5}\d{4}[A-Z]"
                r"[1-9A-Z]Z[0-9A-Z]"
            )

            if not re.fullmatch(gstin_pattern, gstin):
                QMessageBox.warning(
                    dialog,
                    "Invalid GSTIN",
                    "Please enter a GSTIN in the expected format.",
                )
                return

            values["GST IN"] = gstin

        conn = get_connection()

        try:
            cursor = conn.cursor()
            fields = list(values.keys())

            if record is None:
                columns_sql = ", ".join(
                    f'"{field}"' for field in fields
                )
                placeholders = ", ".join(
                    "?" for _ in fields
                )

                cursor.execute(
                    f'INSERT INTO "{config["table"]}" '
                    f"({columns_sql}) VALUES ({placeholders})",
                    [values[field] for field in fields],
                )

            else:
                set_sql = ", ".join(
                    f'"{field}" = ?' for field in fields
                )

                update_values = [
                    values[field] for field in fields
                ]
                update_values.append(
                    record[config["id_column"]]
                )

                cursor.execute(
                    f'UPDATE "{config["table"]}" '
                    f"SET {set_sql} "
                    f'WHERE "{config["id_column"]}" = ?',
                    update_values,
                )

            conn.commit()

        except Exception as error:
            QMessageBox.critical(
                dialog,
                "Database Error",
                f"Could not save the record:\n{error}",
            )
            return

        finally:
            conn.close()

        dialog.accept()
        self.refresh_column(directory_name)

    def delete_record(
        self,
        directory_name,
        record_id,
        dialog,
    ):
        config = DIRECTORIES[directory_name]

        answer = QMessageBox.question(
            dialog,
            "Confirm Deletion",
            "Are you sure you want to delete this record?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        conn = get_connection()

        try:
            cursor = conn.cursor()

            cursor.execute(
                f'DELETE FROM "{config["table"]}" '
                f'WHERE "{config["id_column"]}" = ?',
                (record_id,),
            )

            conn.commit()

        except Exception as error:
            QMessageBox.critical(
                dialog,
                "Database Error",
                f"Could not delete the record:\n{error}",
            )
            return

        finally:
            conn.close()

        dialog.accept()
        self.refresh_column(directory_name)
