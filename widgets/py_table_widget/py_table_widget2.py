# -*- coding: utf-8 -*-
"""
PyTableWidget2 - 自定义表格组件
提供了一个具有自定义样式和主题支持的表格组件
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidget

# 导入样式模板
from .style import style

class PyTableWidget2(QTableWidget):
    """
    自定义表格组件类
    提供了一个可自定义外观的表格控件，支持主题颜色和样式定制
    """
    def __init__(
        self, 
        radius = 8,                      # 表格圆角半径
        color = "#FFF",                  # 文本颜色
        bg_color = "#444",               # 背景颜色
        selection_color = "#FFF",        # 选中项颜色
        header_horizontal_color = "#333", # 水平表头颜色
        header_vertical_color = "#444",  # 垂直表头颜色
        bottom_line_color = "#555",      # 底部线条颜色
        grid_line_color = "#555",        # 网格线颜色
        scroll_bar_bg_color = "#FFF",    # 滚动条背景颜色
        scroll_bar_btn_color = "#3333",  # 滚动条按钮颜色
        context_color = "#00ABE8",       # 上下文颜色（用于滚动条和选中项）
        header_font_size = "16px",       # 表头字体大小
        header_font_weight = 600         # 表头字体粗细
    ):
        super().__init__()
        
        # 应用样式表
        self.set_stylesheet(
            radius,
            color,
            bg_color,
            header_horizontal_color,
            header_vertical_color,
            selection_color,
            bottom_line_color,
            grid_line_color,
            scroll_bar_bg_color,
            scroll_bar_btn_color,
            context_color,
            header_font_size,
            header_font_weight
        )

    def set_stylesheet(
        self,
        radius,
        color,
        bg_color,
        header_horizontal_color,
        header_vertical_color,
        selection_color,
        bottom_line_color,
        grid_line_color,
        scroll_bar_bg_color,
        scroll_bar_btn_color,
        context_color,
        header_font_size = "16px",
        header_font_weight = 600
    ):
        """
        设置表格样式
        
        使用style模板并填充颜色参数来设置表格的外观
        """
        # 应用样式表，使用format方法填充样式模板中的颜色参数
        style_format = style.format(
            _radius = radius,          
            _color = color,
            _bg_color = bg_color,
            _header_horizontal_color = header_horizontal_color,
            _header_vertical_color = header_vertical_color,
            _selection_color = selection_color,
            _bottom_line_color = bottom_line_color,
            _grid_line_color = grid_line_color,
            _scroll_bar_bg_color = scroll_bar_bg_color,
            _scroll_bar_btn_color = scroll_bar_btn_color,
            _context_color = context_color,
            _header_font_size = header_font_size,
            _header_font_weight = header_font_weight
        )
        self.setStyleSheet(style_format)