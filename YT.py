from flask import Flask, render_template, Response, request
from tkinter import Tk, filedialog
import yt_dlp
import threading
import time
import os
import re
import webview

URL_CLEAN = r'^(https?://[^\?]+)'

app = Flask(__name__)

progress_data = {"percent": "", "title": ""}

def get_video_title(url):
    ydl_opts = {'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return info.get('title', 'Unknown')
        except Exception as e:
            print(f"Error getting title: {e}")
            return "Unknown"

@app.route("/", methods=["GET", "POST"])
def index():
    is_checked = False
    if request.method == "POST":
        is_checked = request.form.get('playlist') == 'on'
        quality = request.form["quality"]
        url = request.form["url"]
        folder = request.form["folder"]
        progress_data["title"] = get_video_title(url)

        if not is_checked:
            match = re.match(URL_CLEAN, url)
            if match:
                url = match.group(1)

        if not folder:
            folder = os.path.join(os.getcwd(), "downloads")

        if quality == "best":
            fmt = "bestvideo+bestaudio/best"
        else:
            fmt = f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]"

        def download_video(url):
            def progress_hook(d):
                if d['status'] == 'downloading':
                    progress_data["percent"] = d['_percent_str'].strip()
                elif d['status'] == 'finished':
                    progress_data["percent"] = "100%"

            ydl_opts = {
                'ffmpeg_location': 'ffmpeg.exe',
                'format': fmt,
                'merge_output_format': 'mp4',
                'progress_hooks': [progress_hook],
                'outtmpl': os.path.join(folder, "%(title)s.%(ext)s")
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        threading.Thread(target=download_video, args=(url,), daemon=True).start()
    return render_template("index.html")

@app.route("/progress")
def progress():
    def generate():
        while True:
            percent_match = re.search(r'(\d+\.?\d*)%', progress_data['percent'])
            percent = percent_match.group(1) if percent_match else ''
            title = progress_data["title"]
            yield f'data: {{"percent": "{percent}", "title": "{title}"}}\n\n'
            time.sleep(1)
    return Response(generate(), mimetype="text/event-stream")

@app.route("/choose_folder")
def choose_folder():
    root = Tk()
    root.withdraw()
    folder_selected = filedialog.askdirectory()
    return folder_selected if folder_selected else "downloads"


# class API:
#     def choose_folder(self):
#         root = Tk()
#         root.withdraw()
#         folder_selected = filedialog.askdirectory()
#         root.destroy()
#         return folder_selected if folder_selected else ""


def run_flask():
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

if __name__ == "__main__":
    # Start Flask server in background thread
    threading.Thread(target=run_flask, daemon=True).start()

    # Run pywebview on main thread with custom icon
    icon_path = os.path.abspath("static/new.ico")  # Make sure file exists
    webview.create_window(
        title="YT Downloader",
        url="http://127.0.0.1:5000",
        width=550,
        height=600,
        resizable=False,
        x=400,
        y=150,
        minimized=False,
        maximized=False,
        frameless=False,
    )
    webview.start()
