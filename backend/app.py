import os
import json
import threading
import platform
import socket
import tkinter as tk
from tkinter import messagebox
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
from colorama import init
import logging
from typing import Dict, Any
from werkzeug.serving import run_simple
from queue import Queue
import requests
import re
import winsound
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
import eyed3

# Initialize Flask application and CORS
app = Flask(__name__)
CORS(app)

# Constants
DEBUG = True
DOWNLOAD_DIRECTORY = "downloads" if DEBUG else os.path.join(os.path.expanduser("~"), "Downloads")
OUTPUT_FORMATS = {'audio': 'mp3', 'video': 'mp4'}  # Keep audio as mp3 and video as mp4
MAX_CONCURRENT_DOWNLOADS = 3
COMPLETION_SOUND_FREQ = 1000
COMPLETION_SOUND_DURATION = 500

# Initialize colorama and logging
init(autoreset=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Rich console
console = Console()

# Create download directory if it doesn't exist
os.makedirs(DOWNLOAD_DIRECTORY, exist_ok=True)

# Track active downloads and queue
active_downloads: Dict[str, Dict[str, Any]] = {}
download_queue = Queue()

def is_internet_available() -> bool:
    """Check internet connectivity."""
    try:
        socket.create_connection(("www.google.com", 80))
        return True
    except OSError:
        return False

def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing reserved characters."""
    reserved_chars_pattern = r'[<>:"/\\|?*]'
    return re.sub(r'_+', '_', re.sub(reserved_chars_pattern, '_', filename))

def display_no_internet_message():
    """Display an error message if there's no internet connection."""
    with tk.Tk() as root:
        root.withdraw()
        messagebox.showerror("Sem conexão com a Internet", "Você não está conectado à internet.")

def add_metadata_to_mp3(file_path: str, video_info: Dict[str, Any]):
    """Add metadata to the downloaded MP3 file."""
    try:
        audiofile = eyed3.load(file_path)
        if not audiofile or not audiofile.tag:
            audiofile.initTag()

        audiofile.tag.title = video_info.get("title", "Título Desconhecido")
        audiofile.tag.artist = video_info.get("uploader", "Artista Desconhecido")
        audiofile.tag.album = "Download do YouTube"
        audiofile.tag.year = video_info.get("upload_date", "")[:4]
        audiofile.tag.comments.set(video_info.get("description", ""))

        # Add album art
        thumbnail_url = video_info.get("thumbnail")
        if thumbnail_url:
            response = requests.get(thumbnail_url)
            if response.status_code == 200:
                audiofile.tag.images.set(3, response.content, "image/jpeg", u"Capa do Álbum")

        audiofile.tag.save()
        console.print(Panel(f"[bold green]Metadados adicionados a {file_path}[/bold green]"))
    except Exception as e:
        console.print(Panel(f"[bold red]Erro ao adicionar metadados a {file_path}: {e}[/bold red]"))


def extract_video_info(youtube_url: str) -> Dict[str, Any]:
    """Extract video information using yt-dlp."""
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

# Update download options for video format
def get_download_options(title: str, is_audio: bool, quality: str = 'best') -> Dict[str, Any]:
    """Get download options for yt-dlp."""
    file_extension = OUTPUT_FORMATS['audio'] if is_audio else OUTPUT_FORMATS['video']
    sanitized_title = sanitize_filename(title)
    
    options = {
        'outtmpl': os.path.join(DOWNLOAD_DIRECTORY, f"{sanitized_title}.%(ext)s"),
        'format': 'bestaudio[ext=m4a]/best[ext=mp3]' if is_audio else f'bestvideo[ext=mp4][height<={quality}]+bestaudio[ext=m4a]/best[ext=mp4][height<={quality}]/best',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}] if is_audio else [],
    }
    
    return options

# Modify download_media function to handle MP3 and MP4 correctly
def download_media(youtube_url: str, title: str, is_audio: bool, quality: str):
    """Download media from YouTube with improved progress display."""
    download_opts = get_download_options(title, is_audio, quality)
    
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
            percentage = d.get('percentage', 0)
            if percentage is not None:
                progress.update(task, completed=int(percentage))
            
            # Update the description with detailed information
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            speed = d.get('speed', 0)
            
            if total > 0:
                progress.update(task, total=total, completed=downloaded, description=f"[cyan]Baixando: {title}")
    
    download_opts['progress_hooks'] = [progress_hook]
    
    try:
        with Live(Panel(progress), refresh_per_second=10) as live:
            with yt_dlp.YoutubeDL(download_opts) as ydl:
                ydl.download([youtube_url])
        
        # Post-download processing only for audio files
        if is_audio:
            sanitized_title = sanitize_filename(title)
            final_file_path = os.path.join(DOWNLOAD_DIRECTORY, f"{sanitized_title}.mp3")
            if os.path.exists(final_file_path + ".mp3"):
                os.rename(final_file_path + ".mp3", final_file_path)
            
            video_info = extract_video_info(youtube_url)
            add_metadata_to_mp3(final_file_path, video_info)
        else:
            console.print(Panel(f"[bold green]Download de vídeo concluído: {title}[/bold green]"))

        play_completion_sound()
        
        console.print(Panel(f"[bold green]Download concluído: {title}[/bold green]"))
    except Exception as e:
        console.print(Panel(f"[bold red]Erro durante o download: {str(e)}[/bold red]"))
    finally:
        with threading.Lock():
            active_downloads.pop(youtube_url, None)
        process_download_queue()

def play_completion_sound():
    """Play a beep sound when download is completed."""
    if platform.system() == "Windows":
        winsound.Beep(COMPLETION_SOUND_FREQ, COMPLETION_SOUND_DURATION)
    else:
        os.system('echo -e "\a"')

def handle_download_request(youtube_url: str, format_type: str, quality: str) -> tuple:
    """Handle download request for a YouTube video."""
    video_info = extract_video_info(youtube_url)
    if not video_info:
        error_message = "Não foi possível extrair as informações do vídeo. Por favor, verifique a URL."
        console.print(Panel(f"[bold red]{error_message}[/bold red]"))
        return {"error": error_message}, 400

    title = video_info['title']
    sanitized_title = sanitize_filename(title)
    is_audio = format_type == "audio"

    if is_file_downloaded(sanitized_title, is_audio):
        error_message = "Arquivo já baixado."
        console.print(Panel(f"[bold yellow]{error_message}[/bold yellow]"))
        return {"error": error_message}, 409

    with threading.Lock():
        if len(active_downloads) < MAX_CONCURRENT_DOWNLOADS:
            active_downloads[youtube_url] = {"title": title, "status": "baixando"}
            
            # Ensure all arguments are passed correctly
            threading.Thread(target=download_media, args=(youtube_url, title, is_audio, quality)).start()
            message = "Download iniciado."
        else:
            download_queue.put((youtube_url, title, is_audio, quality))
            message = "Download enfileirado."
        
        console.print(Panel(f"[bold blue]{message} Título: {title}[/bold blue]"))
        return {"message": message, "title": title, "position": download_queue.qsize()}, 202

def process_download_queue():
    """Process the download queue."""
    if not download_queue.empty() and len(active_downloads) < MAX_CONCURRENT_DOWNLOADS:
        youtube_url, title, quality = download_queue.get()
        with threading.Lock():
            active_downloads[youtube_url] = {"title": title, "status": "baixando"}
        threading.Thread(target=download_media, args=(youtube_url, title, quality)).start()

def is_file_downloaded(title: str, is_audio: bool) -> bool:
    """Check if a file has been downloaded."""
    file_extension = OUTPUT_FORMATS['video']
    return os.path.exists(os.path.join(DOWNLOAD_DIRECTORY, f"{title}.{file_extension}"))

@app.route('/download', methods=['POST'])
def download():
    """Handle video download requests."""
    data = request.json
    youtube_url = data.get("url")
    format_type = data.get("format", "video").lower()
    quality = data.get("quality", "720")
    response, status_code = handle_download_request(youtube_url, format_type, quality)
    return jsonify(response), status_code

@app.route('/is_downloading', methods=['GET'])
def is_downloading():
    """Check if a video is being downloaded."""
    youtube_url = request.args.get("url")
    is_downloading = youtube_url in active_downloads
    status = active_downloads.get(youtube_url, {}).get("status", "não encontrado")
    return jsonify({"is_downloading": is_downloading, "status": status}), 200

@app.route('/download_status', methods=['GET'])
def download_status():
    """Get status of all active downloads and the queue."""
    return jsonify({"active_downloads": active_downloads, "queue_size": download_queue.qsize()}), 200

@app.route('/cancel_download', methods=['POST'])
def cancel_download():
    """Cancel an active download or remove it from the queue."""
    data = request.json
    youtube_url = data.get("url")

    if youtube_url in active_downloads:
        active_downloads.pop(youtube_url, None)
        process_download_queue()
        message = "Download cancelado com sucesso"
        console.print(Panel(f"[bold green]{message}[/bold green]"))
        return jsonify({"message": message}), 200

    with download_queue.mutex:
        queue_list = list(download_queue.queue)
        for i, (url, _, _) in enumerate(queue_list):
            if url == youtube_url:
                del queue_list[i]
                download_queue.queue.clear()
                download_queue.queue = Queue(queue_list)
                message = "Download removido da fila"
                console.print(Panel(f"[bold green]{message}[/bold green]"))
                return jsonify({"message": message}), 200

    error_message = "Download não encontrado"
    console.print(Panel(f"[bold red]{error_message}[/bold red]"))
    return jsonify({"error": error_message}), 404

@app.route('/download_file', methods=['GET'])
def download_file():
    """Serve a downloaded file."""
    filename = request.args.get('filename')
    file_path = os.path.join(DOWNLOAD_DIRECTORY, filename)

    if not os.path.exists(file_path):
        error_message = "Arquivo não encontrado"
        console.print(Panel(f"[bold red]{error_message}[/bold red]"))
        return jsonify({"error": error_message}), 404

    return send_file(file_path, as_attachment=True)

@app.route('/valid_video', methods=['POST'])
def valid_video():
    """Check if a given URL is a valid YouTube video page."""
    data = request.json
    youtube_url = data.get("url", "").strip()

    # Regular expression to validate YouTube video URL
    youtube_regex = r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.?be/)[\w-]{11}$'

    if re.match(youtube_regex, youtube_url):
        return jsonify({"message": "Valid YouTube video URL."}), 200
    else:
        return jsonify({"error": "Invalid YouTube video URL."}), 400

def start_server():
    """Start the Flask server with error handling."""
    app.register_error_handler(Exception, lambda e: (jsonify({"error": "Erro interno do servidor"}), 500))
    console.print(Panel("[bold green]Iniciando o servidor...[/bold green]"))
    run_simple('localhost', 5000, app, use_reloader=False, use_debugger=DEBUG)

if __name__ == '__main__':
    if not is_internet_available():
        display_no_internet_message()
    else:
        start_server()
