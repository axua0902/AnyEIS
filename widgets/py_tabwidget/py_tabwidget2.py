from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt

# STYLE
# ///////////////////////////////////////////////////////////////
style = '''
/* /////////////////////////////////////////////////////////////////////////////////////////////////
QTabWidget */

QTabWidget {{	
    background-color: {_bg_color};
    padding: 2px;
    border-radius: {_radius}px;
    color: {_color};
    border: 1px solid {_bottom_line_color};
}}

QTabWidget::pane {{
    background-color: {_bg_color};
    border-radius: {_radius}px;
}}

QTabWidget::tab-bar {{
    alignment: {_alignment};
    border: none;
}}

QTabBar::tab {{
    background-color: {_tab_bg_color};
    color: {_tab_text_color};
    padding: 5px 12px;
    margin-right: 2px;
    border-top-left-radius: {_radius}px;
    border-top-right-radius: {_radius}px;
    border: 1px solid {_bottom_line_color};
    border-bottom: none;
    min-width: 70px;
    min-height: 15px;
    font-size: {_font_size}px;
    font-weight: {_font_weight};
    font-style: {_font_style};
    text-align: {_text_align};
}}

QTabBar::tab:selected {{
    background-color: {_selection_color};
    color: {_tab_active_text_color};
    border-top: 2px solid {_tab_active_color};
    border-left: 1px solid {_bottom_line_color};
    border-right: 1px solid {_bottom_line_color};
    border-bottom: 1px solid {_selection_color};
    margin-bottom: -1px;
}}

QTabBar::tab:hover:!selected {{
    background-color: {_tab_hover_color};
    color: {_tab_hover_text_color};
    border-top: 2px solid {_tab_hover_border_color};
}}

QTabBar::tab:!selected {{
    background-color: {_tab_bg_color};
    color: {_tab_text_color};
    border-bottom: 1px solid {_bottom_line_color};
    margin-top: 2px;
}}

QTabBar::tab:first {{
    margin-left: 0px;
}}

QTabBar::tab:last {{
    margin-right: 0px;
}}

'''

# PY TAB WIDGET
# ///////////////////////////////////////////////////////////////
class PyTabWidget2(QTabWidget):
    def __init__(
        self,
        radius = 8,
        color = "#303133",
        bg_color = "#FFFFFF", 
        selection_color = "#EBF2FC",
        bottom_line_color = "#E6EAEF",
        tab_bg_color = "#F5F7FA",
        tab_text_color = "#303133",
        tab_active_color = "#0078FF",
        tab_active_text_color = "#1A1A1A",
        tab_hover_color = "#E6EAEF",
        tab_hover_text_color = "#1A1A1A",
        tab_hover_border_color = "#2590FF",
        alignment = "left",
        font_size = 12,
        font_weight = 700,
        font_style = "normal",
        text_align = "center",
        parent = None,
    ):
        super().__init__()

        # SET PARAMETERS
        if parent != None:
            self.setParent(parent)

        # SET STYLESHEET
        custom_style = style.format(
            _radius = radius,
            _color = color,
            _bg_color = bg_color,
            _selection_color = selection_color,
            _bottom_line_color = bottom_line_color,
            _tab_bg_color = tab_bg_color,
            _tab_text_color = tab_text_color,
            _tab_active_color = tab_active_color,
            _tab_active_text_color = tab_active_text_color,
            _tab_hover_color = tab_hover_color,
            _tab_hover_text_color = tab_hover_text_color,
            _tab_hover_border_color = tab_hover_border_color,
            _alignment = alignment,
            _font_size = font_size,
            _font_weight = font_weight,
            _font_style = font_style,
            _text_align = text_align
        )
        self.setStyleSheet(custom_style)

