import sys
import re
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, 
                             QMessageBox, QHBoxLayout, QComboBox, QProgressBar, QSizePolicy, QApplication)
from PyQt6.QtCore import QUrl, QTimer, pyqtSlot
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QIcon, QFont
from .custom_web_engine_page import CustomWebEnginePage
from .download_manager import DownloadManager

class DownloadManagerHandler:
    """Handles download requests and provides a confirmation dialog."""
    
    def __init__(self, download_manager, parent):
        self.download_manager = download_manager
        self.parent = parent

    def request_download(self, youtube_url, format_type, quality):
        reply = QMessageBox.question(
            self.parent,
            f'Download {format_type.capitalize()} Confirmation',
            f'Do you want to download this {format_type}?\n{youtube_url}',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            response, status_code = self.download_manager.handle_download_request(
                youtube_url, format_type, quality, self.parent.update_progress
            )

            if status_code == 202:  # Download started successfully
                message = f"Download started: {response['title']}"
                self.parent.show_download_status(message)
            else:  # Error in starting the download
                error_message = response.get("error", "Unknown error occurred.")
                self.parent.show_download_status(error_message, is_error=True)


class BrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Browser with Download Options")
        # Initialize the download manager
        self.download_manager = DownloadManager()  # Make sure you have a DownloadManager defined somewhere
        self.download_handler = DownloadManagerHandler(self.download_manager, self)  # Create the handler

        # Get the screen geometry to set the window size
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        margin = 20  # Set a margin for the window

        # Calculate the size for the window
        width = int(screen_geometry.width() * 0.7)  # 70% of available width
        height = int(screen_geometry.height() * 0.7)  # 70% of available height

        # Set the geometry with margin
        self.setGeometry(
            screen_geometry.x() + margin,   # Margin on the left
            screen_geometry.y() + margin,   # Margin on the top
            width,                           # Width
            height                           # Height
        )

        self.home_url = "https://www.youtube.com"  # Set home URL

        self.init_ui()
        self.init_browser()
        self.init_timer()
        self.apply_styles()

        # Show the window maximized
        self.showMaximized()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # URL bar layout
        url_layout = QHBoxLayout()
        self.url_label = QLabel("URL")
        self.url_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.url_content = QLabel()
        self.url_content.setWordWrap(False)
        self.url_content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        url_layout.addWidget(self.url_label)
        url_layout.addWidget(self.url_content)

        self.browser_view = QWebEngineView(self)
        self.progress_bar = QProgressBar()
        self.download_video_button = QPushButton("Download Video")
        self.download_audio_button = QPushButton("Download Audio")
        self.quality_combo = QComboBox()

        # Navigation buttons
        self.back_button = QPushButton("Voltar")
        self.back_button.setIcon(QIcon.fromTheme("go-previous"))
        self.forward_button = QPushButton("Avançar")
        self.forward_button.setIcon(QIcon.fromTheme("go-next"))
        self.refresh_button = QPushButton("Atualizar")
        self.refresh_button.setIcon(QIcon.fromTheme("view-refresh"))
        self.home_button = QPushButton("Início")
        self.home_button.setIcon(QIcon.fromTheme("go-home"))

        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Progresso do Download: %p%")

        self.download_video_button.setEnabled(False)
        self.download_video_button.clicked.connect(self.handle_video_download_click)

        self.download_audio_button.setEnabled(False)
        self.download_audio_button.clicked.connect(self.handle_audio_download_click)

        self.quality_combo.addItems(['720p', '1080p', '480p', '360p'])

        # Connect navigation buttons
        self.back_button.clicked.connect(self.browser_view.back)
        self.forward_button.clicked.connect(self.browser_view.forward)
        self.refresh_button.clicked.connect(self.browser_view.reload)
        self.home_button.clicked.connect(self.navigate_home)

        # Layout setup
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.back_button)
        button_layout.addWidget(self.forward_button)
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.home_button)
        button_layout.addWidget(self.download_video_button)
        button_layout.addWidget(self.download_audio_button)
        button_layout.addWidget(self.quality_combo)

        main_layout.addLayout(url_layout)
        main_layout.addWidget(self.browser_view)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.progress_bar)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def init_browser(self):
        self.browser_view.setUrl(QUrl(self.home_url))

    def init_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_url_periodically)
        self.timer.start(2000)

    def resizeEvent(self, event):
        # If the window is maximized, prevent any resize changes
        if self.isMaximized():
            self.setGeometry(self.geometry())  # Keep current geometry
        super().resizeEvent(event)  # Call base class method

    def set_window_title(self, title):
        self.setWindowTitle(title)

    def update_url_label(self, url):
        self.url_content.setText(url)

    def enable_download_buttons(self, enable):
        self.download_video_button.setEnabled(enable)
        self.download_audio_button.setEnabled(enable)

    def check_url_periodically(self):
        current_url = self.browser_view.url().toString()
        self.update_url_label(current_url)

        if re.match(r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.?be/)[\w-]{11}$', current_url):
            self.enable_download_buttons(True)
        else:
            self.enable_download_buttons(False)
            self.set_window_title("YouTube Browser with Download Options")

    def show_download_status(self, message, is_error=False):
        if is_error:
            QMessageBox.critical(self, "Download Error", message)
        else:
            QMessageBox.information(self, "Download Started", message)

    @pyqtSlot()
    def handle_video_download_click(self):
        current_url = self.browser_view.url().toString()
        quality = self.quality_combo.currentText().replace('p', '')
        self.download_handler.request_download(current_url, "video", quality)

    @pyqtSlot()
    def handle_audio_download_click(self):
        current_url = self.browser_view.url().toString()
        self.download_handler.request_download(current_url, "audio", "best")

    @pyqtSlot(int)
    def update_progress(self, percentage):
        self.progress_bar.setValue(percentage)

    @pyqtSlot()
    def navigate_home(self):
        self.browser_view.setUrl(QUrl(self.home_url))

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QLabel {
                font-size: 14px;
                color: #333;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                text-align: center;
                text-decoration: none;
                font-size: 14px;
                margin: 4px 2px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QComboBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
                min-width: 6em;
            }
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                background-color: #e0e0e0;  /* Background color of the bar */
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;  /* Fill color */
                width: 20px;  /* Width of the chunk */
            }
        """)

        # Set a modern font
        font = QFont("Segoe UI", 10)
        self.setFont(font)

        # Style specific widgets
        self.url_label.setStyleSheet("""
            background-color: white;
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 5px;
        """)

        self.url_content.setStyleSheet("""
            background-color: white;
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 5px;
        """)

        self.download_video_button.setStyleSheet("""
            QPushButton {
                background-color: #008CBA;
            }
            QPushButton:disabled {
                background-color: #80C5DA;
                color: #CCCCCC;
            }
        """)

        self.download_audio_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
            }
            QPushButton:disabled {
                background-color: #F9A19A;
                color: #CCCCCC;
            }
        """)

        # Style navigation buttons
        nav_button_style = """
            QPushButton {
                background-color: #E0E0E0;
                color: #333333;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #D0D0D0;
            }
            QPushButton:pressed {
                background-color: #C0C0C0;
            }
        """
        self.back_button.setStyleSheet(nav_button_style)
        self.forward_button.setStyleSheet(nav_button_style)
        self.refresh_button.setStyleSheet(nav_button_style)
        self.home_button.setStyleSheet(nav_button_style)
