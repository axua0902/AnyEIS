from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt

# IMPORT STYLE
# ///////////////////////////////////////////////////////////////
from . style import *

# PY PUSH BUTTON
# ///////////////////////////////////////////////////////////////
class PyTabWidget(QTabWidget):
    def __init__(
        self, 
        radius=8,
        color="#6c99f4",
        bg_color="#444",
        selection_color="#FFF",
        bottom_line_color="#666",  # 添加底部线条颜色的参数
    ):
        super().__init__()

        # PARAMETERS

        # SET STYLESHEET
        self.set_stylesheet(
            radius,
            color,
            bg_color,
            selection_color,
            bottom_line_color
        )

    # SET STYLESHEET
    def set_stylesheet(
        self,
        radius,
        color,
        bg_color,
        selection_color,
        bottom_line_color
    ):
        # APPLY STYLESHEET
        style_format = style.format(
            _radius=radius,
            _color=color,
            _bg_color=bg_color,
            _selection_color=selection_color,
            _bottom_line_color=bottom_line_color,
            _alignment = "left"
        )
        self.setStyleSheet(style_format)