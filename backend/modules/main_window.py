import sys
from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel,
    QMessageBox, QHBoxLayout, QComboBox, QProgressBar, QSizePolicy, QApplication
)
from PyQt6.QtCore import QUrl, QTimer, pyqtSlot, QThread, pyqtSignal, QObject
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEngineProfile
from .custom_web_engine_page import CustomWebEnginePage
from .download_manager import DownloadManager
import asyncio
from .constants import CACHE_DIRECTORY


class DownloadWorker(QObject):
    """Worker para gerenciar o download em uma thread separada."""
    progress = pyqtSignal(int)
    finished = pyqtSignal(str, bool)  # mensagem, é_erro

    def __init__(self, download_manager, youtube_url, format_type, quality):
        super().__init__()
        self.download_manager = download_manager
        self.youtube_url = youtube_url
        self.format_type = format_type
        self.quality = quality

    def run(self):
        """Lida com o processo de download."""
        try:
            response, status_code = self.download_manager.handle_download_request(
                self.youtube_url, self.format_type, self.quality, self.update_progress
            )
            if status_code != 202:
                message = response.get("error", "Falha no download!")
                self.finished.emit(message, True)
            else:
                message = f"Download iniciado: {response['title']}"
                self.finished.emit(message, False)
        except Exception as e:
            self.finished.emit(str(e), True)

    def update_progress(self, percentage):
        """Atualiza o sinal de progresso."""
        self.progress.emit(percentage)


class DownloadManagerHandler:
    """Manipula solicitações de download e confirmações do usuário."""

    def __init__(self, download_manager, parent):
        self.download_manager = download_manager
        self.parent = parent

    def request_download(self, youtube_url, format_type, quality):
        """Pergunta ao usuário por confirmação antes de iniciar o download."""
        # Cria a mensagem de confirmação
        msg_box = QMessageBox(self.parent)
        msg_box.setWindowTitle(f'Confirmação de Download {format_type.capitalize()}')
        msg_box.setText(f'Você deseja baixar este {format_type}?\n{youtube_url}')
        
        # Define os botões com textos personalizados
        btn_sim = msg_box.addButton('Sim', QMessageBox.ButtonRole.YesRole)
        btn_nao = msg_box.addButton('Não', QMessageBox.ButtonRole.NoRole)
        
        # Exibe a caixa de diálogo
        msg_box.exec()

        # Verifica a resposta do usuário
        if msg_box.clickedButton() == btn_sim:
            self.parent.start_download(youtube_url, format_type, quality)
class BrowserWindow(QMainWindow):
    """Janela Principal do Navegador com recursos de download de vídeos do YouTube."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube")
        self.download_manager = DownloadManager()
        self.download_handler = DownloadManagerHandler(
            self.download_manager, self)
        self.download_thread = None
        self.download_worker = None

        self.home_url = "https://www.youtube.com"
        self.init_ui()  # Inicializa a interface do usuário apenas uma vez
        self.init_timer()  # Move a inicialização do timer aqui
        self.apply_styles()
        self.showMaximized()

    def init_ui(self):
        """Inicializa o layout e os widgets da interface do usuário."""
        self.init_browser()  # Inicializa as configurações da visualização do navegador
        self.setup_buttons()  # Agora você pode configurar os botões com segurança
        self.setup_progress_bar()
        self.setup_layouts()  # Agora é seguro configurar layouts

    def setup_layouts(self):
        """Configura o layout principal e a exibição da URL."""
        main_layout = QVBoxLayout()
        url_layout = QHBoxLayout()

        self.url_label = QLabel("URL")
        self.url_content = QLabel()
        self.url_content.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        url_layout.addWidget(self.url_label)
        url_layout.addWidget(self.url_content)

        main_layout.addLayout(url_layout)
        main_layout.addWidget(self.browser_view)
        main_layout.addLayout(self.setup_button_layout())
        main_layout.addWidget(self.progress_bar)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def setup_buttons(self):
        """Inicializa os botões de navegação e download."""
        self.back_button = self.create_nav_button(
            "Voltar", "go-previous", self.browser_view.back)
        self.forward_button = self.create_nav_button(
            "Avançar", "go-next", self.browser_view.forward)
        self.refresh_button = self.create_nav_button(
            "Atualizar", "view-refresh", self.browser_view.reload)
        self.home_button = self.create_nav_button(
            "Início", "go-home", self.navigate_home)

        self.download_video_button = self.create_download_button(
            "Baixar Vídeo", self.handle_video_download_click)
        self.download_audio_button = self.create_download_button(
            "Baixar Áudio", self.handle_audio_download_click)

        self.quality_combo = QComboBox()
        self.quality_combo.addItems(['720p', '1080p', '480p', '360p'])

    def setup_progress_bar(self):
        """Configura a barra de progresso do download."""
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Progresso do Download: %p%")

    def setup_button_layout(self):
        """Configura o layout dos botões da janela."""
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.back_button)
        button_layout.addWidget(self.forward_button)
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.home_button)
        button_layout.addWidget(self.download_video_button)
        button_layout.addWidget(self.download_audio_button)
        button_layout.addWidget(self.quality_combo)
        return button_layout

    def create_nav_button(self, text, icon_name, slot):
        """Método utilitário para criar um botão de navegação."""
        button = QPushButton(text)
        button.setIcon(QIcon.fromTheme(icon_name))
        button.clicked.connect(slot)
        return button

    def create_download_button(self, text, slot):
        """Método utilitário para criar um botão de download."""
        button = QPushButton(text)
        button.setEnabled(False)
        button.clicked.connect(slot)
        return button

    def init_browser(self):
        """Inicializa as configurações da visualização do navegador."""
        self.browser_view = QWebEngineView(self)
        profile = self.browser_view.page().profile()
        cache_path = CACHE_DIRECTORY

        profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
        profile.setHttpCacheMaximumSize(
            1024 * 1024 * 100)  # Tamanho do cache: 100 MB
        profile.setCachePath(cache_path)

        # Ativa a aceleração de hardware, rolagem suave e outros recursos
        browser_settings = self.browser_view.settings()
        browser_settings.setAttribute(
            QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        browser_settings.setAttribute(
            QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)
        browser_settings.setAttribute(
            QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        browser_settings.setAttribute(
            QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        browser_settings.setAttribute(
            QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)

        self.browser_view.setUrl(QUrl(self.home_url))

    def init_timer(self):
        """Inicializa o timer de verificação da URL."""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_url_periodically)
        self.timer.start(2000)

    def check_url_periodically(self):
        """Verifica a URL atual e atualiza os estados dos botões de download."""
        current_url = self.browser_view.url().toString()
        self.update_url_label(current_url)

        is_youtube_url = current_url.startswith(
            "https://www.youtube.com/watch?v=") or current_url.startswith("https://youtu.be/")
        self.enable_download_buttons(is_youtube_url)
        if not is_youtube_url:
            self.setWindowTitle("YouTube")

    def update_url_label(self, url):
        """Atualiza o rótulo de exibição da URL."""
        self.url_content.setText(url)

    def enable_download_buttons(self, enable):
        """Habilita ou desabilita os botões de download."""
        self.download_video_button.setEnabled(enable)
        self.download_audio_button.setEnabled(enable)

    def start_download(self, youtube_url, format_type, quality):
        """Inicia o download em uma thread separada."""
        if self.download_thread:
            self.terminate_download_thread()

        self.download_thread = QThread()
        self.download_worker = DownloadWorker(
            self.download_manager, youtube_url, format_type, quality)
        self.download_worker.moveToThread(self.download_thread)

        self.download_thread.started.connect(self.download_worker.run)
        self.download_worker.finished.connect(self.on_download_finished)
        self.download_worker.progress.connect(self.update_progress)

        self.download_thread.start()

    def terminate_download_thread(self):
        """Termina a thread de download se estiver em execução."""
        if self.download_thread:
            self.download_thread.quit()
            self.download_thread.wait()

    def on_download_finished(self, message, is_error):
        """Lida com a conclusão do download."""
        self.terminate_download_thread()
        self.download_worker = None
        self.show_download_status(message, is_error)

    def show_download_status(self, message, is_error=False):
        """Exibe uma mensagem de status para o download."""
        if is_error:
            QMessageBox.critical(self, "Erro no Download", message)
        else:
            QMessageBox.information(self, "Download Iniciado", message)

    def closeEvent(self, event):
        """Lida com a limpeza quando a janela é fechada."""
        self.terminate_download_thread()
        event.accept()

    @pyqtSlot()
    def handle_video_download_click(self):
        """Handle the click event for downloading videos."""
        current_url = self.browser_view.url().toString()
        quality = self.quality_combo.currentText().replace(
            'p', '')  # Remove 'p' to get numeric value
        self.download_handler.request_download(current_url, "video", quality)

    @pyqtSlot()
    def handle_audio_download_click(self):
        """Handle the click event for downloading audio."""
        current_url = self.browser_view.url().toString()
        self.download_handler.request_download(current_url, "audio", "best")

    @pyqtSlot(int)
    def update_progress(self, percentage):
        """Update the progress bar with the current download percentage."""
        self.progress_bar.setValue(percentage)

    @pyqtSlot()
    def navigate_home(self):
        """Navigate back to the home URL."""
        self.browser_view.setUrl(QUrl(self.home_url))

    def apply_styles(self):
        """Apply custom styles to the application."""
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
                background-color: #e0e0e0;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 20px;
            }
        """)

        font = QFont("Segoe UI", 10)
        self.setFont(font)

        # Style URL labels
        for widget in [self.url_label, self.url_content]:
            widget.setStyleSheet("""
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
            """)

        # Style download buttons
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
        for button in [self.back_button, self.forward_button, self.refresh_button, self.home_button]:
            button.setStyleSheet(nav_button_style)

    def focusInEvent(self, event):
        """Repaint browser view on focus in."""
        self.browser_view.setVisible(False)
        self.browser_view.setVisible(True)
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        """Hide browser view on focus out."""
        self.browser_view.setVisible(False)
        super().focusOutEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BrowserWindow()
    window.show()
    sys.exit(app.exec())
