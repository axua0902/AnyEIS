# STYLE
# ///////////////////////////////////////////////////////////////
style = '''
/* /////////////////////////////////////////////////////////////////////////////////////////////////
QTabWidget */

QTabWidget {{	
    background-color: {_bg_color};
    padding: 0px;
    border-radius: {_radius}px;
    color: {_color};
    border: 1px solid {_bottom_line_color};
}}

QTabWidget::pane {{
    border: 1px solid {_bottom_line_color};
    border-top: 1px solid {_tab_active_color};
    background-color: {_bg_color};
    border-radius: {_radius}px;
    margin-top: -1px;
}}

QTabWidget::tab-bar {{
    alignment: {_alignment};
    border: none;
}}

QTabBar::tab {{
    background-color: {_tab_bg_color};
    color: {_tab_text_color};
    margin-right: 2px;
    border-top-left-radius: {_radius}px;
    border-top-right-radius: {_radius}px;
    border: 1px solid {_bottom_line_color};
    border-bottom: none;
    min-width: 80px;
    min-height: 25px;
    padding: 5px 16px;
    font-weight: 600;
}}

QTabBar::tab:selected {{
    background-color: {_selection_color};
    color: {_tab_active_text_color};
    border-top: 2px solid {_tab_active_color};
    border-left: 1px solid {_bottom_line_color};
    border-right: 1px solid {_bottom_line_color};
    border-bottom: 1px solid {_selection_color};
    margin-bottom: -1px;
}}

QTabBar::tab:hover:!selected {{
    background-color: {_tab_hover_color};
    color: {_tab_hover_text_color};
    border-top: 2px solid {_tab_hover_border_color};
}}

QTabBar::tab:!selected {{
    background-color: {_tab_bg_color};
    color: {_tab_text_color};
    border-bottom: 1px solid {_bottom_line_color};
    margin-top: 2px;
}}

QTabBar::tab:first {{
    margin-left: 0px;
}}

QTabBar::tab:last {{
    margin-right: 0px;
}}

'''