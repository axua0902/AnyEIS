# IMPORT QT CORE
# ///////////////////////////////////////////////////////////////
from qt_core import *



# STYLE
# ///////////////////////////////////////////////////////////////
label_style = '''
QLabel {{
	color: {_color};
	font: {_font};
}}
QLabel:hover {{
	color: {_color_hover};
}}
'''

# PY LABEL
# ///////////////////////////////////////////////////////////////
class PyLabel(QLabel):
    def __init__(
        self,
        text="",
        color="#000000",  # 默认颜色为黑色
        font_family="Segoe UI",  # 默认字体为 Arial
        font_size=12,  # 默认字体大小为 10
        font_weight=400,  # 默认字体权重为正常
        color_hover=None,
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
            _font=f"{font_family};{font_size};{font_weight}",
            _color_hover=color_hover if color_hover is not None else color
        )
        self.setStyleSheet(custom_style)