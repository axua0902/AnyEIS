
# IMPORT QT CORE
# ///////////////////////////////////////////////////////////////
from qt_core import *

# STYLE
# ///////////////////////////////////////////////////////////////
style = '''
QPushButton {{
	border: 1px solid {_border_color};
    font-family: {_font_family};
    font-size: {_font_size}px;
    font-weight: {_font_weight};
    font-style: {_font_style};
    text-align: {_text_align};
    padding-left: {_padding_left}px;
    padding-right: {_padding_right}px;
    color: {_font_color};
	border-radius: {_radius};	
	background-color: {_bg_color};
}}
QPushButton:hover {{
	background-color: {_bg_color_hover};
}}
QPushButton:pressed {{	
	background-color: {_bg_color_pressed};
}}
'''

# PY PUSH BUTTON
# ///////////////////////////////////////////////////////////////
class PyPushButton2(QPushButton):
    def __init__(
        self, 
        text,
        radius,
        font_color,
        bg_color,
        bg_color_hover,
        bg_color_pressed,
        font_size,
        border_color,
        font_weight = 700,
        font_style = "normal",
        text_align = "center",
        padding_left = 5,
        padding_right = 5,
        font_family = "Arial, sans-serif",
        parent = None,
    ):
        super().__init__()

        # SET PARAMETRES
        self.setText(text)
        if parent != None:
            self.setParent(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # SET STYLESHEET
        custom_style = style.format(
            _font_color = font_color,
            _radius = radius,
            _bg_color = bg_color,
            _bg_color_hover = bg_color_hover,
            _bg_color_pressed = bg_color_pressed,
            _font_size=font_size,
            _border_color=border_color,
            _font_weight=font_weight,
            _font_style=font_style,
            _text_align=text_align,
            _padding_left=padding_left,
            _padding_right=padding_right,
            _font_family=font_family,
        )
        self.setStyleSheet(custom_style)

        