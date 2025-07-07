import sys
import os
import json
import threading
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QFileDialog, QComboBox, QTextEdit, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QSizePolicy, QMenu
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor, QFontDatabase, QFont, QIcon
from sorter import scan_and_sort
from undo_sort import undo_moves

CONFIG_DIR = "configs"
DEFAULT_CONFIG_NAME = "default"
DEFAULT_CONFIG_PATH = os.path.join(CONFIG_DIR, f"{DEFAULT_CONFIG_NAME}.json")

DEFAULT_RULES = {
    ".pdf": {"folder": "PDFs", "subfolder": "year"},
    ".jpg": {"folder": "Images", "subfolder": "year"},
    ".jpeg": {"folder": "Images", "subfolder": "year"},
    ".png": {"folder": "Images", "subfolder": "year"},
    ".docx": {"folder": "TextFiles", "subfolder": "year"},
    ".txt": {"folder": "TextFiles", "subfolder": None},
    ".mp3": {"folder": "Audio", "subfolder": "musictype"},
    ".url": {"folder": "Internet Shortcuts", "subfolder": None},
    ".exe": {"folder": "Installers", "subfolder": None},
    ".msi": {"folder": "Installers", "subfolder": None},
    ".lnk": {"folder": "Shortcuts", "subfolder": None}
}

class FileSorterGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sortly")
        self.setWindowIcon(QIcon("icons/icon.ico"))
        self.resize(1300, 1100)
        self.setMinimumSize(900, 500)

        font_id = QFontDatabase.addApplicationFont("Oswald-Regular.ttf")
        families = QFontDatabase.applicationFontFamilies(font_id)
        if families:
            self.setFont(QFont(families[0], 10))
        else:
            print("⚠️ Oswald font not found. Falling back to default.")
            self.setFont(QFont("Arial", 10))

        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: Oswald;
            }
            QHeaderView::section {
                background-color: #333;
                color: white;
                padding: 4px;
                border: 1px solid #444;
            }
            QTableWidget {
                background-color: #2a2a2a;
                color: white;
                gridline-color: #444;
            }
            QTableWidget QTableCornerButton::section {
                background-color: #333;
                border: 1px solid #444;
            }
            QComboBox {
                background-color: #2a2a2a;
                color: white;
            }
            QComboBox QAbstractItemView {
                background-color: #2a2a2a;
                color: white;
                selection-background-color: #3b82f6;
                selection-color: black;
            }
            QPushButton {
                background-color: #3b82f6;
                color: white;
                padding: 6px 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QLineEdit, QTextEdit {
                background-color: #2a2a2a;
                color: white;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 4px;
            }
            QLabel {
                font-weight: bold;
                color: white;
            }
                           
            QMenu {
                background-color: #2a2a2a;
                color: white;
                border: 1px solid #444;
                padding: 5px;
            }

            QMenu::item {
                padding: 6px 20px;
                background-color: transparent;
            }

            QMenu::item:selected {
                background-color: #FFFFFF; 
                color: black; 
            }                         
            
        """
        )

        self.sort_config = DEFAULT_RULES.copy()
        self.current_config_name = DEFAULT_CONFIG_NAME
        os.makedirs(CONFIG_DIR, exist_ok=True)

        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        sidebar = QVBoxLayout()
        rule_label = QLabel("Sorting Rules:")
        sidebar.addWidget(rule_label)

        self.table = QTableWidget(0, 3)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_table_context_menu)
        self.table.setHorizontalHeaderLabels(["File Extension", "Folder Name", "Subfolder Rule"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        sidebar.addWidget(self.table)

        config_btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Rule")
        add_btn.clicked.connect(self.add_rule_row)
        delete_btn = QPushButton("Delete Rule")
        delete_btn.clicked.connect(self.delete_selected_rule)
        save_btn = QPushButton("Save Config")
        save_btn.clicked.connect(self.save_current_config)
        reset_btn = QPushButton("Reset Default")
        reset_btn.clicked.connect(self.reset_to_default)
        config_btn_layout.addWidget(add_btn)
        config_btn_layout.addWidget(delete_btn)
        config_btn_layout.addWidget(save_btn)
        config_btn_layout.addWidget(reset_btn)
        sidebar.addLayout(config_btn_layout)

        self.config_selector = QComboBox()
        self.config_selector.currentTextChanged.connect(self.load_selected_config)
        sidebar.addWidget(QLabel("Configuration:"))
        sidebar.addWidget(self.config_selector)

        self.new_config_input = QLineEdit()
        self.new_config_input.setPlaceholderText("New config name")
        create_btn = QPushButton("Create Config")
        create_btn.clicked.connect(self.create_new_config)
        delete_config_btn = QPushButton("Delete Config")
        delete_config_btn.clicked.connect(self.delete_config)
        sidebar.addWidget(QLabel("Create New Config:"))
        sidebar.addWidget(self.new_config_input)
        sidebar.addWidget(create_btn)
        sidebar.addWidget(delete_config_btn)

        self.load_available_configs()

        main_area = QVBoxLayout()

        behavior_layout = QHBoxLayout()
        self.behavior_combo = QComboBox()
        self.behavior_combo.addItems([
            "Leave pre-existing folders alone",
            "Sort contents of pre-existing folders",
            "Move pre-existing folders to archive"
        ])
        behavior_layout.addWidget(QLabel("When encountering pre-existing folders:"))
        behavior_layout.addWidget(self.behavior_combo)
        main_area.addLayout(behavior_layout)

        folder_layout = QHBoxLayout()
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Select a folder to sort...")
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_folder)
        folder_layout.addWidget(self.folder_input)
        folder_layout.addWidget(browse_btn)
        main_area.addLayout(folder_layout)

        btn_layout = QHBoxLayout()
        sort_btn = QPushButton("Sort Files")
        sort_btn.clicked.connect(self.sort_files)
        undo_btn = QPushButton("Undo Last Sort")
        undo_btn.clicked.connect(self.undo_sort)
        btn_layout.addWidget(sort_btn)
        btn_layout.addWidget(undo_btn)
        main_area.addLayout(btn_layout)

        main_area.addWidget(QLabel("Log Output:"))
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        main_area.addWidget(self.log_output)

        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar)
        sidebar_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        main_layout.addWidget(sidebar_widget)

        main_widget = QWidget()
        main_widget.setLayout(main_area)
        main_layout.addWidget(main_widget)

        self.populate_table()

    def show_table_context_menu(self, pos):
        selected_rows = set(index.row() for index in self.table.selectedIndexes())
        if not selected_rows:
            return

        menu = QMenu(self)

        delete_icon = QIcon("icons/delete.svg")
        duplicate_icon = QIcon("icons/duplicate.svg")

        delete_action = menu.addAction(delete_icon, "Delete Rule(s)")
        duplicate_action = menu.addAction(duplicate_icon, "Duplicate Rule(s)")

        action = menu.exec_(self.table.viewport().mapToGlobal(pos))

        if action == delete_action:
            for row in sorted(selected_rows, reverse=True):
                ext_item = self.table.item(row, 0)
                if ext_item:
                    ext = ext_item.text().strip().lower()
                    if ext in self.sort_config:
                        del self.sort_config[ext]
                self.table.removeRow(row)

        elif action == duplicate_action:
            for row in sorted(selected_rows):
                ext_item = self.table.item(row, 0)
                folder_item = self.table.item(row, 1)
                subfolder_widget = self.table.cellWidget(row, 2)

                if ext_item and folder_item:
                    ext = ext_item.text().strip().lower()
                    folder = folder_item.text().strip()
                    subfolder = subfolder_widget.currentText() if subfolder_widget else "None"

                    new_row = self.table.rowCount()
                    self.table.insertRow(new_row)
                    self.table.setItem(new_row, 0, QTableWidgetItem(ext))
                    self.table.setItem(new_row, 1, QTableWidgetItem(folder))
                    new_subfolder_combo = QComboBox()
                    new_subfolder_combo.addItems(["None", "Year", "MusicType"])
                    new_subfolder_combo.setCurrentText(subfolder)
                    new_subfolder_combo.setFocusPolicy(Qt.NoFocus)
                    new_subfolder_combo.installEventFilter(self)
                    self.table.setCellWidget(new_row, 2, new_subfolder_combo)

    
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folder_input.setText(folder)

    def add_rule_row(self):
        row_pos = self.table.rowCount()
        self.table.insertRow(row_pos)
        self.table.setItem(row_pos, 0, QTableWidgetItem(".ext"))
        self.table.setItem(row_pos, 1, QTableWidgetItem("FolderName"))
        subfolder_combo = QComboBox()
        subfolder_combo.addItems(["None", "Year", "MusicType"])
        subfolder_combo.setFocusPolicy(Qt.NoFocus)
        subfolder_combo.installEventFilter(self)
        self.table.setCellWidget(row_pos, 2, subfolder_combo)

    def eventFilter(self, source, event):
        if event.type() == event.Wheel and isinstance(source, QComboBox):
            return True
        return super().eventFilter(source, event)

    def delete_selected_rule(self):
        selected = self.table.currentRow()
        if selected >= 0:
            ext = self.table.item(selected, 0).text().strip().lower()
            if ext in self.sort_config:
                del self.sort_config[ext]
            self.table.removeRow(selected)

    def save_current_config(self):
        config_name = self.config_selector.currentText()
        config = {}
        for row in range(self.table.rowCount()):
            ext_item = self.table.item(row, 0)
            folder_item = self.table.item(row, 1)
            subfolder_widget = self.table.cellWidget(row, 2)
            if not ext_item or not folder_item:
                continue
            ext = ext_item.text().strip().lower()
            folder = folder_item.text().strip()
            subfolder = subfolder_widget.currentText().lower() if subfolder_widget else None
            config[ext] = {"folder": folder, "subfolder": subfolder if subfolder != "none" else None}

        path = os.path.join(CONFIG_DIR, f"{config_name}.json")
        with open(path, "w") as f:
            json.dump(config, f, indent=2)
        self.log(f"Saved config: {config_name}")
        self.sort_config = config

    def load_selected_config(self, name):
        path = os.path.join(CONFIG_DIR, f"{name}.json")
        if not os.path.exists(path):
            self.sort_config = DEFAULT_RULES.copy()
        else:
            with open(path, "r") as f:
                self.sort_config = json.load(f)
        self.populate_table()
        self.current_config_name = name
        if hasattr(self, 'log_output'):
            self.log(f"Loaded config: {name}")

    def create_new_config(self):
        name = self.new_config_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Invalid Name", "Please enter a name for the new config.")
            return
        path = os.path.join(CONFIG_DIR, f"{name}.json")
        if os.path.exists(path):
            QMessageBox.warning(self, "Exists", "A config with this name already exists.")
            return
        with open(path, "w") as f:
            json.dump(DEFAULT_RULES, f, indent=2)
        self.config_selector.addItem(name)
        self.config_selector.setCurrentText(name)
        self.new_config_input.clear()
        self.log(f"Created new config: {name}")

    def delete_config(self):
        name = self.config_selector.currentText()
        if name == DEFAULT_CONFIG_NAME:
            QMessageBox.warning(self, "Cannot Delete", "Cannot delete the default configuration.")
            return
        path = os.path.join(CONFIG_DIR, f"{name}.json")
        if os.path.exists(path):
            os.remove(path)
        self.load_available_configs()
        self.config_selector.setCurrentText(DEFAULT_CONFIG_NAME)
        self.log(f"Deleted config: {name}")

    def load_available_configs(self):
        self.config_selector.clear()
        for filename in os.listdir(CONFIG_DIR):
            if filename.endswith(".json"):
                name = filename[:-5]
                self.config_selector.addItem(name)

    def reset_to_default(self):
        self.sort_config = DEFAULT_RULES.copy()
        self.populate_table()
        self.log("Reset to default rules.")

    def populate_table(self):
        self.table.setRowCount(0)
        for ext, rule in self.sort_config.items():
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)
            self.table.setItem(row_pos, 0, QTableWidgetItem(ext))
            self.table.setItem(row_pos, 1, QTableWidgetItem(rule.get("folder", "")))
            subfolder_combo = QComboBox()
            subfolder_combo.addItems(["None", "Year"])
            if ext == ".mp3":
                subfolder_combo.addItem("MusicType")
            current = rule.get("subfolder", "none")
            subfolder_combo.setCurrentText(current.capitalize() if current else "None")
            subfolder_combo.setFocusPolicy(Qt.NoFocus)
            subfolder_combo.installEventFilter(self)
            self.table.setCellWidget(row_pos, 2, subfolder_combo)

    def sort_files(self):
        folder = self.folder_input.text().strip()
        if not folder or not os.path.isdir(folder):
            QMessageBox.critical(self, "Error", "Please select a valid folder.")
            return
        self.save_current_config()
        self.log("Sorting started...")
        behavior = self.behavior_combo.currentText()
        threading.Thread(target=self._sort_thread, args=(folder, behavior), daemon=True).start()

    def _sort_thread(self, folder, behavior):
        summary = scan_and_sort(folder, self.sort_config, behavior)
        self.log("Sorting complete.")
        self.log("\n--- Summary ---")
        for k, v in summary.items():
            self.log(f"{k}: {v}")

    def undo_sort(self):
        self.log("Undo started...")
        threading.Thread(target=self._undo_thread, daemon=True).start()

    def _undo_thread(self):
        undo_moves()
        self.log("Undo complete.")

    def log(self, message):
        self.log_output.append(message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = FileSorterGUI()
    gui.show()
    sys.exit(app.exec_())
