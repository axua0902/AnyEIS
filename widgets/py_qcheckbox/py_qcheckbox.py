# IMPORT QT CORE
# ///////////////////////////////////////////////////////////////
from qt_core import *

# STYLE
# ///////////////////////////////////////////////////////////////
style = '''
QCheckBox {{
    spacing: 5px;
    color: {_color};
}}
QCheckBox::indicator {{
    width: 13px;
    height: 13px;
}}
QCheckBox::indicator:unchecked {{
}}
QCheckBox::indicator:checked {{
}}
QCheckBox:hover {{
    color: {_color_hover};
}}
'''

# PY CHECK BOX
# ///////////////////////////////////////////////////////////////
class PyCheckBox(QCheckBox):
    def __init__(
        self,
        text,
        color,
        color_hover,
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
            _color = color,
            _color_hover = color_hover
        )
        self.setStyleSheet(custom_style)


