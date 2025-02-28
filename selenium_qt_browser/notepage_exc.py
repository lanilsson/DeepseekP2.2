"""
NotePageExc Module - Implements spreadsheet functionality

This module contains the NotePageExc class which provides a UI for
creating and editing spreadsheet-like data.
"""

from selenium_qt_browser.tab_types import TabType
from PyQt6.QtCore import Qt, QTimer, QAbstractTableModel, QModelIndex
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, 
    QPushButton, QToolBar, QLabel, QComboBox,
    QSpinBox, QHeaderView, QMenu, QInputDialog,
    QLineEdit, QFileDialog, QMessageBox
)
from PyQt6.QtGui import (
    QFont, QColor, QAction, QKeySequence
)

class SpreadsheetModel(QAbstractTableModel):
    """Model for the spreadsheet data."""
    
    def __init__(self, rows=100, cols=26, parent=None):
        super().__init__(parent)
        self.rows = rows
        self.cols = cols
        self.data = {}  # Dictionary to store cell data: {(row, col): value}
        
    def rowCount(self, parent=QModelIndex()):
        return self.rows
    
    def columnCount(self, parent=QModelIndex()):
        return self.cols
    
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        
        row, col = index.row(), index.column()
        
        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            return self.data.get((row, col), "")
        
        return None
    
    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if not index.isValid():
            return False
        
        row, col = index.row(), index.column()
        
        if role == Qt.ItemDataRole.EditRole:
            # Store the value
            self.data[(row, col)] = value
            self.dataChanged.emit(index, index)
            return True
        
        return False
    
    def flags(self, index):
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable
    
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                # Use Excel-like column headers (A, B, C, ...)
                return chr(65 + section) if section < 26 else chr(64 + section // 26) + chr(65 + section % 26)
            else:
                # Row numbers (1, 2, 3, ...)
                return str(section + 1)
        
        return None
    
    def insertRow(self, position, parent=QModelIndex()):
        self.beginInsertRows(parent, position, position)
        self.rows += 1
        
        # Shift data down
        new_data = {}
        for (row, col), value in self.data.items():
            if row >= position:
                new_data[(row + 1, col)] = value
            else:
                new_data[(row, col)] = value
        
        self.data = new_data
        self.endInsertRows()
        return True
    
    def insertColumn(self, position, parent=QModelIndex()):
        self.beginInsertColumns(parent, position, position)
        self.cols += 1
        
        # Shift data right
        new_data = {}
        for (row, col), value in self.data.items():
            if col >= position:
                new_data[(row, col + 1)] = value
            else:
                new_data[(row, col)] = value
        
        self.data = new_data
        self.endInsertColumns()
        return True
    
    def removeRow(self, position, parent=QModelIndex()):
        if self.rows <= 1:
            return False
        
        self.beginRemoveRows(parent, position, position)
        self.rows -= 1
        
        # Remove data in the row and shift up
        new_data = {}
        for (row, col), value in self.data.items():
            if row == position:
                continue  # Skip this row
            elif row > position:
                new_data[(row - 1, col)] = value
            else:
                new_data[(row, col)] = value
        
        self.data = new_data
        self.endRemoveRows()
        return True
    
    def removeColumn(self, position, parent=QModelIndex()):
        if self.cols <= 1:
            return False
        
        self.beginRemoveColumns(parent, position, position)
        self.cols -= 1
        
        # Remove data in the column and shift left
        new_data = {}
        for (row, col), value in self.data.items():
            if col == position:
                continue  # Skip this column
            elif col > position:
                new_data[(row, col - 1)] = value
            else:
                new_data[(row, col)] = value
        
        self.data = new_data
        self.endRemoveColumns()
        return True
    
    def clear(self):
        self.beginResetModel()
        self.data = {}
        self.endResetModel()


class NotePageExc(QWidget):
    """A tab for creating and editing spreadsheet-like data."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.tab_type = TabType.NOTEPAGE_EXC
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the spreadsheet UI."""
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create toolbar
        self.create_toolbar()
        main_layout.addWidget(self.toolbar)
        
        # Create spreadsheet view
        self.spreadsheet_model = SpreadsheetModel()
        self.spreadsheet_view = QTableView()
        self.spreadsheet_view.setModel(self.spreadsheet_model)
        
        # Configure the view
        self.spreadsheet_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.spreadsheet_view.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.spreadsheet_view.setAlternatingRowColors(True)
        self.spreadsheet_view.setStyleSheet("""
            QTableView {
                background-color: #1e1e1e;
                color: #f0f0f0;
                gridline-color: #3a3a3a;
                border: 1px solid #333333;
                border-radius: 6px;
                selection-background-color: #2a5caa;
                selection-color: #ffffff;
                alternate-background-color: #262626;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #f0f0f0;
                padding: 4px;
                border: 1px solid #3a3a3a;
            }
        """)
        
        # Add spreadsheet view to main layout
        main_layout.addWidget(self.spreadsheet_view)
        
        # Add status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("""
            color: #64FFDA;
            font-size: 10px;
        """)
        status_layout.addWidget(self.status_label)
        
        # Add cell info
        self.cell_info_label = QLabel("Cell: -")
        self.cell_info_label.setStyleSheet("""
            color: #64FFDA;
            font-size: 10px;
        """)
        self.cell_info_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        status_layout.addWidget(self.cell_info_label)
        
        main_layout.addLayout(status_layout)
        
        # Connect signals
        self.spreadsheet_view.selectionModel().selectionChanged.connect(self.update_cell_info)
        
        # Set up context menu
        self.spreadsheet_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.spreadsheet_view.customContextMenuRequested.connect(self.show_context_menu)
    
    def create_toolbar(self):
        """Create the toolbar with spreadsheet actions."""
        self.toolbar = QToolBar("Spreadsheet Tools")
        self.toolbar.setStyleSheet("""
            background-color: #2d2d2d;
            border: 1px solid #333333;
            border-radius: 4px;
            padding: 2px;
            spacing: 2px;
        """)
        
        # Add row
        self.add_row_action = QAction("Add Row", self)
        self.add_row_action.triggered.connect(self.add_row)
        self.toolbar.addAction(self.add_row_action)
        
        # Add column
        self.add_column_action = QAction("Add Column", self)
        self.add_column_action.triggered.connect(self.add_column)
        self.toolbar.addAction(self.add_column_action)
        
        self.toolbar.addSeparator()
        
        # Remove row
        self.remove_row_action = QAction("Remove Row", self)
        self.remove_row_action.triggered.connect(self.remove_row)
        self.toolbar.addAction(self.remove_row_action)
        
        # Remove column
        self.remove_column_action = QAction("Remove Column", self)
        self.remove_column_action.triggered.connect(self.remove_column)
        self.toolbar.addAction(self.remove_column_action)
        
        self.toolbar.addSeparator()
        
        # Clear all
        self.clear_action = QAction("Clear All", self)
        self.clear_action.triggered.connect(self.clear_spreadsheet)
        self.toolbar.addAction(self.clear_action)
        
        self.toolbar.addSeparator()
        
        # Cell formatting (placeholder for future enhancement)
        self.format_action = QAction("Format Cell", self)
        self.format_action.triggered.connect(self.format_cell)
        self.toolbar.addAction(self.format_action)
    
    def add_row(self):
        """Add a new row to the spreadsheet."""
        selected_indexes = self.spreadsheet_view.selectionModel().selectedIndexes()
        if selected_indexes:
            row = selected_indexes[0].row() + 1
        else:
            row = self.spreadsheet_model.rowCount()
        
        self.spreadsheet_model.insertRow(row)
        self.status_label.setText(f"Row {row + 1} added")
    
    def add_column(self):
        """Add a new column to the spreadsheet."""
        selected_indexes = self.spreadsheet_view.selectionModel().selectedIndexes()
        if selected_indexes:
            column = selected_indexes[0].column() + 1
        else:
            column = self.spreadsheet_model.columnCount()
        
        self.spreadsheet_model.insertColumn(column)
        col_name = chr(65 + column) if column < 26 else chr(64 + column // 26) + chr(65 + column % 26)
        self.status_label.setText(f"Column {col_name} added")
    
    def remove_row(self):
        """Remove the selected row from the spreadsheet."""
        selected_indexes = self.spreadsheet_view.selectionModel().selectedIndexes()
        if selected_indexes:
            row = selected_indexes[0].row()
            if self.spreadsheet_model.removeRow(row):
                self.status_label.setText(f"Row {row + 1} removed")
            else:
                self.status_label.setText("Cannot remove the last row")
        else:
            self.status_label.setText("No row selected")
    
    def remove_column(self):
        """Remove the selected column from the spreadsheet."""
        selected_indexes = self.spreadsheet_view.selectionModel().selectedIndexes()
        if selected_indexes:
            column = selected_indexes[0].column()
            if self.spreadsheet_model.removeColumn(column):
                col_name = chr(65 + column) if column < 26 else chr(64 + column // 26) + chr(65 + column % 26)
                self.status_label.setText(f"Column {col_name} removed")
            else:
                self.status_label.setText("Cannot remove the last column")
        else:
            self.status_label.setText("No column selected")
    
    def clear_spreadsheet(self):
        """Clear all data from the spreadsheet."""
        self.spreadsheet_model.clear()
        self.status_label.setText("Spreadsheet cleared")
    
    def format_cell(self):
        """Format the selected cell (placeholder for future enhancement)."""
        selected_indexes = self.spreadsheet_view.selectionModel().selectedIndexes()
        if selected_indexes:
            self.status_label.setText("Cell formatting not implemented yet")
        else:
            self.status_label.setText("No cell selected")
    
    def update_cell_info(self, selected, deselected):
        """Update the cell info display."""
        selected_indexes = self.spreadsheet_view.selectionModel().selectedIndexes()
        if selected_indexes:
            row = selected_indexes[0].row()
            column = selected_indexes[0].column()
            col_name = chr(65 + column) if column < 26 else chr(64 + column // 26) + chr(65 + column % 26)
            self.cell_info_label.setText(f"Cell: {col_name}{row + 1}")
        else:
            self.cell_info_label.setText("Cell: -")
    
    def show_context_menu(self, position):
        """Show context menu for the spreadsheet."""
        menu = QMenu(self)
        
        # Add actions
        menu.addAction(self.add_row_action)
        menu.addAction(self.add_column_action)
        menu.addSeparator()
        menu.addAction(self.remove_row_action)
        menu.addAction(self.remove_column_action)
        menu.addSeparator()
        menu.addAction(self.clear_action)
        menu.addSeparator()
        menu.addAction(self.format_action)
        
        # Show the menu
        menu.exec(self.spreadsheet_view.mapToGlobal(position))