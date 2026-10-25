"""

Contains the reusable components for the UI
Contains Dialog boxes, buttons, and page ui common accross the app

"""


from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


# ============================================================
# DESIGN COLOURS
# Change these values to customise the application's theme.
# ============================================================

COLOR = "#7B2944"
COLOR_HOVER = "#652138"
COLOR_LIGHT = "#F5E9EE"

BACKGROUND_COLOR = "#F7F7F9"
SURFACE_COLOR = "#FFFFFF"
BORDER_COLOR = "#E3DEE2"

TEXT_COLOR = "#29252A"
TEXT_SECONDARY_COLOR = "#777078"
TEXT_ON_COLOR = "#FFFFFF"


# ============================================================
# LAYOUT SETTINGS
# ============================================================

PAGE_PADDING = 28
COMPONENT_SPACING = 12


# ============================================================
# REUSABLE DIALOG
# Used for forms such as Add Customer and Edit Vendor.
# ============================================================

class AppDialog(QDialog):

    def __init__(
        self,
        title="Dialog",
        parent=None,
        min_width=460,
        min_height=260,
        primary_text="Save",
        cancel_text="Cancel",
        show_footer=True,
    ):
        super().__init__(parent)

        self.setWindowTitle(title)
        self.setMinimumSize(min_width, min_height)
        self.setModal(True)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {SURFACE_COLOR};
                color: {TEXT_COLOR};
            }}

            QLabel#dialogTitle {{
                color: {TEXT_COLOR};
                font-size: 20px;
                font-weight: 600;
            }}

            QPushButton {{
                padding: 0 16px;
                border-radius: 6px;
                font-size: 13px;
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 22, 24, 20)
        main_layout.setSpacing(COMPONENT_SPACING)

        # Dialog heading
        self.title_label = QLabel(title)
        self.title_label.setObjectName("dialogTitle")
        main_layout.addWidget(self.title_label)

        # Main content area
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(COMPONENT_SPACING)
        main_layout.addLayout(self.content_layout, 1)

        # Footer buttons
        self.footer_layout = QHBoxLayout()
        self.footer_layout.setSpacing(10)
        self.footer_layout.addStretch()

        self.cancel_button = QPushButton(cancel_text)
        self.cancel_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.cancel_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {SURFACE_COLOR};
                color: {TEXT_COLOR};
                border: 1px solid {BORDER_COLOR};
            }}

            QPushButton:hover {{
                background-color: {BACKGROUND_COLOR};
            }}

            QPushButton:pressed {{
                background-color: {COLOR_LIGHT};
            }}
        """)
        self.cancel_button.clicked.connect(self.reject)

        self.primary_button = QPushButton(primary_text)
        self.primary_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.primary_button.setDefault(True)
        self.primary_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR};
                color: {TEXT_ON_COLOR};
                border: 1px solid {COLOR};
            }}

            QPushButton:hover {{
                background-color: {COLOR_HOVER};
                border-color: {COLOR_HOVER};
            }}

            QPushButton:pressed {{
                background-color: {COLOR_HOVER};
            }}
        """)
        self.primary_button.clicked.connect(self.accept)

        self.footer_layout.addWidget(self.cancel_button)
        self.footer_layout.addWidget(self.primary_button)

        if show_footer:
            main_layout.addLayout(self.footer_layout)

    def add_content(self, widget):
        """Add a widget to the dialog's main content area."""
        self.content_layout.addWidget(widget)

    def showEvent(self, event):
        """Centre the dialog over its parent or the screen."""
        super().showEvent(event)

        parent = self.parentWidget()

        if parent is not None:
            parent_rect = parent.frameGeometry()
            dialog_rect = self.frameGeometry()

            dialog_rect.moveCenter(parent_rect.center())
            self.move(dialog_rect.topLeft())

        else:
            screen = QApplication.primaryScreen()

            if screen is not None:
                screen_rect = screen.availableGeometry()
                dialog_rect = self.frameGeometry()

                dialog_rect.moveCenter(screen_rect.center())
                self.move(dialog_rect.topLeft())


# ============================================================
# REUSABLE ADD BUTTON
# Used for actions such as Add Customer or Add Item.
# ============================================================

class AddButton(QPushButton):

    def __init__(self, text="Add", parent=None):
        super().__init__(text, parent)

        self.setMinimumHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR};
                color: {TEXT_ON_COLOR};
                border: 1px solid {COLOR};
                border-radius: 6px;
                padding: 0 18px;
                font-size: 13px;
                font-weight: 600;
            }}

            QPushButton:hover {{
                background-color: {COLOR_HOVER};
                border-color: {COLOR_HOVER};
            }}

            QPushButton:pressed {{
                background-color: {COLOR_HOVER};
            }}

            QPushButton:disabled {{
                background-color: {BORDER_COLOR};
                color: {TEXT_SECONDARY_COLOR};
                border-color: {BORDER_COLOR};
            }}
        """)


# ============================================================
# REUSABLE NAVIGATION BUTTON
# Used in the application's sidebar.
# ============================================================

class NavigationButton(QPushButton):

    def __init__(self, text, parent=None):
        super().__init__(text, parent)

        self.setCheckable(True)
        self.setMinimumHeight(42)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {TEXT_COLOR};
                border: none;
                border-left: 3px solid transparent;
                border-radius: 5px;
                padding: 0 14px;
                text-align: left;
                font-size: 13px;
            }}

            QPushButton:hover {{
                background-color: {COLOR_LIGHT};
                color: {COLOR};
            }}

            QPushButton:checked {{
                background-color: {COLOR_LIGHT};
                color: {COLOR};
                border-left: 3px solid {COLOR};
                font-weight: 600;
            }}

            QPushButton:focus {{
                outline: none;
            }}
        """)


# ============================================================
# REUSABLE BASE PAGE
# Used as the foundation for each main application page.
# ============================================================

class BasePage(QWidget):

    def __init__(
        self,
        title="Page Title",
        description="",
        parent=None,
    ):
        super().__init__(parent)

        self.setObjectName("basePage")

        self.setStyleSheet(f"""
            QWidget#basePage {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
            }}

            QLabel#pageTitle {{
                color: {TEXT_COLOR};
                font-size: 25px;
                font-weight: 600;
            }}

            QLabel#pageDescription {{
                color: {TEXT_SECONDARY_COLOR};
                font-size: 13px;
            }}

            QFrame#pageContent {{
                background-color: {SURFACE_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 10px;
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            PAGE_PADDING,
            PAGE_PADDING,
            PAGE_PADDING,
            PAGE_PADDING,
        )
        main_layout.setSpacing(22)

        # Page header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(20)

        heading_layout = QVBoxLayout()
        heading_layout.setSpacing(6)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("pageTitle")
        heading_layout.addWidget(self.title_label)

        self.description_label = QLabel(description)
        self.description_label.setObjectName("pageDescription")
        self.description_label.setWordWrap(True)

        if description:
            heading_layout.addWidget(self.description_label)
        else:
            self.description_label.hide()

        header_layout.addLayout(heading_layout, 1)

        # Space for page-specific action buttons
        self.actions_layout = QHBoxLayout()
        self.actions_layout.setSpacing(10)
        header_layout.addLayout(self.actions_layout)

        main_layout.addLayout(header_layout)

        # Main page content container
        self.content_frame = QFrame()
        self.content_frame.setObjectName("pageContent")

        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(COMPONENT_SPACING)

        main_layout.addWidget(self.content_frame, 1)

    def add_action(self, widget):
        """Add an action button to the page header."""
        self.actions_layout.addWidget(widget)

    def add_content(self, widget, stretch=0):
        """Add a widget to the page's content area."""
        self.content_layout.addWidget(widget, stretch)

    def set_page_title(self, title):
        """Update the page heading."""
        self.title_label.setText(title)

    def set_page_description(self, description):
        """Update the page description."""
        self.description_label.setText(description)
        self.description_label.setVisible(bool(description))
