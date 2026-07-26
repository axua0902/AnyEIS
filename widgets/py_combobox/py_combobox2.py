# IMPORT QT CORE
# ///////////////////////////////////////////////////////////////
from qt_core import *

# STYLE
# ///////////////////////////////////////////////////////////////
style = '''
QComboBox {{
	border: 1px solid {_border_color};
    padding-left: 10px;
    padding-right: 5px;
    color: {_color};
	border-radius: {_radius}px;	
	background-color: {_bg_color};
    font-size: {_font_size}px;
    font-weight: {_font_weight};
    min-height: {_min_height}px;
}}
QComboBox QAbstractItemView {{
    selection-background-color: {_selection_color};
}}
QComboBox:hover {{
	background-color: {_bg_color_hover};
}}
QComboBox:pressed {{	
	background-color: {_bg_color_pressed};
}}
QComboBox:drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left-width: 1px;
    border-left-color: {_dropdown_border_color};
    border-left-style: solid;
    border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
    background-color: transparent;
}}
QComboBox::down-arrow {{
    image: url(images/svg_icons/icon_arrow_down.svg);
    width: 14px;
    height: 14px;
}}
'''

# PY COMBO BOX
# ///////////////////////////////////////////////////////////////
class PyComboBox2(QComboBox):
    def __init__(
        self,
        radius = 8,
        color = "#000000",
        bg_color = "#FFFFFF",
        bg_color_hover = "#F0F0F0",
        bg_color_pressed = "#E0E0E0",
        selection_color = "#0078D4",
        border_color = None,
        dropdown_border_color = None,
        font_size = 16,
        font_weight = 700,
        min_height = 38,
        parent = None
    ):
        super().__init__()

        # SET PARAMETRES
        if parent is not None:
            self.setParent(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Use border_color if provided, otherwise use color
        border_color = border_color if border_color is not None else color
        # Use dropdown_border_color if provided, otherwise use border_color
        dropdown_border_color = dropdown_border_color if dropdown_border_color is not None else border_color

        # SET STYLESHEET
        custom_style = style.format(
            _border_color = border_color,
            _dropdown_border_color = dropdown_border_color,
            _radius = radius,
            _color = color,
            _bg_color = bg_color,
            _bg_color_hover = bg_color_hover,
            _bg_color_pressed = bg_color_pressed,
            _selection_color = selection_color,
            _font_size = font_size,
            _font_weight = font_weight,
            _min_height = min_height
        )
        self.setStyleSheet(custom_style)


