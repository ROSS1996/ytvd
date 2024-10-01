# main.py

import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from modules.download_manager import DownloadManager
from modules.main_window import BrowserWindow

def main():
    # Create the application instance
    app = QApplication(sys.argv)

    # Check internet connection before launching the application
    if not DownloadManager.is_internet_connected():
        QMessageBox.critical(None, "No Internet Connection", "You are not connected to the internet.")
        return  # Exit if no internet connection

    # Create and show the main application window
    window = BrowserWindow()
    window.showMaximized()  # Use showMaximized() here

    # Start the event loop
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
