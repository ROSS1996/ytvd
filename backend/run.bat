@echo off
cd /d D:\CustomYTdownloader\backend
call venv\Scripts\activate.bat
pip install yt-dlp -U
pip install -r requirements.txt
python app.py
pause
