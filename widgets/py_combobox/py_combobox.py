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
	border-radius: {_radius};	
	background-color: {_bg_color};
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
'''

# PY COMBO BOX
# ///////////////////////////////////////////////////////////////
class PyComboBox(QComboBox):
    def __init__(
        self,
        radius,
        color,
        bg_color,
        bg_color_hover,
        bg_color_pressed,
        selection_color,
        parent = None
    ):
        super().__init__()

        # SET PARAMETRES
        if parent is not None:
            self.setParent(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # SET STYLESHEET
        custom_style = style.format(
            _border_color = color,
            _radius = radius,
            _color = color,
            _bg_color = bg_color,
            _bg_color_hover = bg_color_hover,
            _bg_color_pressed = bg_color_pressed,
            _selection_color = selection_color
        )
        self.setStyleSheet(custom_style)


