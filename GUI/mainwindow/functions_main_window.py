# IMPORT PACKAGES AND MODULES


# IMPORT QT CORE
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from GUI.functions.functions import Functions


# FUNCTIONS
class MainFunctions():
    def __init__(self, ui):
        self.ui = ui

    # SET MAIN WINDOW PAGES
    def set_page(self, page):
        self.ui.load_pages.pages.setCurrentWidget(page)
    # ///////////////////////////////////////////////////////////////

    # SET LEFT COLUMN PAGES
    def set_left_column_menu(self,menu,title,icon_path):
        self.ui.left_column.menus.menus.setCurrentWidget(menu)
        self.ui.left_column.title_label.setText(title)
        self.ui.left_column.icon.set_icon(icon_path)
    # ///////////////////////////////////////////////////////////////

    # SET RIGHT COLUMN PAGES
    def set_right_column_menu(self, menu):
        self.ui.right_column.menus.setCurrentWidget(menu)
    # ///////////////////////////////////////////////////////////////


    # RETURN IF LEFT COLUMN IS VISIBLE
    def left_column_is_visible(self):
        width = self.ui.left_column_frame.width()
        if width == 0:
            return False
        else:
            return True
    # ///////////////////////////////////////////////////////////////

    # RETURN IF RIGHT COLUMN IS VISIBLE
    def right_column_is_visible(self):
        width = self.ui.right_column_frame.width()
        if width == 0:
            return False
        else:
            return True
        # ///////////////////////////////////////////////////////////////

    # GET TITLE BUTTON BY OBJECT NAME
    def get_title_bar_btn(self, object_name):
        return self.ui.title_bar_frame.findChild(QPushButton, object_name)
    # ///////////////////////////////////////////////////////////////


    # GET TITLE BUTTON BY OBJECT NAME
    # ///////////////////////////////////////////////////////////////
    def get_left_menu_btn(self, object_name):
        return self.ui.left_menu.findChild(QPushButton, object_name)
    
    # LEFT AND RIGHT COLUMNS / SHOW / HIDE
    def toggle_left_column(self):
        # GET ACTUAL COLUMNS SIZE
        width = self.ui.left_column_frame.width()
        right_column_width = self.ui.right_column_frame.width()
        MainFunctions.start_box_animation(self, width, right_column_width, "left")

    # ///////////////////////////////////////////////////////////////

    def toggle_right_column(self):
        # GET ACTUAL COLUMNS SIZE
        left_column_width = self.ui.left_column_frame.width()
        width = self.ui.right_column_frame.width()
        MainFunctions.start_box_animation(self, left_column_width, width, "right")

    # ///////////////////////////////////////////////////////////////


    def start_box_animation(self, left_box_width, right_box_width, direction):

        time_animation = self.ui.settings["time_animation"]
        minimum_left = self.ui.settings["left_column_size"]["minimum"]
        maximum_left = self.ui.settings["left_column_size"]["maximum"]
        minimum_right = self.ui.settings["right_column_size"]["minimum"]
        maximum_right = self.ui.settings["right_column_size"]["maximum"]

        # Check Left Values        
        if left_box_width == minimum_left and direction == "left":
            left_width = maximum_left
        else:
            left_width = minimum_left

        # Check Right values        
        if right_box_width == minimum_right and direction == "right":
            right_width = maximum_right
        else:
            right_width = minimum_right       


        # ANIMATION LEFT BOX        
        self.left_box = QPropertyAnimation(self.ui.left_column_frame, b"minimumWidth")
        self.left_box.setDuration(time_animation)
        self.left_box.setStartValue(left_box_width)
        self.left_box.setEndValue(left_width)
        self.left_box.setEasingCurve(QEasingCurve.Type.InOutQuart)

        # ANIMATION RIGHT BOX        
        self.right_box = QPropertyAnimation(self.ui.right_column_frame, b"minimumWidth")
        self.right_box.setDuration(time_animation)
        self.right_box.setStartValue(right_box_width)
        self.right_box.setEndValue(right_width)
        self.right_box.setEasingCurve(QEasingCurve.Type.InOutQuart)

        # GROUP ANIMATION
        self.group = QParallelAnimationGroup()
        self.group.stop()
        self.group.addAnimation(self.left_box)
        self.group.addAnimation(self.right_box)
        self.group.start()

        # ///////////////////////////////////////////////////////////////


        # LEFT MENU BTN IS CLICKED
        # Run function when btn is clicked
        # Check funtion by object name / btn_id
    def btn_clicked(self,btn):
        # Remove Selection If Clicked By "btn_close_left_column"
        if btn.objectName() != "btn_settings":
            self.ui.left_menu.deselect_all_tab()

        # Get Title Bar Btn And Reset Active
        top_settings = MainFunctions.get_title_bar_btn(self, "btn_top_settings")
        top_settings.set_active(False)


        # LEFT MENU TOP BUTTONS
        left_menu_btns_top = {
            "btn_home": self.ui.load_pages.home_page.page_home,# Home
            "btn_plotting": self.ui.load_pages.plotting_page.Plotting,# Plotting
            "btn_processing": self.ui.load_pages.processing_page.Processing,# Processing
            "btn_simulation": self.ui.load_pages.simulation_page.Simulation,# Simulation
            "btn_fitting": self.ui.load_pages.fitting_page.Fitting,# Fitting
        }
        btn_name = btn.objectName()
        if btn_name in left_menu_btns_top:
            self.ui.left_menu.select_only_one(btn_name)
            MainFunctions.set_page(self, left_menu_btns_top[btn_name])

        # LEFT MENU BOTTOM BUTTONS
        left_menu_btns_bottom = {
            "btn_theme": {
                "menu_name": self.ui.left_column.menus.menu_theme,
                "title_name": "Theme",
                "icon_name": "icon_heart.svg"
            },
            "btn_info": {
                "menu_name": self.ui.left_column.menus.menu_info,
                "title_name": "Information",
                "icon_name": "icon_info.svg"
            },
            "btn_settings": {
                "menu_name": self.ui.left_column.menus.menu_setting,
                "title_name": "Settings",
                "icon_name": "icon_settings.svg"
            }
        }

        btn_name = btn.objectName()
        if btn_name in left_menu_btns_bottom:
            current_menu = self.ui.left_column.menus.menus.currentWidget()
            target_menu = left_menu_btns_bottom[btn_name]["menu_name"]

            if not MainFunctions.left_column_is_visible(self):
                MainFunctions.toggle_left_column(self)
            elif current_menu == target_menu:
                MainFunctions.toggle_left_column(self)

            self.ui.left_menu.select_only_one_tab(btn_name)
            MainFunctions.set_left_column_menu(
                self,
                menu=left_menu_btns_bottom[btn_name]["menu_name"],
                title=left_menu_btns_bottom[btn_name]["title_name"],
                icon_path=Functions.set_svg_icon(left_menu_btns_bottom[btn_name]["icon_name"])
            )

        # CLOSE LEFT COLUMN 关闭左侧栏按钮
        if btn.objectName() == "btn_close_left_column":
            self.ui.left_menu.deselect_all_tab()
            MainFunctions.toggle_left_column(self)


        # SETTINGS TITLE BAR
        if btn.objectName() == "btn_top_settings":
            if not MainFunctions.right_column_is_visible(self):         # Toogle Active
                btn.set_active(True)
                MainFunctions.toggle_right_column(self)                # Show / Hide
            else:
                btn.set_active(False)
                MainFunctions.toggle_right_column(self)                # Show / Hide
            top_settings = MainFunctions.get_left_menu_btn(self, "btn_settings")  # Get Left Menu Btn
            top_settings.set_active_tab(False)

        print(f"Button {btn.objectName()}, clicked!")        # DEBUG



    def btn_released(self,btn):
        print(f"Button {btn.objectName()}, released!") # DEBUG






