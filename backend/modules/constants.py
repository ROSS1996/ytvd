import os
import re

DEBUG = True
DOWNLOAD_DIRECTORY = "downloads" if DEBUG else os.path.join(os.path.expanduser("~"), "Downloads")
OUTPUT_FORMATS = {'audio': 'mp3', 'video': 'mp4'}
MAX_CONCURRENT_DOWNLOADS = 3
COMPLETION_SOUND_FREQ = 1000
COMPLETION_SOUND_DURATION = 500

# Create download directory if it doesn't exist
os.makedirs(DOWNLOAD_DIRECTORY, exist_ok=True)

# Regex for detecting YouTube videos
YOUTUBE_VIDEO_REGEX = r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.?be/)[\w-]{11}$'
