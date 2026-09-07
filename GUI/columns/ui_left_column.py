from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


from GUI.columns.ui_left_setting import Ui_LeftSetting
from widgets.py_push_button.py_push_button import PyPushButton



class Ui_LeftColumn(object):
    def setupUi(self, LeftColumn):
        if not LeftColumn.objectName():
            LeftColumn.setObjectName(u"LeftColumn")


        LeftColumn.resize(200, 600)
        self.main_pages_layout = QVBoxLayout(LeftColumn)
        self.main_pages_layout.setSpacing(0)
        self.main_pages_layout.setObjectName(u"main_pages_layout")
        self.main_pages_layout.setContentsMargins(5, 5, 5, 5)

        self.menus = QStackedWidget(LeftColumn)
        self.menus.setObjectName(u"menus")


        self.left_setting = Ui_LeftSetting()

    # ///////////////////////////////////////////////////////////////

        # Menu_ Theme
        self.menu_theme = QWidget()
        self.menu_theme.setObjectName(u"menu_theme")
        self.verticalLayout_theme = QVBoxLayout(self.menu_theme)
        self.verticalLayout_theme.setSpacing(5)
        self.verticalLayout_theme.setObjectName(u"verticalLayout_theme")
        self.verticalLayout_theme.setContentsMargins(5, 5, 5, 5)


        self.verticalLayout_theme.addWidget(self.left_setting.theme_dark)
        self.verticalLayout_theme.addWidget(self.left_setting.theme_light)
        self.verticalLayout_theme.addStretch()  # 让按钮集中在上方

        self.left_setting.theme_dark.clicked.connect(lambda: self.left_setting.on_theme_update_clicked("dark"))
        self.left_setting.theme_light.clicked.connect(lambda: self.left_setting.on_theme_update_clicked("light"))

        self.menus.addWidget(self.menu_theme)


    # ///////////////////////////////////////////////////////////////
        # menu_info
        self.menu_info = QWidget()
        self.menu_info.setObjectName(u"menu_info")
        self.verticalLayout_2 = QVBoxLayout(self.menu_info)
        self.verticalLayout_2.setSpacing(5)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(5, 5, 5, 5)

        self.menu_info_widget = QWidget(self.menu_info)
        self.menu_info_widget.setObjectName(u"btn_4_widget")
        self.menu_info_widget.setMinimumSize(QSize(0, 40))
        self.menu_info_widget.setMaximumSize(QSize(16777215, 40))
        self.verticalLayout_2.addWidget(self.menu_info_widget)

        self.label_basic_info = QLabel(self.menu_info)
        self.label_basic_info.setObjectName(u"label_basic_info")
        self.label_basic_info.setStyleSheet(u"font-size: 12pt; font-weight: bold;")
        self.label_basic_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_basic_info.setWordWrap(True)
        self.verticalLayout_2.addWidget(self.label_basic_info)

        self.label_tech = QLabel(self.menu_info)
        self.label_tech.setObjectName(u"label_tech")
        self.label_tech.setStyleSheet(u"font-size: 9pt;")
        self.label_tech.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_tech.setWordWrap(True)
        self.verticalLayout_2.addWidget(self.label_tech)

        self.label_contact = QLabel(self.menu_info)
        self.label_contact.setObjectName(u"label_contact")
        self.label_contact.setStyleSheet(u"font-size: 9pt; color: #007acc;")
        self.label_contact.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_contact.setOpenExternalLinks(True)
        self.label_contact.setWordWrap(True)
        self.verticalLayout_2.addWidget(self.label_contact)

        self.label_contribution = QLabel(self.menu_info)
        self.label_contribution.setObjectName(u"label_contrib_other")
        self.label_contribution.setStyleSheet(u"font-size: 9pt;")
        self.label_contribution.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_contribution.setOpenExternalLinks(True)
        self.label_contribution.setWordWrap(True)
        self.verticalLayout_2.addWidget(self.label_contribution)


        self.label_copyright = QLabel(self.menu_info)
        self.label_copyright.setObjectName(u"label_copyright_license")
        self.label_copyright.setStyleSheet(u"font-size: 9pt;")
        self.label_copyright.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_copyright.setOpenExternalLinks(True)
        self.label_copyright.setWordWrap(True)
        self.verticalLayout_2.addWidget(self.label_copyright)

        self.menus.addWidget(self.menu_info)



    # ///////////////////////////////////////////////////////////////

        # Menu menu_setting
        self.menu_setting = QWidget()
        self.menu_setting.setObjectName(u"menu_setting")
        self.verticalLayout = QVBoxLayout(self.menu_setting)
        self.verticalLayout.setSpacing(5)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(5, 5, 5, 5)


        # self.left_setting = Ui_LeftSetting()
        self.verticalLayout.addWidget(self.left_setting.left_btn_working_path)
        self.verticalLayout.addWidget(self.left_setting.left_btn_language)
        self.verticalLayout.addWidget(self.left_setting.left_btn_2)
        self.verticalLayout.addWidget(self.left_setting.left_btn_3)
        self.verticalLayout.addStretch()  # 让按钮集中在上方

        self.left_setting.left_btn_working_path.clicked.connect(self.left_setting.on_working_path_clicked)
        self.left_setting.left_btn_language.clicked.connect(self.left_setting.on_language_clicked)
        self.left_setting.left_btn_2.clicked.connect(self.left_setting.on_help_clicked)
        self.left_setting.left_btn_3.clicked.connect(self.left_setting.on_about_clicked)

        self.menus.addWidget(self.menu_setting)


        self.main_pages_layout.addWidget(self.menus)
        self.retranslateUi(LeftColumn)
        self.menus.setCurrentIndex(0)

        QMetaObject.connectSlotsByName(LeftColumn)




    # retranslateUi
    def retranslateUi(self, LeftColumn):
        LeftColumn.setWindowTitle(QCoreApplication.translate("LeftColumn", u"Form", None))
        # Merge information content
        self.label_basic_info.setText(QCoreApplication.translate(
            "LeftColumn",
            u"AnyEIS\n Version: v1.0.0\n",
            None
        ))
        self.label_copyright.setText(QCoreApplication.translate(
            "LeftColumn",
            u"© 2020-2026 AnyEIS Authors. All rights reserved.<br>"
            u'<a href="https://www.apache.org/licenses/LICENSE-2.0">License: Apache License 2.0</a>',
            None
        ))
        self.label_contact.setText(QCoreApplication.translate(
            "LeftColumn",
            u'Support Email: zhan234@outlook.com<br>'
            u'<a href="https://github.com/axua0902/AnyEIS">GitHub: github.com/axua0902/AnyEIS</a>',
            None
        ))
        self.label_tech.setText(QCoreApplication.translate(
            "LeftColumn",
            u"Dependencies: PySide6 >= 6.5.0, numpy >= 1.24.0, pandas >= 2.0.0, "
            u"matplotlib >= 3.7.0, openpyxl >= 3.1.0, lmfit >= 1.2.0, "
            u"schemdraw >= 0.18.0, scipy >= 1.10.0, mpmath >= 1.3.0",
            None
        ))
        self.label_contribution.setText(QCoreApplication.translate(
            "LeftColumn",
            u"Contributors: Zhang An<br>"
            u"Developer: AnyEIS Authors \nRelease Date: 2026.09.01<br>"
            u"Acknowledgements: Thanks to all testers and community supporters.<br>",
            None
        ))


