import sys
import json
import sqlite3
import bcrypt
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QLineEdit, QPushButton, QTabWidget, QDialog, QLabel, QComboBox,
    QMessageBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView

# Database and session paths
DB_PATH = Path.home() / ".simple_browser" / "auth.db"
SESSION_FILE = Path.home() / ".simple_browser" / "session.json"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

class AuthManager:
    """Manage user authentication and sessions."""
    
    def __init__(self):
        self.init_db()
    
    def init_db(self):
        """Initialize SQLite database for user authentication."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                default_search_engine TEXT DEFAULT 'google'
            )
        """)
        conn.commit()
        conn.close()
    
    def create_account(self, email, password):
        """Create a new user account."""
        if not email.endswith("@gmail.com"):
            return False, "Only @gmail.com addresses are allowed."
        
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, password_hash)
            )
            conn.commit()
            conn.close()
            return True, "Account created successfully."
        except sqlite3.IntegrityError:
            return False, "Email already registered."
    
    def login(self, email, password):
        """Authenticate user and return True/False."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        conn.close()
        
        if result and bcrypt.checkpw(password.encode(), result[0].encode()):
            self.save_session(email)
            return True
        return False
    
    def save_session(self, email):
        """Save session to file."""
        with open(SESSION_FILE, "w") as f:
            json.dump({"email": email}, f)
    
    def load_session(self):
        """Load session from file."""
        if SESSION_FILE.exists():
            try:
                with open(SESSION_FILE, "r") as f:
                    return json.load(f).get("email")
            except Exception:
                return None
        return None
    
    def logout(self):
        """Remove session."""
        if SESSION_FILE.exists():
            SESSION_FILE.unlink()
    
    def get_default_search_engine(self, email):
        """Retrieve user's default search engine."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT default_search_engine FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else "google"
    
    def set_default_search_engine(self, email, engine):
        """Update user's default search engine."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET default_search_engine = ? WHERE email = ?",
            (engine, email)
        )
        conn.commit()
        conn.close()


class SettingsDialog(QDialog):
    """Settings dialog for account and search engine preferences."""
    
    def __init__(self, parent, email, auth_manager):
        super().__init__(parent)
        self.email = email
        self.auth_manager = auth_manager
        self.setWindowTitle("Settings")
        self.setGeometry(100, 100, 400, 250)
        self.result_action = None
        
        layout = QVBoxLayout()
        
        # Email display
        email_label = QLabel(f"Logged in as: <b>{email}</b>")
        layout.addWidget(email_label)
        
        # Default search engine
        search_label = QLabel("Default Search Engine:")
        layout.addWidget(search_label)
        
        self.search_combo = QComboBox()
        self.search_combo.addItems(["google", "bing", "duckduckgo"])
        current_engine = auth_manager.get_default_search_engine(email)
        self.search_combo.setCurrentText(current_engine)
        layout.addWidget(self.search_combo)
        
        # Save button
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)
        
        # Logout button
        logout_btn = QPushButton("Logout")
        logout_btn.clicked.connect(self.logout_clicked)
        layout.addWidget(logout_btn)
        
        self.setLayout(layout)
    
    def save_settings(self):
        """Save search engine preference."""
        engine = self.search_combo.currentText()
        self.auth_manager.set_default_search_engine(self.email, engine)
        QMessageBox.information(self, "Success", f"Default search engine set to {engine}.")
        self.accept()
    
    def logout_clicked(self):
        """Handle logout."""
        self.auth_manager.logout()
        self.result_action = "logout"
        self.accept()


class LoginDialog(QDialog):
    """Login and account creation dialog."""
    
    def __init__(self, parent, auth_manager):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.authenticated_email = None
        self.setWindowTitle("Simple Browser - Login")
        self.setGeometry(100, 100, 400, 250)
        
        layout = QVBoxLayout()
        
        title = QLabel("Simple Browser")
        title_font = QFont("Google Sans", 20, QFont.Weight.Bold)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Email input
        email_label = QLabel("Email (@gmail.com):")
        layout.addWidget(email_label)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("your-email@gmail.com")
        layout.addWidget(self.email_input)
        
        # Password input
        password_label = QLabel("Password:")
        layout.addWidget(password_label)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self.login)
        button_layout.addWidget(login_btn)
        
        create_btn = QPushButton("Create Account")
        create_btn.clicked.connect(self.create_account)
        button_layout.addWidget(create_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def login(self):
        """Handle login."""
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        if not email or not password:
            QMessageBox.warning(self, "Error", "Please enter email and password.")
            return
        
        if self.auth_manager.login(email, password):
            self.authenticated_email = email
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Invalid email or password.")
    
    def create_account(self):
        """Handle account creation."""
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        if not email or not password:
            QMessageBox.warning(self, "Error", "Please enter email and password.")
            return
        
        success, message = self.auth_manager.create_account(email, password)
        if success:
            QMessageBox.information(self, "Success", message)
            self.email_input.clear()
            self.password_input.clear()
        else:
            QMessageBox.warning(self, "Error", message)


class SimpleBrowser(QMainWindow):
    """Main browser window."""
    
    def __init__(self, email):
        super().__init__()
        self.email = email
        self.auth_manager = AuthManager()
        self.search_engines = {
            "google": "https://www.google.com/search?q=",
            "bing": "https://www.bing.com/search?q=",
            "duckduckgo": "https://duckduckgo.com/?q="
        }
        
        self.setWindowTitle("Simple Browser")
        self.setGeometry(100, 100, 1200, 800)
        
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Tabs widget (at the top)
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        
        # Add new tab button
        new_tab_btn = QPushButton("+")
        new_tab_btn.setMaximumWidth(40)
        new_tab_btn.clicked.connect(self.new_tab)
        
        tabs_layout = QHBoxLayout()
        tabs_layout.addWidget(self.tabs)
        tabs_layout.addWidget(new_tab_btn)
        tabs_layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs_container = QWidget()
        self.tabs_container.setLayout(tabs_layout)
        
        main_layout.addWidget(self.tabs_container)
        
        # Search bar and settings button (below tabs)
        search_layout = QHBoxLayout()
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search or enter URL...")
        search_font = QFont("Google Sans", 12)
        self.search_bar.setFont(search_font)
        self.search_bar.returnPressed.connect(self.search)
        search_layout.addWidget(self.search_bar)
        
        settings_btn = QPushButton("⚙ Settings")
        settings_btn.setMaximumWidth(120)
        settings_btn.clicked.connect(self.open_settings)
        search_layout.addWidget(settings_btn)
        
        self.search_layout_widget = QWidget()
        self.search_layout_widget.setLayout(search_layout)
        main_layout.addWidget(self.search_layout_widget)
        
        # WebEngine view
        self.web_view = QWebEngineView()
        main_layout.addWidget(self.web_view)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Create first tab
        self.new_tab()
        
        # Enable fullscreen support
        self.web_view.page().fullScreenRequested.connect(self.handle_fullscreen_request)
    
    def new_tab(self):
        """Create a new browser tab."""
        web_view = QWebEngineView()
        web_view.setUrl(QUrl("https://www.google.com"))
        web_view.page().fullScreenRequested.connect(self.handle_fullscreen_request)
        tab_index = self.tabs.addTab(web_view, "New Tab")
        self.tabs.setCurrentIndex(tab_index)
        self.web_view = web_view
    
    def close_tab(self, index):
        """Close a tab."""
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)
        else:
            QMessageBox.information(self, "Info", "Cannot close the last tab.")
    
    def search(self):
        """Search or navigate."""
        query = self.search_bar.text().strip()
        if not query:
            return
        
        if query.startswith("http://") or query.startswith("https://"):
            url = query
        else:
            engine = self.auth_manager.get_default_search_engine(self.email)
            url = self.search_engines.get(engine, self.search_engines["google"]) + query
        
        self.web_view.setUrl(QUrl(url))
        self.search_bar.clear()
    
    def open_settings(self):
        """Open settings dialog."""
        settings_dialog = SettingsDialog(self, self.email, self.auth_manager)
        if settings_dialog.exec() == QDialog.DialogCode.Accepted:
            if settings_dialog.result_action == "logout":
                QMessageBox.information(self, "Logged Out", "You have been logged out.")
                self.close()
                sys.exit(0)
    
    def handle_fullscreen_request(self, request):
        """Handle fullscreen requests from web content (e.g., YouTube)."""
        if request.toggleOn():
            self.showFullScreen()
            self.tabs_container.hide()
            self.search_layout_widget.hide()
        else:
            self.showNormal()
            self.tabs_container.show()
            self.search_layout_widget.show()
        
        request.accept()


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    auth_manager = AuthManager()
    
    # Check for existing session
    email = auth_manager.load_session()
    
    if not email:
        # Show login dialog
        login_dialog = LoginDialog(None, auth_manager)
        if login_dialog.exec() != QDialog.DialogCode.Accepted:
            sys.exit(0)
        email = login_dialog.authenticated_email
    
    # Open browser
    browser = SimpleBrowser(email)
    browser.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
