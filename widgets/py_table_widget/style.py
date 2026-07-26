# 表格样式定义
# ///////////////////////////////////////////////////////////////
style = '''
/* /////////////////////////////////////////////////////////////////////////////////////////////////
QTableWidget - 表格组件样式 */

QTableWidget {{	
	background-color: {_bg_color};
	padding: 5px;
	border-radius: {_radius}px;
	gridline-color: {_grid_line_color};
    color: {_color};
    font-size: 16px;
    border: none;
    border-radius: 0px;
    padding: 0px;
}}
QTableWidget::item{{
	border-color: none;
	padding: 10px 16px;
	gridline-color: {_grid_line_color};
    border-bottom: 1px solid {_bottom_line_color};
    color: {_color};
}}
QTableWidget::item:selected{{
	background-color: {_selection_color};
    color: #FFFFFF;
}}
QTableWidget::item:hover {{
    background-color: {_header_vertical_color};
}}
QHeaderView::section{{
	background-color: {_header_horizontal_color};
	max-width: 30px;
	border: none;
    border-bottom: 1px solid {_bottom_line_color};
}}
QTableWidget::horizontalHeader {{	
	background-color: {_header_horizontal_color};
}}
QTableWidget QTableCornerButton::section {{
    border: none;
	background-color: {_header_horizontal_color};
	padding: 3px;
    border-top-left-radius: {_radius}px;
}}
QHeaderView::section:horizontal
{{
    border: none;
	background-color: {_header_horizontal_color};
    padding: 0px 16px;
    color: {_color};
    font-weight: {_header_font_weight};
    font-size: {_header_font_size};
    border-bottom: 1px solid {_bottom_line_color};
    height: 40px;
    line-height: 40px;
    vertical-align: middle;
}}
QHeaderView::section:vertical
{{
    border: none;
	background-color: {_header_vertical_color};
    border-bottom: 1px solid {_bottom_line_color};
    color: {_color};
    padding: 0px;
    margin: 0px;
    font-weight: 500;
    font-size: 16px;
    height: 40px;
    text-align: center;
}}
QHeaderView::section:vertical:nth-child(even) {{
    background-color: {_bg_color};
}}
QHeaderView::section:vertical:nth-child(odd) {{
    background-color: {_header_vertical_color};
}}
QTableView {{
    gridline-color: {_grid_line_color};
    background-color: {_bg_color};
    selection-background-color: {_selection_color};
    selection-color: #FFFFFF;
    alternate-background-color: {_header_vertical_color};
}}
QTableView::item:hover {{
    background-color: {_header_vertical_color};
}}

/* /////////////////////////////////////////////////////////////////////////////////////////////////
Checkbox Indicators */
QTableWidget::indicator {{
    width: 20px;
    height: 20px;
}}
QTableWidget::indicator:checked {{
    background-color: #2196F3;
    border: 2px solid #2196F3;
}}
QTableWidget::indicator:unchecked {{
    background-color: transparent;
    border: 2px solid #757575;
}}

/* /////////////////////////////////////////////////////////////////////////////////////////////////
ScrollBars */
QScrollBar:horizontal {{
    border: none;
    background: {_scroll_bar_bg_color};
    height: 8px;
    margin: 0px 21px 0 21px;
	border-radius: 0px;
}}
QScrollBar::handle:horizontal {{
    background: {_context_color};
    min-width: 25px;
	border-radius: 4px
}}
QScrollBar::add-line:horizontal {{
    border: none;
    background: {_scroll_bar_btn_color};
    width: 20px;
	border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
    subcontrol-position: right;
    subcontrol-origin: margin;
}}
QScrollBar::sub-line:horizontal {{
    border: none;
    background: {_scroll_bar_btn_color};
    width: 20px;
	border-top-left-radius: 4px;
    border-bottom-left-radius: 4px;
    subcontrol-position: left;
    subcontrol-origin: margin;
}}
QScrollBar::up-arrow:horizontal, QScrollBar::down-arrow:horizontal
{{
     background: none;
}}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal
{{
     background: none;
}}
QScrollBar:vertical {{
	border: none;
    background: {_scroll_bar_bg_color};
    width: 8px;
    margin: 21px 0 21px 0;
	border-radius: 0px;
}}
QScrollBar::handle:vertical {{	
	background: {_context_color};
    min-height: 25px;
	border-radius: 4px
}}
QScrollBar::add-line:vertical {{
     border: none;
    background: {_scroll_bar_btn_color};
     height: 20px;
	border-bottom-left-radius: 4px;
    border-bottom-right-radius: 4px;
     subcontrol-position: bottom;
     subcontrol-origin: margin;
}}
QScrollBar::sub-line:vertical {{
	border: none;
    background: {_scroll_bar_btn_color};
     height: 20px;
	border-top-left-radius: 4px;
    border-top-right-radius: 4px;
     subcontrol-position: top;
     subcontrol-origin: margin;
}}
QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {{
     background: none;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
     background: none;
}}
'''