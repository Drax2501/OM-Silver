
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QFrame,
)

from database import init_db
from pages.directory import DirectoryPage
from pages.transactions import TransactionsPage
from pages.inventory import InventoryPage
from pages.ledger import LedgerPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("OM Silver")
        self.resize(1400, 850)
        self.setMinimumSize(1000, 650)

        self.create_interface()

    def create_interface(self):
        # Main application layout
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ---------------- SIDEBAR ----------------

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 24, 16, 20)
        sidebar_layout.setSpacing(10)

        app_title = QLabel("OM SILVER")
        app_title.setObjectName("appTitle")
        app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        app_subtitle = QLabel("Business Management")
        app_subtitle.setObjectName("appSubtitle")
        app_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sidebar_layout.addWidget(app_title)
        sidebar_layout.addWidget(app_subtitle)
        sidebar_layout.addSpacing(25)

        navigation_label = QLabel("WORKSPACE")
        navigation_label.setObjectName("sectionLabel")
        sidebar_layout.addWidget(navigation_label)
        sidebar_layout.addSpacing(5)

        # ---------------- PAGE STACK ----------------

        self.pages = QStackedWidget()
        self.pages.setObjectName("pageStack")

        self.directory_page = DirectoryPage()
        self.transactions_page = TransactionsPage()
        self.inventory_page = InventoryPage()
        self.ledger_page = LedgerPage()

        self.pages.addWidget(self.directory_page)
        self.pages.addWidget(self.transactions_page)
        self.pages.addWidget(self.inventory_page)
        self.pages.addWidget(self.ledger_page)

        # ---------------- NAVIGATION BUTTONS ----------------

        self.nav_buttons = []

        navigation_items = [
            ("Directory", 0),
            ("Transactions", 1),
            ("Inventory", 2),
            ("Ledger", 3),
        ]

        for label, page_index in navigation_items:
            button = QPushButton(label)
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setMinimumHeight(44)

            button.clicked.connect(
                lambda checked=False, index=page_index:
                self.show_page(index)
            )

            sidebar_layout.addWidget(button)
            self.nav_buttons.append(button)

        sidebar_layout.addStretch()

        footer = QLabel("OM Silver")
        footer.setObjectName("sidebarFooter")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(footer)

        # ---------------- MAIN CONTENT ----------------

        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")

        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(self.pages)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content_frame, 1)

        self.setCentralWidget(central_widget)

        # ---------------- APPLICATION STYLING ----------------

        self.setStyleSheet("""
            /* Overall application */

            QMainWindow,
            QWidget#centralWidget,
            QFrame#contentFrame,
            QStackedWidget#pageStack {
                background-color: #F6F5F3;
                color: #302B2A;
            }

            QWidget {
                color: #302B2A;
            }

            /* Sidebar */

            QFrame#sidebar {
                background-color: #FFFFFF;
                border-right: 1px solid #E7E3E0;
            }

            QLabel#appTitle {
                background-color: transparent;
                color: #702C3B;
                font-size: 24px;
                font-weight: 700;
                letter-spacing: 2px;
            }

            QLabel#appSubtitle {
                background-color: transparent;
                color: #88817F;
                font-size: 11px;
            }

            QLabel#sectionLabel {
                background-color: transparent;
                color: #918987;
                font-size: 10px;
                font-weight: 700;
                padding-left: 8px;
                letter-spacing: 1px;
            }

            QLabel#sidebarFooter {
                background-color: transparent;
                color: #918987;
                font-size: 11px;
                padding: 8px;
            }

            QPushButton#navButton {
                background-color: transparent;
                color: #514A48;
                border: none;
                border-radius: 7px;
                padding: 10px 14px;
                text-align: left;
                font-size: 14px;
            }

            QPushButton#navButton:hover {
                background-color: #F5EEEE;
            }

            QPushButton#navButton:checked {
                background-color: #702C3B;
                color: #FFFFFF;
                font-weight: 600;
            }

            /* General buttons */

            QPushButton {
                background-color: #FFFFFF;
                color: #514A48;
                border: 1px solid #DDD6D2;
                border-radius: 6px;
                padding: 7px 12px;
                min-height: 18px;
            }

            QPushButton:hover {
                background-color: #F5EEEE;
                border-color: #C9A9AF;
            }

            QPushButton:pressed {
                background-color: #EDE1E3;
            }

            QPushButton:disabled {
                background-color: #F0EFED;
                color: #A8A19E;
                border-color: #E3E0DE;
            }

            /* Text inputs */

            QLineEdit,
            QPlainTextEdit,
            QTextEdit,
            QSpinBox,
            QDoubleSpinBox,
            QDateEdit,
            QDateTimeEdit,
            QTimeEdit,
            QComboBox {
                background-color: #FFFFFF;
                color: #302B2A;
                border: 1px solid #DCD6D2;
                border-radius: 5px;
                padding: 6px;
                selection-background-color: #702C3B;
                selection-color: #FFFFFF;
            }

            QLineEdit:focus,
            QPlainTextEdit:focus,
            QTextEdit:focus,
            QSpinBox:focus,
            QDoubleSpinBox:focus,
            QComboBox:focus {
                border: 1px solid #9B6571;
            }

            QLineEdit:disabled,
            QPlainTextEdit:disabled,
            QTextEdit:disabled,
            QSpinBox:disabled,
            QDoubleSpinBox:disabled,
            QComboBox:disabled {
                background-color: #F0EFED;
                color: #8B8582;
            }

            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                color: #302B2A;
                selection-background-color: #F0E4E6;
                selection-color: #302B2A;
                border: 1px solid #DCD6D2;
                outline: none;
            }

            /* Tables */

            QTableWidget,
            QTableView,
            QTreeWidget,
            QTreeView,
            QListWidget,
            QListView {
                background-color: #FFFFFF;
                alternate-background-color: #FAF8F7;
                color: #302B2A;
                border: 1px solid #E3DEDA;
                gridline-color: #ECE7E4;
                selection-background-color: #F0E4E6;
                selection-color: #302B2A;
                outline: none;
            }

            QTableWidget::item,
            QTableView::item,
            QTreeWidget::item,
            QListWidget::item {
                background-color: transparent;
                color: #302B2A;
                padding: 5px;
            }

            QTableWidget::item:selected,
            QTableView::item:selected,
            QTreeWidget::item:selected,
            QListWidget::item:selected {
                background-color: #F0E4E6;
                color: #302B2A;
            }

            QHeaderView::section {
                background-color: #F2EFED;
                color: #514A48;
                border: none;
                border-bottom: 1px solid #E3DEDA;
                padding: 9px 7px;
                font-weight: 600;
            }

            /* Dialogs and message boxes */

            QDialog,
            QMessageBox {
                background-color: #F6F5F3;
                color: #302B2A;
            }

            QDialog QWidget,
            QMessageBox QLabel {
                color: #302B2A;
            }

            /* Group boxes and scroll areas */

            QGroupBox {
                background-color: #FFFFFF;
                color: #302B2A;
                border: 1px solid #E3DEDA;
                border-radius: 7px;
                margin-top: 12px;
                padding: 10px;
                font-weight: 600;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                background-color: #F6F5F3;
                color: #514A48;
            }

            QScrollArea {
                background-color: #F6F5F3;
                border: none;
            }

            QScrollArea QWidget {
                background-color: transparent;
            }

            /* Scrollbars */

            QScrollBar:vertical {
                background-color: #F0EEEC;
                width: 10px;
                margin: 0;
                border: none;
            }

            QScrollBar::handle:vertical {
                background-color: #C9C1BD;
                min-height: 25px;
                border-radius: 4px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #AFA5A0;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
            }

            QScrollBar:horizontal {
                background-color: #F0EEEC;
                height: 10px;
                margin: 0;
                border: none;
            }

            QScrollBar::handle:horizontal {
                background-color: #C9C1BD;
                min-width: 25px;
                border-radius: 4px;
            }

            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                width: 0;
            }

            /* Separators and tabs */

            QFrame[frameShape="4"],
            QFrame[frameShape="5"] {
                color: #E3DEDA;
            }

            QTabWidget::pane {
                background-color: #FFFFFF;
                border: 1px solid #E3DEDA;
            }

            QTabBar::tab {
                background-color: #EEEAE7;
                color: #514A48;
                padding: 8px 14px;
                border: 1px solid #E3DEDA;
            }

            QTabBar::tab:selected {
                background-color: #FFFFFF;
                color: #702C3B;
            }

            QToolTip {
                background-color: #FFFFFF;
                color: #302B2A;
                border: 1px solid #DCD6D2;
                padding: 5px;
            }
        """)

        # Open Directory by default
        self.show_page(0)

    def show_page(self, index):
        self.pages.setCurrentIndex(index)

        for button_index, button in enumerate(self.nav_buttons):
            button.setChecked(button_index == index)

        # Refresh page data when switching to a page.
        current_page = self.pages.widget(index)

        if hasattr(current_page, "refresh_items"):
            current_page.refresh_items()

        if hasattr(current_page, "refresh_transactions"):
            current_page.refresh_transactions()

        if hasattr(current_page, "load_accounts"):
            current_page.load_accounts()


if __name__ == "__main__":
    # Set a light palette before constructing the pages.
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(
        QPalette.ColorRole.Window, QColor("#F6F5F3")
    )
    palette.setColor(
        QPalette.ColorRole.WindowText, QColor("#302B2A")
    )
    palette.setColor(
        QPalette.ColorRole.Base, QColor("#FFFFFF")
    )
    palette.setColor(
        QPalette.ColorRole.AlternateBase, QColor("#FAF8F7")
    )
    palette.setColor(
        QPalette.ColorRole.Text, QColor("#302B2A")
    )
    palette.setColor(
        QPalette.ColorRole.Button, QColor("#FFFFFF")
    )
    palette.setColor(
        QPalette.ColorRole.ButtonText, QColor("#302B2A")
    )
    palette.setColor(
        QPalette.ColorRole.Highlight, QColor("#702C3B")
    )
    palette.setColor(
        QPalette.ColorRole.HighlightedText, QColor("#FFFFFF")
    )
    palette.setColor(
        QPalette.ColorRole.ToolTipBase, QColor("#FFFFFF")
    )
    palette.setColor(
        QPalette.ColorRole.ToolTipText, QColor("#302B2A")
    )
    app.setPalette(palette)

    init_db()

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
