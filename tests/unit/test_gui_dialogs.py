"""Unit tests for GUI custom dialogs."""

from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QApplication

from app.gui.dialogs import BrowserRetryDialog


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_browser_retry_dialog_init(qapp):
    dialog = BrowserRetryDialog()
    assert dialog.windowTitle() == "Authentication Required"
    assert dialog.selected_browser is None
    assert dialog.open_settings is False


def test_browser_retry_dialog_select_browser(qapp):
    dialog = BrowserRetryDialog()
    handler = dialog._make_browser_handler("firefox")

    dialog.accept = MagicMock()
    handler()

    assert dialog.selected_browser == "firefox"
    assert dialog.open_settings is False
    dialog.accept.assert_called_once()


def test_browser_retry_dialog_open_settings(qapp):
    dialog = BrowserRetryDialog()
    dialog.accept = MagicMock()

    dialog._on_settings_clicked()

    assert dialog.selected_browser is None
    assert dialog.open_settings is True
    dialog.accept.assert_called_once()
