import sys
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtWidgets import QApplication, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QTabWidget, QToolBar, QWidget, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView


class OpenSourceBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SimpleBrowser")
        self.resize(1400, 900)
        self.home_url = "https://www.google.com/?hl=en"

        self.address_bar = QLineEdit(self)
        self.address_bar.setPlaceholderText("Search or enter address")
        self.address_bar.returnPressed.connect(self.navigate)
        self.address_bar.setStyleSheet(
            "QLineEdit {"
            "font-family: 'Adwaita Sans', 'Helvetica Neue', Arial, sans-serif;"
            "font-size: 13px;"
            "padding: 8px 14px;"
            "border: 1px solid #4e5d7a;"
            "border-radius: 18px;"
            "background: #202832;"
            "color: #f2f5fa;"
            "margin-left: 12px;"
            "}" 
            "QLineEdit:focus {"
            "border: 1px solid #5b87ff;"
            "background: #1c2530;"
            "}"
        )

        self.tabs = QTabWidget(self)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.tab_changed)
        self.tabs.setDocumentMode(True)
        self.tabs.setElideMode(Qt.TextElideMode.ElideRight)

        self.tab_count_label = QLabel("1 tab")
        self.tab_count_label.setStyleSheet(
            "color: #a8b7d0; font-size: 12px; margin-left: 12px;"
        )

        self.add_tab(self.home_url)

        back_button = QPushButton("◀")
        back_button.clicked.connect(self.navigate_back)
        forward_button = QPushButton("▶")
        forward_button.clicked.connect(self.navigate_forward)
        reload_button = QPushButton("↻")
        reload_button.clicked.connect(self.navigate_reload)
        home_button = QPushButton("⌂")
        home_button.clicked.connect(self.navigate_home)
        new_tab_button = QPushButton("+")
        new_tab_button.clicked.connect(self.add_new_tab)
        new_tab_button.setToolTip("Open a new tab")
        self.tab_count_label = QLabel("1 tab")
        self.tab_count_label.setStyleSheet(
            "color: #a8b7d0; font-size: 12px; margin-left: 12px;"
        )

        for button in (back_button, forward_button, reload_button, home_button, new_tab_button):
            button.setFixedSize(30, 30)
            button.setStyleSheet(
                "QPushButton {"
                "border: none;"
                "border-radius: 15px;"
                "background: #2a3240;"
                "color: #e5ecff;"
                "font-weight: bold;"
                "}" 
                "QPushButton:hover {"
                "background: #3c4e6c;"
                "}"
            )

        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setStyleSheet(
            "QToolBar { background: #171f2b; border-bottom: 1px solid #2f3e53; padding: 8px; }"
        )
        toolbar.addWidget(back_button)
        toolbar.addWidget(forward_button)
        toolbar.addWidget(reload_button)
        toolbar.addWidget(home_button)
        toolbar.addWidget(new_tab_button)
        toolbar.addWidget(self.tab_count_label)
        toolbar.addWidget(self.address_bar)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(toolbar)
        layout.addWidget(self.tabs)
        self.setCentralWidget(container)

        self.view = self.current_view()

    def current_view(self) -> QWebEngineView:
        return self.tabs.currentWidget()

    def update_title(self, title: str):
        self.setWindowTitle(
            f"{title} - SimpleBrowser" if title else "SimpleBrowser"
        )

    def add_tab(self, url: str, label: str = "New Tab"):
        view = QWebEngineView(self)
        view.setStyleSheet("background: #0f1620;")
        view.setHtml(
            "<html><body style='background:#0f1620;color:#e5ecff;display:flex;align-items:center;justify-content:center;height:100%;margin:0;'>"
            "<div style='text-align:center;font-family:sans-serif;font-size:18px;'>Loading SimpleBrowser...</div>"
            "</body></html>",
            QUrl("about:blank"),
        )
        view.setUrl(QUrl(url))
        index = self.tabs.addTab(view, label)
        self.tabs.setCurrentIndex(index)
        self.update_tab_count()
        view.urlChanged.connect(lambda qurl, view=view: self.on_tab_url_changed(qurl, view))
        view.titleChanged.connect(lambda title, view=view: self.on_tab_title_changed(title, view))

    def add_new_tab(self):
        self.add_tab(self.home_url)

    def close_tab(self, index: int):
        if self.tabs.count() == 1:
            return
        self.tabs.removeTab(index)
        self.update_tab_count()

    def tab_changed(self, index: int):
        if index < 0:
            return
        self.view = self.current_view()
        self.address_bar.setText(self.view.url().toString())
        self.view.urlChanged.connect(self.update_address)
        self.view.titleChanged.connect(lambda title: self.update_title(title))

    def on_tab_url_changed(self, qurl, view):
        if view is self.current_view():
            self.address_bar.setText(qurl.toString())

    def on_tab_title_changed(self, title, view):
        index = self.tabs.indexOf(view)
        if index != -1:
            self.tabs.setTabText(index, title or "New Tab")
        if view is self.current_view():
            self.update_title(title)

    def navigate_back(self):
        self.current_view().back()

    def navigate_forward(self):
        self.current_view().forward()

    def navigate_reload(self):
        self.current_view().reload()

    def navigate_home(self):
        self.current_view().setUrl(QUrl(self.home_url))

    def update_tab_count(self):
        count = self.tabs.count()
        self.tab_count_label.setText(f"{count} tab{'s' if count != 1 else ''}")

    def warn_insecure(self, url: str) -> bool:
        if url.startswith("http://"):
            message = (
                "You are navigating to an insecure HTTP site. "
                "Data sent or received on this page is not encrypted. "
                "Proceed only if you trust the site."
            )
            reply = QMessageBox.warning(
                self,
                "Insecure Connection",
                message,
                QMessageBox.StandardButton.Ok,
                QMessageBox.StandardButton.Cancel,
            )
            return reply == QMessageBox.StandardButton.Ok
        return True

    def navigate(self):
        url = self.address_bar.text().strip()
        if not url:
            return
        if "://" not in url:
            url = "https://" + url
        if url.startswith("http://") and not self.warn_insecure(url):
            return
        self.view.setUrl(QUrl(url))

    def update_address(self, qurl):
        self.address_bar.setText(qurl.toString())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OpenSourceBrowser()
    window.show()
    sys.exit(app.exec())
