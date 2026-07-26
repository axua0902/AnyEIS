
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


from GUI.pages.ui_page_home import Ui_MainPagesHome
from GUI.pages.ui_page_plotting import Ui_PlottingPage
from GUI.pages.ui_page_processing import Ui_ProcessingPage
from GUI.pages.ui_page_simulation import Ui_SimulationPage
from GUI.pages.ui_page_fitting import Ui_FittingPage




class Ui_Pages(object):
    def setupPages(self, Pages):
        if not Pages.objectName():
            Pages.setObjectName(u"MainPages")

        self.main_pages_layout = QVBoxLayout(Pages)
        self.main_pages_layout.setSpacing(0)
        self.main_pages_layout.setObjectName(u"main_pages_layout")
        self.main_pages_layout.setContentsMargins(5, 5, 5, 5)


        ####################################################################
        self.pages = QStackedWidget(Pages)
        self.pages.setObjectName(u"pages")
        ####################################################################
        self.home_page = Ui_MainPagesHome()
        self.home_page.page_home.setObjectName(u"page_home")
        self.pages.addWidget(self.home_page.page_home)
        ####################################################################
        self.plotting_page = Ui_PlottingPage()
        self.plotting_page.Plotting.setObjectName(u"page_plotting")
        self.pages.addWidget(self.plotting_page.Plotting)
        ####################################################################
        self.processing_page = Ui_ProcessingPage()
        self.processing_page.Processing.setObjectName(u"page_processing")
        self.pages.addWidget(self.processing_page.Processing)
        ####################################################################
        self.simulation_page = Ui_SimulationPage()
        self.simulation_page.Simulation.setObjectName(u"page_simulation")
        self.pages.addWidget(self.simulation_page.Simulation)
        ####################################################################
        self.fitting_page = Ui_FittingPage()
        self.fitting_page.Fitting.setObjectName(u"page_fitting")
        self.pages.addWidget(self.fitting_page.Fitting)
        ####################################################################


        ####################################################################
        self.main_pages_layout.addWidget(self.pages)
        self.pages.setCurrentIndex(0)
        ####################################################################

        QMetaObject.connectSlotsByName(Pages)

   