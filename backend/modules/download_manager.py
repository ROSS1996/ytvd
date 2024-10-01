import os
import threading
import socket
import re
from queue import Queue
from typing import Dict, Any
import requests
import eyed3
import yt_dlp
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
from .constants import DOWNLOAD_DIRECTORY, OUTPUT_FORMATS, MAX_CONCURRENT_DOWNLOADS

# Inicializa o console Rich
console = Console()

# Cria o diretório de download se não existir
os.makedirs(DOWNLOAD_DIRECTORY, exist_ok=True)

# Regex para detectar vídeos do YouTube
YOUTUBE_VIDEO_REGEX = r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.?be/)[\w-]{11}$'


class DownloadManager:
    def __init__(self):
        self.active_downloads: Dict[str, Dict[str, Any]] = {}
        self.download_queue = Queue()
        self.lock = threading.Lock()

    @staticmethod
    def is_internet_connected() -> bool:
        """Verifica se a internet está conectada."""
        try:
            # Realiza uma rápida resolução DNS em vez de estabelecer uma conexão TCP
            socket.gethostbyname("www.google.com")
            return True
        except socket.gaierror:
            return False

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitiza um nome de arquivo removendo caracteres ilegais."""
        reserved_chars_pattern = r'[<>:"/\\|?*]'
        return re.sub(r'_+', '_', re.sub(reserved_chars_pattern, '_', filename))

    @staticmethod
    def add_metadata_to_mp3(file_path: str, video_info: Dict[str, Any]):
        """Adiciona metadados ao arquivo MP3 baixado."""
        try:
            audiofile = eyed3.load(file_path)
            if not audiofile or not audiofile.tag:
                audiofile.initTag()

            audiofile.tag.title = video_info.get("title", "Título Desconhecido")
            audiofile.tag.artist = video_info.get("uploader", "Artista Desconhecido")
            audiofile.tag.album = "Download do YouTube"
            audiofile.tag.year = video_info.get("upload_date", "")[:4]
            audiofile.tag.comments.set(video_info.get("description", ""))

            # Baixa a miniatura em uma thread separada
            thumbnail_url = video_info.get("thumbnail")
            if thumbnail_url:
                threading.Thread(target=DownloadManager.download_thumbnail, args=(thumbnail_url, audiofile)).start()

            audiofile.tag.save()
            console.print(Panel(f"[bold green]Metadados adicionados a {file_path}[/bold green]"))
        except Exception as e:
            console.print(Panel(f"[bold red]Erro ao adicionar metadados a {file_path}: {e}[/bold red]"))

    @staticmethod
    def download_thumbnail(thumbnail_url: str, audiofile):
        """Baixa a miniatura e a define para o arquivo de áudio."""
        try:
            response = requests.get(thumbnail_url, timeout=5)
            if response.status_code == 200:
                audiofile.tag.images.set(3, response.content, "image/jpeg", "Capa do Álbum")
                audiofile.tag.save()
        except Exception as e:
            console.print(Panel(f"[bold red]Erro ao baixar a miniatura: {e}[/bold red]"))

    @staticmethod
    def extract_video_info(youtube_url: str) -> Dict[str, Any]:
        """Extrai informações do vídeo a partir da URL do YouTube fornecida."""
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                return {
                    "title": info.get("title"),
                    "duration": info.get("duration"),
                    "thumbnail": info.get("thumbnail"),
                    "uploader": info.get("uploader"),
                    "upload_date": info.get("upload_date"),
                    "description": info.get("description")
                }
        except Exception as e:
            console.print(Panel(f"[bold red]Erro ao extrair informações do vídeo: {e}[/bold red]"))
            return {}

    def get_download_options(self, title: str, is_audio: bool, quality: str = 'best') -> Dict[str, Any]:
        """Obtém opções de download para vídeo/áudio do YouTube."""
        file_extension = OUTPUT_FORMATS['audio'] if is_audio else OUTPUT_FORMATS['video']
        sanitized_title = self.sanitize_filename(title)

        options = {
            'outtmpl': os.path.join(DOWNLOAD_DIRECTORY, f"{sanitized_title}.%(ext)s"),
            'format': 'bestaudio[ext=m4a]/best[ext=mp3]' if is_audio else f'bestvideo[ext=mp4][height<={quality}]+bestaudio[ext=m4a]/best[ext=mp4][height<={quality}]/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}] if is_audio else [],
            'noplaylist': True  # Garantindo que apenas o vídeo único seja baixado
        }

        return options

    def are_downloads_active(self) -> bool:
        """Verifica se há downloads ativos."""
        with self.lock:
            return len(self.active_downloads) > 0

    def download_media(self, youtube_url: str, title: str, is_audio: bool, quality: str, progress_callback):
        """Baixa mídia do YouTube e atualiza o progresso."""
        download_opts = self.get_download_options(title, is_audio, quality)

        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
        )

        task = progress.add_task(f"[cyan]Baixando: {title}", total=100)

        def progress_hook(d):
            if d['status'] == 'downloading':
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes', 1)

                # Proteção contra divisão por zero
                if total > 0:
                    percentage = (downloaded / total) * 95  # Limite em 95%
                    progress.update(task, completed=int(min(percentage, 95)))
                    progress_callback(min(int(percentage), 95))  # Garantir que o valor do callback de progresso seja limitado a 95

        download_opts['progress_hooks'] = [progress_hook]

        try:
            with Live(Panel(progress), refresh_per_second=10) as live:
                with yt_dlp.YoutubeDL(download_opts) as ydl:
                    ydl.download([youtube_url])

            # Determina o caminho final do arquivo com base em ser áudio ou vídeo
            final_file_path = os.path.join(DOWNLOAD_DIRECTORY, self.sanitize_filename(title))
            if is_audio:
                final_file_path += ".mp3"
            else:
                final_file_path += ".mp4"  # Supondo que os arquivos de vídeo sejam salvos como .mp4

            # Se o arquivo baixado for áudio, adicione metadados
            if is_audio:
                video_info = self.extract_video_info(youtube_url)
                self.add_metadata_to_mp3(final_file_path, video_info)

            # Atualiza a barra de progresso para 100% após todas as tarefas pós-download
            progress.update(task, completed=100)  # Define o progresso para 100%
            progress_callback(100)  # Garantir que o valor do callback de progresso seja 100 agora

            console.print(Panel(f"[bold green]Download concluído: {title}[/bold green]"))

        except Exception as e:
            console.print(Panel(f"[bold red]Erro durante o download: {str(e)}[/bold red]"))
        finally:
            with self.lock:
                self.active_downloads.pop(youtube_url, None)
            self.process_download_queue()

    def handle_download_request(self, youtube_url: str, format_type: str, quality: str, progress_callback) -> tuple:
        """Gerencia uma solicitação de download."""
        video_info = self.extract_video_info(youtube_url)
        if not video_info:
            error_message = "Falha ao extrair informações do vídeo. Por favor, verifique a URL."
            console.print(Panel(f"[bold red]{error_message}[/bold red]"))
            return {"error": error_message}, 400

        title = video_info['title']
        sanitized_title = self.sanitize_filename(title)
        is_audio = format_type == "audio"

        if self.is_file_downloaded(sanitized_title, is_audio):
            error_message = "Arquivo já baixado."
            console.print(Panel(f"[bold yellow]{error_message}[/bold yellow]"))
            return {"error": error_message}, 409

        with self.lock:
            if len(self.active_downloads) < MAX_CONCURRENT_DOWNLOADS:
                self.active_downloads[youtube_url] = {"title": title, "status": "downloading"}
                threading.Thread(target=self.download_media, args=(youtube_url, title, is_audio, quality, progress_callback)).start()
                message = "Download iniciado."
            else:
                self.download_queue.put((youtube_url, title, is_audio, quality))
                message = "Download na fila."

            console.print(Panel(f"[bold blue]{message} Título: {title}[/bold blue]"))
            return {"message": message, "title": title, "position": self.download_queue.qsize()}, 202

    def process_download_queue(self):
        """Processa a fila de downloads se houver slots ativos disponíveis."""
        if not self.download_queue.empty() and len(self.active_downloads) < MAX_CONCURRENT_DOWNLOADS:
            youtube_url, title, is_audio, quality = self.download_queue.get()
            with self.lock:
                self.active_downloads[youtube_url] = {"title": title, "status": "downloading"}
            threading.Thread(target=self.download_media, args=(youtube_url, title, is_audio, quality)).start()

    def is_file_downloaded(self, title: str, is_audio: bool) -> bool:
        """Verifica se um arquivo já foi baixado."""
        file_extension = OUTPUT_FORMATS['audio'] if is_audio else OUTPUT_FORMATS['video']
        return os.path.exists(os.path.join(DOWNLOAD_DIRECTORY, f"{title}.{file_extension}"))

    def cancel_download(self, youtube_url: str) -> tuple:
        """Cancela um download em andamento ou o remove da fila."""
        with self.lock:
            if youtube_url in self.active_downloads:
                self.active_downloads.pop(youtube_url, None)
                self.process_download_queue()
                message = "Download cancelado com sucesso"
                console.print(Panel(f"[bold green]{message}[/bold green]"))
                return {"message": message}, 200
            else:
                message = "Nenhum download ativo encontrado com a URL fornecida."
                console.print(Panel(f"[bold yellow]{message}[/bold yellow]"))
                return {"error": message}, 404
