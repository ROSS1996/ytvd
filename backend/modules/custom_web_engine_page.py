import re
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtCore import pyqtSignal

# Regex for detecting YouTube videos
YOUTUBE_VIDEO_REGEX = r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.?be/)[\w-]{11}$'


class URLHandler:
    """Handles URL validation and title fetching for YouTube links."""
    
    def is_youtube_url(self, url: str) -> bool:
        """Check if the given URL is a valid YouTube video URL."""
        return re.match(YOUTUBE_VIDEO_REGEX, url) is not None


class TitleFetcher:
    """Fetches the title of a web page."""
    
    def __init__(self, page: QWebEnginePage):
        self.page = page

    def fetch_title(self, callback):
        """Executes JavaScript to get the page title."""
        self.page.runJavaScript("document.title", callback)


class CustomWebEnginePage(QWebEnginePage):
    title_updated = pyqtSignal(str)

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.url_handler = URLHandler()
        self.title_fetcher = TitleFetcher(self)

        # Connect to the loadFinished signal to ensure we fetch the title only after the page is loaded
        self.loadFinished.connect(self.on_load_finished)

    def on_load_finished(self, success):
        """Fetch title once the page has finished loading."""
        if success:
            youtube_url = self.main_window.browser_view.url().toString()
            if self.url_handler.is_youtube_url(youtube_url):
                print(f"Fetching title for: {youtube_url}")  # Debug print
                self.title_fetcher.fetch_title(self.update_title)  # Use TitleFetcher to get the title

    def acceptNavigationRequest(self, url, _type, is_main_frame):
        youtube_url = url.toString()
        self.main_window.update_url_label(youtube_url)

        if self.url_handler.is_youtube_url(youtube_url):
            self.main_window.enable_download_buttons(True)
        else:
            self.main_window.enable_download_buttons(False)
            self.main_window.set_window_title("YouTube Browser with Download Options")  # Default title

        return super().acceptNavigationRequest(url, _type, is_main_frame)

    def update_title(self, title):
        """Emit the fetched title or a default if none is valid."""
        print(f"Page title fetched: {title}")  # Debug print
        if title and isinstance(title, str) and len(title) > 0:
            self.title_updated.emit(title)  # Emit the title via the signal
        else:
            print("No valid title fetched, setting to default.")  # Debug print
            self.title_updated.emit("YouTube Browser with Download Options")  # Fallback title
