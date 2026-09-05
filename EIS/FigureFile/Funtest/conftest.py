# -*- coding: utf-8 -*-
"""
conftest.py for EIS/FigureFile/Funtest

pytest fixtures for the Figure render integration tests.

Responsibilities:
  1. Fix sys.path so `import EIS.FigureFile.Figure` works when running
     `pytest EIS/FigureFile/Funtest/test_figure_render.py` from project root.
  2. Provide a session-scoped QApplication singleton (Qt allows only one).
  3. Provide a function-scoped FigWidget fixture that creates a fresh widget
     per test and tears it down afterwards.

Note: The Figure import chain does NOT touch mpmath/gmpy2, so unlike
EIS/ProcessingFile/Funtest/conftest.py we do NOT need the
`sys.modules['gmpy2'] = None` hack.
"""
import os
import sys

# 1. sys.path: project root = 3 levels up from this file
#    EIS/FigureFile/Funtest/conftest.py
#    -> EIS/FigureFile/Funtest/  (this dir)
#    -> EIS/FigureFile/
#    -> EIS/
#    -> AnyEIS/                   (project root)
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..')
)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from PySide6.QtWidgets import QApplication
import pytest


@pytest.fixture(scope="session")
def qapp():
    """Session-scoped QApplication singleton.

    Qt forbids creating more than one QApplication per process, so all
    tests in this file share the same instance.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def fig_widget(qapp):
    """Function-scoped FigWidget: a fresh widget per test, closed after.

    The widget is NOT shown on screen; drawfigure() populates the
    embedded MyMplCanvas fig in-process, which is enough for assertions
    on fig.axes / fig.axes[i].lines.
    """
    from EIS.FigureFile.Figure import FigWidget
    w = FigWidget()
    try:
        yield w
    finally:
        w.close()
        w.deleteLater()
