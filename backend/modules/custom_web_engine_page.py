import re
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtCore import pyqtSignal

# Compila o padrão de regex uma vez
YOUTUBE_VIDEO_REGEX = re.compile(r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.?be/)[\w-]{11}$')

class URLHandler:
    """Gerencia a validação de URLs para links do YouTube."""
    
    @staticmethod
    def is_youtube_url(url: str) -> bool:
        """Verifica se a URL fornecida é um URL de vídeo do YouTube válido."""
        return bool(YOUTUBE_VIDEO_REGEX.match(url))

class TitleFetcher:
    """Obtém o título de uma página da web."""
    
    def __init__(self, page: QWebEnginePage):
        self.page = page

    def fetch_title(self, callback):
        """Executa JavaScript para obter o título da página."""
        self.page.runJavaScript("document.title", callback)

class CustomWebEnginePage(QWebEnginePage):
    title_updated = pyqtSignal(str)

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.url_handler = URLHandler()
        self.title_fetcher = TitleFetcher(self)

        # Conecta ao sinal loadFinished para buscar o título após o carregamento da página
        self.loadFinished.connect(self.on_load_finished)

    def on_load_finished(self, success):
        """Busca o título assim que a página termina de carregar."""
        if success:
            youtube_url = self.main_window.browser_view.url().toString()
            if self.url_handler.is_youtube_url(youtube_url):
                print(f"Buscando título para: {youtube_url}")  # Impressão de depuração
                self.title_fetcher.fetch_title(lambda title: self.update_title(title))

    def acceptNavigationRequest(self, url, _type, is_main_frame):
        youtube_url = url.toString()
        self.main_window.update_url_label(youtube_url)

        # Habilita/desabilita os botões de download com base na validade da URL
        self.main_window.enable_download_buttons(self.url_handler.is_youtube_url(youtube_url))

        # Define o título padrão se não for uma URL do YouTube
        if not self.url_handler.is_youtube_url(youtube_url):
            self.main_window.set_window_title("YouTube")

        return super().acceptNavigationRequest(url, _type, is_main_frame)

    def update_title(self, title):
        """Emite o título obtido ou um padrão se nenhum for válido."""
        print(f"Título da página obtido: {title}")  # Impressão de depuração
        # Emite o título ou fallback
        self.title_updated.emit(title if title else "YouTube")
