import os
import io
import uuid
import threading
import socket
import qrcode
import yt_dlp
import requests
from flask import Flask, request, render_template_string, jsonify, send_file, send_from_directory

app = Flask(__name__)
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
download_progress = {}
download_info = {}

# Fixed: Detect cookies.txt to bypass YouTube's "Sign in to confirm you're not a bot"
COOKIES_FILE = "cookies.txt" if os.path.exists("cookies.txt") else None

# Paste your FULL HTML code here (the 500 lines of CSS/HTML from before)
HTML_TEMPLATE = """
[INSERT YOUR FULL 500-LINE HTML HERE]
"""

def progress_hook(d):
    download_id = d.get("download_id")
    if not download_id: return
    prog = download_progress.setdefault(download_id, {})
    if d['status'] == 'downloading':
        p = d.get('_percent_str', '0%').replace('%','').strip()
        prog.update({"percent": p})
    elif d['status'] == 'finished':
        prog.update({"percent": "100", "finished": True})

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url", "").strip()
        fmt = request.form.get("format", "mp4")
        download_id = str(uuid.uuid4())
        
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best' if fmt == 'mp4' else 'bestaudio/best',
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
            'progress_hooks': [lambda d: (d.update({'download_id': download_id}), progress_hook(d))],
            'cookiefile': COOKIES_FILE, # Fix for YouTube blocks
            'nocheckcertificate': True
        }
        
        def run_down():
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    download_progress[download_id]["filename"] = os.path.basename(ydl.prepare_filename(info))
            except Exception as e:
                download_progress[download_id] = {"error": str(e)}

        download_progress[download_id] = {"percent": "0"}
        threading.Thread(target=run_down).start()
        return jsonify({"download_id": download_id})
    return render_template_string(HTML_TEMPLATE)

@app.route("/progress/<download_id>")
def progress(download_id):
    return jsonify(download_progress.get(download_id, {"percent": "0"}))

@app.route("/download/<path:filename>")
def download(filename):
    path = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return "File not found.", 404

@app.route("/qrcode/<path:filename>")
def qrcode_route(filename):
    # Fixed: Automatically uses your HTTPS Render URL
    public_url = request.host_url.replace("http://", "https://")
    file_url = f"{public_url}download/{filename}"
    img = qrcode.make(file_url)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")

# --- NATIVE APP ROUTES (Removes browser bar) ---
@app.route("/manifest.json")
def serve_manifest():
    return send_from_directory('static', 'manifest.json')

@app.route("/sw.js")
def serve_sw():
    return send_from_directory('static', 'sw.js')

@app.route("/.well-known/assetlinks.json")
def serve_assetlinks():
    # This file is what makes the APK feel like a "Proper App"
    return send_from_directory('static/.well-known', 'assetlinks.json')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
