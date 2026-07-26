# IMPORT QT CORE
# ///////////////////////////////////////////////////////////////
from qt_core import *

# STYLE
# ///////////////////////////////////////////////////////////////
style = '''
QCheckBox {{
    font-size: {_font_size}px;
    font-weight: {_font_weight};
    color: {_text_foreground};
    spacing: {_spacing}px;
}}
QCheckBox::indicator {{
    width: {_indicator_width}px;
    height: {_indicator_height}px;
    border: {_border_width}px solid {_input_border};
    border-radius: {_border_radius}px;
    background-color: {_white_background};
}}
QCheckBox::indicator:unchecked {{
}}
QCheckBox::indicator:checked {{
    background-color: {_blue_primary};
    border-color: {_blue_primary};
}}
QCheckBox:hover {{
    color: {_color_hover};
}}
'''


# PY CHECK BOX
# ///////////////////////////////////////////////////////////////
class PyCheckBox2(QCheckBox):
    def __init__(
        self,
        text,
        text_foreground = "#000000",
        color_hover = "#333333",
        input_border = "#cccccc",
        white_background = "#ffffff",
        blue_primary = "#0078d4",
        font_size = 16,
        font_weight = 700,
        spacing = 8,
        indicator_width = 18,
        indicator_height = 18,
        border_width = 2,
        border_radius = 3,
        parent = None
    ):
        super().__init__()

        # SET PARAMETRES
        self.setText(text)
        if parent is not None:
            self.setParent(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # SET STYLESHEET
        custom_style = style.format(
            _font_size = font_size,
            _font_weight = font_weight,
            _text_foreground = text_foreground,
            _spacing = spacing,
            _indicator_width = indicator_width,
            _indicator_height = indicator_height,
            _border_width = border_width,
            _input_border = input_border,
            _border_radius = border_radius,
            _white_background = white_background,
            _blue_primary = blue_primary,
            _color_hover = color_hover
        )
        self.setStyleSheet(custom_style)
    


