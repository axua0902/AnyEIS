# IMPORT QT CORE
# ///////////////////////////////////////////////////////////////
from qt_core import *



# STYLE
# ///////////////////////////////////////////////////////////////
label_style = '''
QLabel {{
	color: {_color};
	font: {_font};
    padding-left: {_padding_left};
    border-left: {_border_left};
}}
QLabel:hover {{
	color: {_color_hover};
}}
'''

# PY LABEL
# ///////////////////////////////////////////////////////////////
class PyLabel2(QLabel):
    def __init__(
        self,
        text="",
        color="#000000",  # 默认颜色为黑色
        font_family="Segoe UI",  
        font_size=14,  
        font_weight=500,  
        color_hover=None,
        padding_left="2px",  # 默认左内边距
        border_left="2px solid transparent",  # 默认左边框
        parent=None,
    ):
        super().__init__(parent=parent)
        self.setText(text)

        # SET PARAMETERS
        if parent is not None:
            self.setParent(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # SET FONT
        font = QFont(font_family, font_size, QFont.Weight(font_weight))
        self.setFont(font)

        # SET STYLESHEET
        custom_style = label_style.format(
            _color=color,
            _font=f"{font_size}pt '{font_family}' {font_weight}",
            _color_hover=color_hover if color_hover is not None else color,
            _padding_left=padding_left,
            _border_left=border_left
        )
        self.setStyleSheet(custom_style)