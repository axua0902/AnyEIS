import os
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from setting import Settings
from themes import Themes
from widgets.py_push_button.py_push_button2 import PyPushButton2
from widgets.py_combobox.py_combobox2 import PyComboBox2
from widgets.py_label.py_label2 import PyLabel2


class Ui_RightColumn(object):
    def setupUi(self, RightColumn):
        if not RightColumn.objectName():
            RightColumn.setObjectName(u"RightColumn")
        RightColumn.resize(100, 600)

        self.settings = Settings()
        self.themes = Themes()

        self.main_pages_layout = QVBoxLayout(RightColumn)
        self.main_pages_layout.setSpacing(0)
        self.main_pages_layout.setObjectName(u"main_pages_layout")
        self.main_pages_layout.setContentsMargins(5, 5, 5, 5)

        self.top_settings = self.settings.get_top_settings()

        self.menus = QStackedWidget(RightColumn)
        self.menus.setObjectName(u"menus")

        self.menu_1 = QWidget()
        self.menu_1.setObjectName(u"menu_1")
        self.menu_1_layout = QVBoxLayout(self.menu_1)
        self.menu_1_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea(self.menu_1)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.scroll_widget = QWidget()
        self.scroll_widget.setObjectName(u"scroll_widget")
        self.main_layout = QVBoxLayout(self.scroll_widget)
        self.main_layout.setSpacing(10)
        self.main_layout.setObjectName(u"main_layout")
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        self.create_paths_section()
        self.create_export_image_section()
        self.create_user_preferences_section()

        self.main_layout.addStretch()

        self.scroll_area.setWidget(self.scroll_widget)
        self.menu_1_layout.addWidget(self.scroll_area)

        self.menus.addWidget(self.menu_1)
        self.main_pages_layout.addWidget(self.menus)

        self.retranslateUi(RightColumn)
        QMetaObject.connectSlotsByName(RightColumn)

    def create_paths_section(self):
        self.paths_group = QWidget()
        self.paths_group.setObjectName("paths_section")
        self.paths_group.setStyleSheet(f"""
            QWidget#paths_section {{
                background-color: {self.themes.items["app_color"]["bg_two"]};
                border-radius: 8px;
                border: 1px solid {self.themes.items["app_color"]["orange"]};
            }}
        """)
        self.paths_layout = QVBoxLayout(self.paths_group)
        self.paths_layout.setSpacing(8)
        self.paths_layout.setContentsMargins(10, 5, 10, 10)

        self.paths_title = PyLabel2(
            text="Data Paths",
            color=self.themes.items["app_color"]["text_title"],
            font_size=self.settings.items["font"]["text_size_small"],
            font_family=self.settings.items["font"]["family"],
            font_weight=700,
        )
        self.paths_title.setFixedHeight(35)
        self.paths_layout.addWidget(self.paths_title)

        self.input_data_widget, self.input_data_btn = self.create_path_row(
            "Input Data",
            self.top_settings.get("paths", {}).get("input_data", ""),
            self.on_input_data_clicked
        )
        self.paths_layout.addWidget(self.input_data_widget)

        self.reference_data_widget, self.reference_data_btn = self.create_path_row(
            "Reference Data",
            self.top_settings.get("paths", {}).get("reference_data", ""),
            self.on_reference_data_clicked
        )
        self.paths_layout.addWidget(self.reference_data_widget)

        self.results_data_widget, self.results_data_btn = self.create_path_row(
            "Results Data",
            self.top_settings.get("paths", {}).get("results_data", ""),
            self.on_results_data_clicked
        )
        self.paths_layout.addWidget(self.results_data_widget)

        self.restore_defaults_btn = PyPushButton2(
            text="Restore Default Paths",
            font_size=self.settings.items["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color=self.themes.items["app_color"]["white"],
            bg_color=self.themes.items["app_color"]["gray_primary"],
            bg_color_hover=self.themes.items["app_color"]["gray_hover"],
            bg_color_pressed=self.themes.items["app_color"]["gray_pressed"],
            border_color="transparent",
        )
        self.restore_defaults_btn.setFixedHeight(36)
        self.restore_defaults_btn.clicked.connect(self.on_restore_default_paths_clicked)
        self.paths_layout.addWidget(self.restore_defaults_btn)

        self.main_layout.addWidget(self.paths_group)

    def create_path_row(self, label_text, path_value, callback):
        widget = QWidget()
        widget.setFixedHeight(60)
        layout = QVBoxLayout(widget)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)

        label = PyLabel2(
            text=label_text,
            color=self.themes.items["app_color"]["text_title"],
            font_size=self.settings.items["font"]["text_size_utralsmall"],
            font_family=self.settings.items["font"]["family"],
            font_weight=600,
        )
        layout.addWidget(label)

        display_text = self._truncate_path(path_value) if path_value else "Click to set path..."
        path_btn = PyPushButton2(
            text=display_text,
            font_size=self.settings.items["font"]["text_size_utralsmall"],
            font_weight=600,
            radius=4,
            font_color=self.themes.items["app_color"]["text_foreground"],
            bg_color=self.themes.items["app_color"]["input_bg"],
            bg_color_hover=self.themes.items["app_color"]["light_three"],
            bg_color_pressed=self.themes.items["app_color"]["light_two"],
            border_color=self.themes.items["app_color"]["input_border"],
        )
        path_btn.setFixedHeight(32)
        path_btn.clicked.connect(callback)
        layout.addWidget(path_btn)

        return widget, path_btn

    def _truncate_path(self, path, max_length=30):
        """如果路径过长,只显示结尾部分(优先在路径分隔符处截断)"""
        if not path or len(path) <= max_length:
            return path
        truncated = path[-(max_length - 3):]
        sep_idx = max(truncated.find(os.sep), truncated.find("/"))
        if sep_idx >= 0:
            truncated = truncated[sep_idx:]
        return "..." + truncated

    def create_export_image_section(self):
        self.export_group = QWidget()
        self.export_group.setObjectName("export_section")
        self.export_group.setStyleSheet(f"""
            QWidget#export_section {{
                background-color: {self.themes.items["app_color"]["bg_two"]};
                border-radius: 8px;
                border: 1px solid {self.themes.items["app_color"]["blue"]};
            }}
        """)
        self.export_layout = QVBoxLayout(self.export_group)
        self.export_layout.setSpacing(10)
        self.export_layout.setContentsMargins(10, 5, 10, 10)

        self.export_title = PyLabel2(
            text="Export Image",
            color=self.themes.items["app_color"]["text_title"],
            font_size=self.settings.items["font"]["text_size_small"],
            font_family=self.settings.items["font"]["family"],
            font_weight=700,
        )
        self.export_title.setFixedHeight(35)
        self.export_layout.addWidget(self.export_title)

        format_layout = QHBoxLayout()
        format_layout.setSpacing(10)

        format_label = PyLabel2(
            text="Format:",
            color=self.themes.items["app_color"]["text_title"],
            font_family=self.settings.items["font"]["family"],
            font_size=self.settings.items["font"]["text_size_utralsmall"],
            font_weight=600,
        )
        format_layout.addWidget(format_label)

        self.format_combo = PyComboBox2(
            color=self.themes.items["app_color"]["text_foreground"],
            radius=4,
            font_size=self.settings.items["font"]["text_size_small"],
            font_weight=700,
            min_height=32,
            bg_color=self.themes.items["app_color"]["bg_two"],
            bg_color_hover=self.themes.items["app_color"]["light_three"],
            bg_color_pressed=self.themes.items["app_color"]["context_hover"],
            selection_color=self.themes.items["app_color"]["context_pressed"],
            border_color=self.themes.items["app_color"]["light_three"],
        )
        self.format_combo.addItems(["png", "jpg", "svg", "pdf"])
        current_format = self.top_settings.get("export_image", {}).get("format", "png")
        self.format_combo.setCurrentText(current_format)
        self.format_combo.currentTextChanged.connect(self.on_format_changed)
        format_layout.addWidget(self.format_combo, 1)
        self.export_layout.addLayout(format_layout)

        resolution_layout = QHBoxLayout()
        resolution_layout.setSpacing(10)

        resolution_label = PyLabel2(
            text="Resolution (DPI):",
            color=self.themes.items["app_color"]["text_title"],
            font_family=self.settings.items["font"]["family"],
            font_size=self.settings.items["font"]["text_size_utralsmall"],
            font_weight=600,
        )
        resolution_layout.addWidget(resolution_label)

        self.resolution_combo = PyComboBox2(
            color=self.themes.items["app_color"]["text_foreground"],
            radius=4,
            font_size=self.settings.items["font"]["text_size_small"],
            font_weight=700,
            min_height=32,
            bg_color=self.themes.items["app_color"]["bg_two"],
            bg_color_hover=self.themes.items["app_color"]["light_three"],
            bg_color_pressed=self.themes.items["app_color"]["context_hover"],
            selection_color=self.themes.items["app_color"]["context_pressed"],
            border_color=self.themes.items["app_color"]["light_three"],
        )
        self.resolution_combo.addItems(["100", "150", "300", "600"])
        current_resolution = str(self.top_settings.get("export_image", {}).get("resolution", 300))
        self.resolution_combo.setCurrentText(current_resolution)
        self.resolution_combo.currentTextChanged.connect(self.on_resolution_changed)
        resolution_layout.addWidget(self.resolution_combo)
        self.export_layout.addLayout(resolution_layout)

        self.main_layout.addWidget(self.export_group)

    def create_user_preferences_section(self):
        self.prefs_group = QWidget()
        self.prefs_group.setObjectName("prefs_section")
        self.prefs_group.setStyleSheet(f"""
            QWidget#prefs_section {{
                background-color: {self.themes.items["app_color"]["bg_two"]};
                border-radius: 8px;
                border: 1px solid {self.themes.items["app_color"]["green_primary"]};
            }}
        """)
        self.prefs_layout = QVBoxLayout(self.prefs_group)
        self.prefs_layout.setSpacing(10)
        self.prefs_layout.setContentsMargins(10, 5, 10, 10)

        self.prefs_title = PyLabel2(
            text="User Preferences",
            color=self.themes.items["app_color"]["text_title"],
            font_size=self.settings.items["font"]["text_size_small"],
            font_family=self.settings.items["font"]["family"],
            font_weight=700,
        )
        self.prefs_title.setFixedHeight(35)
        self.prefs_layout.addWidget(self.prefs_title)

        self.export_prefs_btn = PyPushButton2(
            text="Export Preferences",
            font_size=self.settings.items["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color=self.themes.items["app_color"]["white"],
            bg_color=self.themes.items["app_color"]["context_color"],
            bg_color_hover=self.themes.items["app_color"]["context_hover"],
            bg_color_pressed=self.themes.items["app_color"]["context_pressed"],
            border_color="transparent",
        )
        self.export_prefs_btn.setFixedHeight(40)
        self.export_prefs_btn.clicked.connect(self.on_export_preferences)
        self.prefs_layout.addWidget(self.export_prefs_btn)

        self.import_prefs_btn = PyPushButton2(
            text="Import Preferences",
            font_size=self.settings.items["font"]["text_size_normal"],
            font_weight=700,
            radius=4,
            font_color=self.themes.items["app_color"]["white"],
            bg_color=self.themes.items["app_color"]["gray_primary"],
            bg_color_hover=self.themes.items["app_color"]["gray_hover"],
            bg_color_pressed=self.themes.items["app_color"]["gray_pressed"],
            border_color="transparent",
        )
        self.import_prefs_btn.setFixedHeight(40)
        self.import_prefs_btn.clicked.connect(self.on_import_preferences)
        self.prefs_layout.addWidget(self.import_prefs_btn)

        self.main_layout.addWidget(self.prefs_group)

    def on_input_data_clicked(self):
        current_path = self.top_settings.get("paths", {}).get("input_data", os.getcwd())
        dialog = QFileDialog(None, "Select Input Data Path", current_path)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly)
        if dialog.exec():
            selected_path = dialog.selectedFiles()[0]
            self.settings.update_input_data_path(selected_path)
            self.top_settings = self.settings.get_top_settings()
            self.update_paths_display()
            QMessageBox.information(None, "Success", f"Input data path updated:\n{selected_path}")

    def on_reference_data_clicked(self):
        current_path = self.top_settings.get("paths", {}).get("reference_data", os.getcwd())
        dialog = QFileDialog(None, "Select Reference Data Path", current_path)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly)
        if dialog.exec():
            selected_path = dialog.selectedFiles()[0]
            self.settings.update_reference_data_path(selected_path)
            self.top_settings = self.settings.get_top_settings()
            self.update_paths_display()
            QMessageBox.information(None, "Success", f"Reference data path updated:\n{selected_path}")

    def on_results_data_clicked(self):
        current_path = self.top_settings.get("paths", {}).get("results_data", os.getcwd())
        dialog = QFileDialog(None, "Select Results Data Path", current_path)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly)
        if dialog.exec():
            selected_path = dialog.selectedFiles()[0]
            self.settings.update_results_data_path(selected_path)
            self.top_settings = self.settings.get_top_settings()
            self.update_paths_display()
            QMessageBox.information(None, "Success", f"Results data path updated:\n{selected_path}")

    def on_restore_default_paths_clicked(self):
        self.settings.update_input_data_path("Data")
        self.settings.update_reference_data_path("Data")
        self.settings.update_results_data_path("Results")
        self.top_settings = self.settings.get_top_settings()
        self.update_paths_display()
        QMessageBox.information(None, "Success", "Default paths restored:\nInput: Data\nReference: Data\nResults: Results")

    def update_paths_display(self):
        for btn, key in (
            (self.input_data_btn, "input_data"),
            (self.reference_data_btn, "reference_data"),
            (self.results_data_btn, "results_data"),
        ):
            raw = self.top_settings.get("paths", {}).get(key, "")
            btn.setText(self._truncate_path(raw) if raw else "Click to set path...")

    def on_format_changed(self, format):
        self.settings.update_export_image_format(format)
        self.top_settings = self.settings.get_top_settings()

    def on_resolution_changed(self, resolution):
        self.settings.update_export_image_resolution(int(resolution))
        self.top_settings = self.settings.get_top_settings()

    def on_export_preferences(self):
        parent_widget = QApplication.activeWindow()
        default_path = os.path.join(os.getcwd(), "AnyEIS_preferences.json")
        file_path, _ = QFileDialog.getSaveFileName(
            parent_widget,
            "Export User Preferences",
            default_path,
            "JSON Files (*.json)"
        )
        if file_path:
            if self.settings.export_user_preferences(file_path):
                QMessageBox.information(parent_widget, "Success", f"Preferences exported to:\n{file_path}")
            else:
                QMessageBox.warning(parent_widget, "Error", "Failed to export preferences.")

    def on_import_preferences(self):
        parent_widget = QApplication.activeWindow()
        file_path, _ = QFileDialog.getOpenFileName(
            parent_widget,
            "Import User Preferences",
            os.getcwd(),
            "JSON Files (*.json)"
        )
        if file_path:
            if self.settings.import_user_preferences(file_path):
                QMessageBox.information(parent_widget, "Success", "Preferences imported successfully!\nSome changes may require restart to take effect.")
                self.top_settings = self.settings.get_top_settings()
                self.format_combo.setCurrentText(self.top_settings.get("export_image", {}).get("format", "png"))
                self.resolution_combo.setCurrentText(str(self.top_settings.get("export_image", {}).get("resolution", 300)))
                self.update_paths_display()
            else:
                QMessageBox.warning(parent_widget, "Error", "Failed to import preferences. File may be invalid.")

    def retranslateUi(self, RightColumn):
        RightColumn.setWindowTitle(QCoreApplication.translate("RightColumn", u"Top Settings", None))
