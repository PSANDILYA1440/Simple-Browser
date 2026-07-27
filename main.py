import json
import sys
from pathlib import Path
from urllib.parse import quote_plus

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QFont
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

SETTINGS_FILE = Path(__file__).with_name(".simple_browser_settings.json")


class SettingsDialog(QDialog):
    """Settings dialog for search engine, language, and quitting."""

    def __init__(self, parent):
        super().__init__(parent)
        self.browser = parent
        self.setWindowTitle("Settings")
        self.setGeometry(100, 100, 380, 280)

        layout = QVBoxLayout()

        search_label = QLabel("Default Search Engine:")
        layout.addWidget(search_label)

        self.search_combo = QComboBox()
        self.search_combo.addItems(["Google", "Yahoo", "Bing"])
        self.search_combo.setCurrentText(
            self.browser.get_search_engine_name(self.browser.default_search_engine)
        )
        layout.addWidget(self.search_combo)

        language_label = QLabel("Default Search Language:")
        layout.addWidget(language_label)

        self.language_combo = QComboBox()
        self.language_combo.addItems([name for name, _ in self.browser.language_options])
        self.language_combo.setCurrentText(
            self.browser.get_language_name(self.browser.default_language)
        )
        self.language_combo.currentTextChanged.connect(self.update_language_preview)
        layout.addWidget(self.language_combo)

        self.language_preview = QLabel(
            f"Current language: {self.browser.get_language_name(self.browser.default_language)}"
        )
        layout.addWidget(self.language_preview)

        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

        quit_btn = QPushButton("Quit")
        quit_btn.clicked.connect(self.quit_app)
        layout.addWidget(quit_btn)

        self.setLayout(layout)

    def update_language_preview(self, selected_name):
        """Update the visible current-language label."""
        self.language_preview.setText(f"Current language: {selected_name}")

    def save_settings(self):
        """Save the selected search engine and language."""
        search_engine_name = self.search_combo.currentText().lower()
        self.browser.default_search_engine = {
            "google": "google",
            "yahoo": "yahoo",
            "bing": "bing",
        }.get(search_engine_name, "google")

        selected_language_name = self.language_combo.currentText()
        self.browser.default_language = self.browser.language_code_map.get(
            selected_language_name, "en"
        )

        self.browser.save_settings()

        QMessageBox.information(
            self,
            "Settings",
            f"Default search engine set to {self.search_combo.currentText()}.\n"
            f"Default language set to {selected_language_name}.",
        )
        self.accept()

    def quit_app(self):
        """Ask before quitting the application."""
        msg = QMessageBox(self)
        msg.setWindowTitle("Quit SimpleBrowser?")
        msg.setText("Quit SimpleBrowser?")
        msg.setIcon(QMessageBox.Icon.Question)

        quit_button = msg.addButton("Quit", QMessageBox.ButtonRole.AcceptRole)
        msg.addButton("Don't Quit", QMessageBox.ButtonRole.RejectRole)

        msg.exec()

        if msg.clickedButton() == quit_button:
            QApplication.instance().quit()


class SimpleBrowser(QMainWindow):
    """Main browser window."""

    def __init__(self):
        super().__init__()

        self.default_search_engine = "google"
        self.default_language = "en"

        self.search_engines = {
            "google": "https://www.google.com/search?q=",
            "yahoo": "https://search.yahoo.com/search?p=",
            "bing": "https://www.bing.com/search?q=",
        }

        self.language_options = [
            ("English", "en"),
            ("German", "de"),
            ("French", "fr"),
            ("Spanish", "es"),
            ("Italian", "it"),
            ("Portuguese", "pt"),
            ("Dutch", "nl"),
            ("Russian", "ru"),
            ("Chinese", "zh-CN"),
            ("Japanese", "ja"),
        ]

        self.language_code_map = {name: code for name, code in self.language_options}
        self.load_settings()

        self.setWindowTitle("Simple Browser")
        self.setGeometry(100, 100, 1200, 800)

        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        url_layout = QHBoxLayout()
        url_layout.setContentsMargins(5, 5, 5, 5)
        url_layout.setSpacing(5)

        self.back_btn = QPushButton("←")
        self.back_btn.setMaximumWidth(40)
        self.back_btn.setMinimumHeight(48)
        self.back_btn.setFixedHeight(48)
        self.back_btn.clicked.connect(self.go_back)
        self.back_btn.setEnabled(False)
        url_layout.addWidget(self.back_btn)

        self.forward_btn = QPushButton("→")
        self.forward_btn.setMaximumWidth(40)
        self.forward_btn.setMinimumHeight(48)
        self.forward_btn.setFixedHeight(48)
        self.forward_btn.clicked.connect(self.go_forward)
        self.forward_btn.setEnabled(False)
        url_layout.addWidget(self.forward_btn)

        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Enter URL or search...")
        self.url_bar.setFont(QFont("Josefin Sans", 26))
        self.url_bar.setMinimumHeight(48)
        self.url_bar.setFixedHeight(48)
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        url_layout.addWidget(self.url_bar)

        settings_btn = QPushButton("⚙ Settings")
        settings_btn.setMaximumWidth(120)
        settings_btn.setMinimumHeight(48)
        settings_btn.setFixedHeight(48)
        settings_btn.clicked.connect(self.open_settings)
        url_layout.addWidget(settings_btn)

        url_container = QWidget()
        url_container.setLayout(url_layout)
        main_layout.addWidget(url_container)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.on_tab_changed)

        new_tab_btn = QPushButton("+")
        new_tab_btn.setMaximumWidth(40)
        new_tab_btn.clicked.connect(self.new_tab)

        tabs_layout = QHBoxLayout()
        tabs_layout.addWidget(self.tabs)
        tabs_layout.addWidget(new_tab_btn)
        tabs_layout.setContentsMargins(0, 0, 0, 0)
        tabs_layout.setSpacing(0)

        tabs_container = QWidget()
        tabs_container.setLayout(tabs_layout)
        main_layout.addWidget(tabs_container)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.new_tab()

    def load_settings(self):
        """Load saved search engine and language settings."""
        if not SETTINGS_FILE.exists():
            return

        try:
            with SETTINGS_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return

        if isinstance(data, dict):
            saved_engine = data.get("default_search_engine", "google")
            if saved_engine in self.search_engines:
                self.default_search_engine = saved_engine

            saved_language = data.get("default_language", "en")
            if saved_language in {code for _, code in self.language_options}:
                self.default_language = saved_language

    def save_settings(self):
        """Persist search engine and language settings."""
        data = {
            "default_search_engine": self.default_search_engine,
            "default_language": self.default_language,
        }
        with SETTINGS_FILE.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_search_engine_name(self, engine_code):
        """Convert engine code to display name."""
        return {
            "google": "Google",
            "yahoo": "Yahoo",
            "bing": "Bing",
        }.get(engine_code, "Google")

    def get_language_name(self, language_code):
        """Convert language code to display name."""
        for name, code in self.language_options:
            if code == language_code:
                return name
        return "English"

    def _create_web_view(self):
        """Create a web view for a new tab."""
        web_view = QWebEngineView()
        web_view.page().fullScreenRequested.connect(self.handle_fullscreen_request)
        web_view.urlChanged.connect(self.update_url_bar)
        web_view.loadFinished.connect(lambda _ok=None: self.update_navigation_buttons())
        return web_view

    def current_web_view(self):
        """Return the currently selected web view."""
        widget = self.tabs.currentWidget()
        if isinstance(widget, QWebEngineView):
            return widget
        return None

    def new_tab(self):
        """Create a new browser tab."""
        web_view = self._create_web_view()
        google_url = f"https://www.google.com/?hl={self.default_language}"
        web_view.setUrl(QUrl(google_url))
        tab_index = self.tabs.addTab(web_view, "New Tab")
        self.tabs.setCurrentIndex(tab_index)
        self.update_navigation_buttons()

    def close_tab(self, index):
        """Close a tab."""
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)
            self.update_navigation_buttons()
        else:
            QMessageBox.information(self, "Info", "Cannot close the last tab.")

    def on_tab_changed(self, _index):
        """Update navigation buttons when the active tab changes."""
        self.update_navigation_buttons()
        web_view = self.current_web_view()
        if web_view is not None:
            self.update_url_bar(web_view.url())

    def update_navigation_buttons(self):
        """Enable or disable Back/Forward based on current history."""
        web_view = self.current_web_view()
        if web_view is None:
            self.back_btn.setEnabled(False)
            self.forward_btn.setEnabled(False)
            return

        history = web_view.history()
        self.back_btn.setEnabled(history.canGoBack())
        self.forward_btn.setEnabled(history.canGoForward())

    def update_url_bar(self, url):
        """Update the URL bar to show the current page URL."""
        self.url_bar.blockSignals(True)
        self.url_bar.setText(url.toString())
        self.url_bar.blockSignals(False)

    def go_back(self):
        """Go back in the current tab's history."""
        web_view = self.current_web_view()
        if web_view is not None:
            web_view.back()
            self.update_navigation_buttons()

    def go_forward(self):
        """Go forward in the current tab's history."""
        web_view = self.current_web_view()
        if web_view is not None:
            web_view.forward()
            self.update_navigation_buttons()

    def _looks_like_url(self, text):
        """Return True if the input should be treated as a URL."""
        text = text.strip()
        if not text:
            return False
        if "://" in text:
            return True
        if text.startswith("www.") or text.startswith("localhost"):
            return True
        if "." in text and " " not in text:
            return True
        return False

    def _normalize_url(self, text):
        """Normalize user-entered URLs."""
        text = text.strip()
        if text.startswith(("http://", "https://", "ftp://")):
            return text
        return f"https://{text}"

    def _show_http_warning(self):
        """Show a warning dialog for insecure HTTP URLs."""
        msg = QMessageBox(self)
        msg.setWindowTitle("Security Warning")
        msg.setText(
            "This website uses HTTP which is not secure. It could be unsafe. Do you want to continue anyway?"
        )
        msg.setIcon(QMessageBox.Icon.Warning)

        enter_button = msg.addButton("Enter Anyway", QMessageBox.ButtonRole.AcceptRole)
        msg.addButton("Go Back", QMessageBox.ButtonRole.RejectRole)

        msg.exec()
        return msg.clickedButton() == enter_button

    def build_search_url(self, query):
        """Build a URL for the selected search engine."""
        if self.default_search_engine == "google":
            return f"https://www.google.com/search?q={quote_plus(query)}&hl={self.default_language}"
        if self.default_search_engine == "yahoo":
            return f"https://search.yahoo.com/search?p={quote_plus(query)}"
        if self.default_search_engine == "bing":
            return f"https://www.bing.com/search?q={quote_plus(query)}"
        return f"https://www.google.com/search?q={quote_plus(query)}&hl={self.default_language}"

    def navigate_to_url(self):
        """Navigate to the URL or search query entered in the URL bar."""
        query = self.url_bar.text().strip()
        if not query:
            return

        web_view = self.current_web_view()
        if web_view is None:
            return

        if query.lower().startswith("http://"):
            if not self._show_http_warning():
                return
            url = query
        elif query.lower().startswith("https://"):
            url = query
        elif self._looks_like_url(query):
            url = self._normalize_url(query)
        else:
            url = self.build_search_url(query)

        web_view.setUrl(QUrl(url))

    def open_settings(self):
        """Open the settings dialog."""
        dialog = SettingsDialog(self)
        dialog.exec()

    def handle_fullscreen_request(self, request):
        """Handle fullscreen requests from web pages."""
        request.accept()


def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)
    browser = SimpleBrowser()
    browser.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
