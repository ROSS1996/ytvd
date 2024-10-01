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

# Initialize Rich console
console = Console()

# Create download directory if it doesn't exist
os.makedirs(DOWNLOAD_DIRECTORY, exist_ok=True)

# Regex for detecting YouTube videos
YOUTUBE_VIDEO_REGEX = r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.?be/)[\w-]{11}$'

class DownloadManager:
    def __init__(self):
        self.active_downloads: Dict[str, Dict[str, Any]] = {}
        self.download_queue = Queue()
        self.lock = threading.Lock()

    @staticmethod
    def is_internet_connected() -> bool:
        """Check if the internet is connected."""
        try:
            socket.create_connection(("www.google.com", 80))
            return True
        except OSError:
            return False

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize a filename by removing illegal characters."""
        reserved_chars_pattern = r'[<>:"/\\|?*]'
        return re.sub(r'_+', '_', re.sub(reserved_chars_pattern, '_', filename))

    @staticmethod
    def add_metadata_to_mp3(file_path: str, video_info: Dict[str, Any]):
        """Add metadata to the downloaded MP3 file."""
        try:
            audiofile = eyed3.load(file_path)
            if not audiofile or not audiofile.tag:
                audiofile.initTag()

            audiofile.tag.title = video_info.get("title", "Unknown Title")
            audiofile.tag.artist = video_info.get("uploader", "Unknown Artist")
            audiofile.tag.album = "YouTube Download"
            audiofile.tag.year = video_info.get("upload_date", "")[:4]
            audiofile.tag.comments.set(video_info.get("description", ""))

            thumbnail_url = video_info.get("thumbnail")
            if thumbnail_url:
                response = requests.get(thumbnail_url)
                if response.status_code == 200:
                    audiofile.tag.images.set(3, response.content, "image/jpeg", "Album Cover")

            audiofile.tag.save()
            console.print(Panel(f"[bold green]Metadata added to {file_path}[/bold green]"))
        except Exception as e:
            console.print(Panel(f"[bold red]Error adding metadata to {file_path}: {e}[/bold red]"))

    @staticmethod
    def extract_video_info(youtube_url: str) -> Dict[str, Any]:
        """Extract video information from the provided YouTube URL."""
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
            console.print(Panel(f"[bold red]Error extracting video info: {e}[/bold red]"))
            return {}

    def get_download_options(self, title: str, is_audio: bool, quality: str = 'best') -> Dict[str, Any]:
        """Get download options for YouTube video/audio."""
        file_extension = OUTPUT_FORMATS['audio'] if is_audio else OUTPUT_FORMATS['video']
        sanitized_title = self.sanitize_filename(title)

        options = {
            'outtmpl': os.path.join(DOWNLOAD_DIRECTORY, f"{sanitized_title}.%(ext)s"),
            'format': 'bestaudio[ext=m4a]/best[ext=mp3]' if is_audio else f'bestvideo[ext=mp4][height<={quality}]+bestaudio[ext=m4a]/best[ext=mp4][height<={quality}]/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}] if is_audio else [],
        }

        return options

    def are_downloads_active(self) -> bool:
        """Check if there are any active downloads."""
        with self.lock:
            return len(self.active_downloads) > 0

    def download_media(self, youtube_url: str, title: str, is_audio: bool, quality: str, progress_callback):
        """Download media from YouTube and update progress."""
        download_opts = self.get_download_options(title, is_audio, quality)

        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
        )

        task = progress.add_task(f"[cyan]Downloading: {title}", total=100)

        def progress_hook(d):
            if d['status'] == 'downloading':
                percentage = d.get('downloaded_bytes', 0) / (d.get('total_bytes', 1)) * 95  # Cap at 95%
                progress.update(task, completed=int(percentage))
                progress_callback(int(percentage))  # Update GUI progress

        download_opts['progress_hooks'] = [progress_hook]

        try:
            with Live(Panel(progress), refresh_per_second=10) as live:
                with yt_dlp.YoutubeDL(download_opts) as ydl:
                    ydl.download([youtube_url])

            # Perform post-download steps, like adding metadata
            if is_audio:
                final_file_path = os.path.join(DOWNLOAD_DIRECTORY, f"{self.sanitize_filename(title)}.mp3")
                if os.path.exists(final_file_path + ".mp3"):
                    os.rename(final_file_path + ".mp3", final_file_path)

                video_info = self.extract_video_info(youtube_url)
                self.add_metadata_to_mp3(final_file_path, video_info)
            
            # Update the progress bar to 100% after all post-download tasks
            progress_callback(100)
            console.print(Panel(f"[bold green]Download and metadata completed: {title}[/bold green]"))

        except Exception as e:
            console.print(Panel(f"[bold red]Error during download: {str(e)}[/bold red]"))
        finally:
            with self.lock:
                self.active_downloads.pop(youtube_url, None)
            self.process_download_queue()

    def handle_download_request(self, youtube_url: str, format_type: str, quality: str, progress_callback) -> tuple:
        """Handle a download request."""
        video_info = self.extract_video_info(youtube_url)
        if not video_info:
            error_message = "Failed to extract video info. Please check the URL."
            console.print(Panel(f"[bold red]{error_message}[/bold red]"))
            return {"error": error_message}, 400

        title = video_info['title']
        sanitized_title = self.sanitize_filename(title)
        is_audio = format_type == "audio"

        if self.is_file_downloaded(sanitized_title, is_audio):
            error_message = "File already downloaded."
            console.print(Panel(f"[bold yellow]{error_message}[/bold yellow]"))
            return {"error": error_message}, 409

        with self.lock:
            if len(self.active_downloads) < MAX_CONCURRENT_DOWNLOADS:
                self.active_downloads[youtube_url] = {"title": title, "status": "downloading"}
                threading.Thread(target=self.download_media, args=(youtube_url, title, is_audio, quality, progress_callback)).start()
                message = "Download started."
            else:
                self.download_queue.put((youtube_url, title, is_audio, quality))
                message = "Download queued."

            console.print(Panel(f"[bold blue]{message} Title: {title}[/bold blue]"))
            return {"message": message, "title": title, "position": self.download_queue.qsize()}, 202

    def process_download_queue(self):
        """Process the download queue if there are active slots available."""
        if not self.download_queue.empty() and len(self.active_downloads) < MAX_CONCURRENT_DOWNLOADS:
            youtube_url, title, is_audio, quality = self.download_queue.get()
            with self.lock:
                self.active_downloads[youtube_url] = {"title": title, "status": "downloading"}
            threading.Thread(target=self.download_media, args=(youtube_url, title, is_audio, quality)).start()

    def is_file_downloaded(self, title: str, is_audio: bool) -> bool:
        """Check if a file has already been downloaded."""
        file_extension = OUTPUT_FORMATS['audio'] if is_audio else OUTPUT_FORMATS['video']
        return os.path.exists(os.path.join(DOWNLOAD_DIRECTORY, f"{title}.{file_extension}"))

    def cancel_download(self, youtube_url: str) -> tuple:
        """Cancel an ongoing download or remove it from the queue."""
        with self.lock:
            if youtube_url in self.active_downloads:
                self.active_downloads.pop(youtube_url, None)
                self.process_download_queue()
                message = "Download canceled successfully"
                console.print(Panel(f"[bold green]{message}[/bold green]"))
                return {"message": message}, 200
            else:
                message = "No active download found with the provided URL."
                console.print(Panel(f"[bold yellow]{message}[/bold yellow]"))
                return {"error": message}, 404
