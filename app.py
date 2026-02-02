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

COOKIES_FILE = "cookies.txt" if os.path.exists("cookies.txt") else None

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Social Media Downloader</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css"/>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"/>
  <style>
    body {min-height: 100vh; margin: 0; background: radial-gradient(circle at 60% 20%, #b8eaff 0%, #188fa7 70%, #061826 100%);
      display: flex; align-items: center; justify-content: center;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #def6ff;}
    .main-card {background: rgba(13, 28, 43, 0.97); border-radius: 2em; box-shadow: 0 8px 30px #12aed645;
      padding: 2.5em 2em 2em 2em; min-width: 336px; max-width: 97vw; width: 400px; text-align: center;}
    h1 {font-weight: 900; font-size: 2.1rem; color: #f7fafd; margin-bottom: 0.55rem; letter-spacing: 0.09em; text-shadow: 0 0 20px #33fffd10;}
    .social-icons {display: flex; flex-direction: row; justify-content: center; align-items: center; gap: 25px; margin-bottom: 24px;}
    .social-icons a {text-decoration: none; color: #45d5fe; background: none; border-radius: 50%; font-size: 2.27rem; padding: .22em;
      display: flex; align-items: center; justify-content: center; transition: color 0.18s, background 0.23s, box-shadow 0.16s, transform 0.21s;}
    .social-icons a:hover, .social-icons a:focus {
      outline: none; background: linear-gradient(135deg,#36e3f1 0%,#b45edd 70%,#fb7185 100%);
      background-clip: text; -webkit-background-clip: text; color: transparent; -webkit-text-fill-color: transparent;
      filter: brightness(1.24) saturate(1.05); transform: scale(1.14); box-shadow: 0 2px 8px 0 #2cb7fa27 inset;
      animation: colorSpin 1.2s linear infinite; text-decoration: none;}
    .social-icons a:active { filter: brightness(1.34);}
    .social-icons i { vertical-align: middle;}
    @keyframes colorSpin {0% { filter: hue-rotate(0deg);} 100% { filter: hue-rotate(360deg);}}
    form label {font-weight: 700; margin-top: 1em; margin-bottom: 2px; text-align: left; color: #bae3ff; font-size: 1.05rem; display:block;}
    input, select {font-size: 1.09rem; margin-bottom: 13px; padding: 12px 13px; border-radius: 10px; border: none;
      background: #152c39; color: #daefff; width: 100%; outline: none; box-shadow: 0 1px 8px #19bbfb15 inset;
      transition: box-shadow 0.2s, background 0.23s;}
    input:focus, select:focus {background: #134e6e; box-shadow: 0 0 12px #00caf228;}
    button {margin-top: 15px; width: 100%; padding: 15px 0; font-weight: 800; font-size: 1.17rem; border-radius: 13px; border: none;
      background: linear-gradient(90deg, #5eead4, #60a5fa 98%); color: #122137; cursor: pointer;
      transition: background 0.21s, color 0.14s; box-shadow: 0 3px 15px #2ae8e930; letter-spacing: 0.04em;}
    button:disabled {filter: grayscale(67%); opacity: 0.77; cursor: not-allowed; box-shadow: none;}
    button:hover:not(:disabled) {background: linear-gradient(90deg,#60a5fa 10%,#5eead4 100%); color: #174a68;}
    .progress { margin-top:20px; height:18px; border-radius:8px; background:#1e6a85; }
    .progress-bar {background: linear-gradient(90deg, #1ed6d2 0%, #3b82f6 100%); font-weight:700; font-size:1.01rem; transition: width 0.33s;}
    .progress-text {margin-top: 7px; font-weight: 600; color: #e7fdfe; text-align: center; font-size:1.07em;}
    #thumb-preview {margin: 18px auto 12px auto; display: none; width: 125px; border-radius:12px; box-shadow: 0 2px 14px #62eada77; cursor: pointer;}
    #download-links {margin: 8px auto 20px auto; display:none;}
    #download-links a, #download-links button {display:inline-block;background:#25e1e0;color:#1e2449; font-weight:600; border-radius:10px; padding:7px 14px; margin:5px 3px;
      text-decoration:none; transition:background 0.24s; border: none; box-shadow: 0 1px 8px #1897fc11 inset; font-size:.94em;}
    #download-links a:hover, #download-links button:hover {background: #60a5fa; color: #fff; text-decoration:none;}
    #qr-code {display: none; margin: 32px auto 10px auto; width: 104px; height:104px; border-radius: 13px; box-shadow: 0 0 14px 1px #b8eaff54;
      background:#fff; cursor: pointer; transition: opacity 0.3s;}
    #qr-tip {text-align: center; font-weight: 700; font-size: 1rem; color: #40d5fe; margin-bottom: 8px; display: none;}
    #toast {position: fixed; bottom: 44px; left: 50%; transform: translateX(-50%); background: #5eead4; color: #1c2736; font-weight: 700;
      font-size: 1.1rem; padding: 12px 28px; border-radius: 20px; opacity: 0; pointer-events: none; box-shadow: 0 4px 18px #81fdfa23;
      user-select: none; transition: opacity 0.29s ease; z-index: 1000; cursor: pointer;}
    #toast.visible { opacity: 1; pointer-events: auto;}
    @media (max-width: 480px) {.main-card { width:97vw; border-radius:8vw; padding:1em 3vw 2vw 3vw;} h1 { font-size:1.38rem;}
      .social-icons {gap:11px; font-size:1.53rem;}}
    /* Modal styles */
    #media-modal {display:none; position:fixed; z-index:1100; left:0; top:0; width:100vw; height:100vh; background:rgba(0,0,0,0.65);
      align-items:center; justify-content:center;}
    #media-modal.active {display:flex;}
    #media-modal-content {background:#061826; border-radius:14px; box-shadow:0 2px 22px #0089bff7; padding:2vw 3vw 3vw 3vw;
      max-width:80vw; max-height:90vh; text-align:center; display:flex; flex-direction:column; align-items:center;}
    #modal-close {color:#abd; font-size:1.7rem; cursor:pointer; margin-left:auto; margin-bottom:8px;}
    video, audio { max-width:72vw; max-height:60vh; outline:none; margin: 12px 0; border-radius:10px;}
  </style>
  <link rel="manifest" href="/manifest.json">
<script>
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js");
}
</script>
</head>
<body>
  <div class="main-card">
    <h1>⚡ Social Media Downloader</h1>
    <div class="social-icons">
      <a href="https://instagram.com" target="_blank" title="Instagram"><i class="fab fa-instagram"></i></a>
      <a href="https://youtube.com" target="_blank" title="YouTube"><i class="fab fa-youtube"></i></a>
      <a href="https://facebook.com" target="_blank" title="Facebook"><i class="fab fa-facebook"></i></a>
      <a href="https://twitter.com" target="_blank" title="Twitter"><i class="fab fa-twitter"></i></a>
    </div>
    <form id="download-form" autocomplete="off" method="post">
      <label for="url">Paste Social Media Link:</label>
      <input id="url" name="url" type="text" placeholder="https://youtube.com/..." required/>
      <label for="format">Select Format:</label>
      <select id="format" name="format" onchange="toggleQualityPicker()">
        <option value="mp3">MP3 (Audio)</option>
        <option value="mp4">MP4 (Video)</option>
      </select>
      <div id="audio-quality">
        <label for="mp3quality">Audio Quality:</label>
        <select id="mp3quality" name="mp3quality">
          <option value="m4a_128">128K (M4A)</option>
          <option value="mp3_128">128K (MP3)</option>
          <option value="mp3_48">48K (MP3)</option>
          <option value="mp3_256">256K (MP3)</option>
        </select>
      </div>
      <div id="video-quality" style="display:none;">
        <label for="mp4quality">Video Quality:</label>
        <select id="mp4quality" name="mp4quality">
          <option value="480">480p</option>
          <option value="720">720p</option>
          <option value="1080">1080p</option>
          <option value="1440">1440p</option>
          <option value="2160">2160p</option>
        </select>
      </div>
      <button id="download-btn" type="submit">⬇️ Download</button>
      <div id="prepare-msg" style="display:none; margin-top:14px; font-weight:700; color:#fbbc04;">Preparing download…</div>
    </form>
    <img id="thumb-preview" src="#" alt="Thumbnail Preview" style="display:none;"/>
    <div id="download-links">
      <a id="video-link" href="#" download target="_blank">⬇️ Video/Audio File</a>
      <button id="thumb-link" onclick="downloadThumbnail()" type="button">🖼️ Thumbnail</button>
      <button id="copy-thumb-url" type="button" onclick="copyThumbUrl()">Copy Thumbnail URL</button>
      <button type="button" class="btn btn-sm btn-outline-info" onclick="copyUrl('#video-link')">Copy Video URL</button>
    </div>
    <div id="progress-container" style="display:none;">
      <div class="progress"><div id="progress-bar" class="progress-bar progress-bar-striped" style="width: 0%">0%</div></div>
      <div class="progress-text"><span id="progress-downloaded">0 B</span> / <span id="progress-total">0 B</span></div>
      <img id="qr-code" src="#" alt="QR for mobile download" />
      <div id="qr-tip">Scan QR code with your phone on this WiFi to download</div>
    </div>
  </div>
  <div id="media-modal" onclick="closeMediaModal(event)">
    <div id="media-modal-content">
      <span id="modal-close" onclick="closeMediaModal(event)" title="Close">&times;</span>
      <div id="media-player-box"></div>
    </div>
  </div>
  <div id="toast"></div>
  <script>
    let thumb_url_actual = '';
    function toggleQualityPicker() {
      var fmt = document.getElementById("format").value;
      document.getElementById("audio-quality").style.display = fmt === "mp3" ? "block" : "none";
      document.getElementById("video-quality").style.display = fmt === "mp4" ? "block" : "none";
    }
    toggleQualityPicker();
    let downloadId=null, timerId=null, lastFileName='', thumb_url='';
    let lastFormat = "mp3";
    document.getElementById('download-form').addEventListener('submit', function(event){
      event.preventDefault();
      clearInterval(timerId);
      downloadId = null;
      lastFileName = '';
      thumb_url = '';
      document.getElementById('prepare-msg').style.display = "block";
      document.getElementById('progress-container').style.display = "none";
      document.getElementById('qr-code').style.display = "none";
      document.getElementById('qr-tip').style.display = "none";
      document.getElementById('thumb-preview').style.display = "none";
      document.getElementById('download-links').style.display = "none";
      document.getElementById('download-btn').disabled = true;
      lastFormat = document.getElementById("format").value;
      fetch("/", {method:"POST", body: new FormData(document.getElementById("download-form"))})
       .then(res => res.json())
       .then(data => {
         if (!data.download_id) {
           showToast("Error starting download.", true);
           resetButton();
           return;
         }
         downloadId = data.download_id;
         lastFileName = data.title && data.extension ? data.title + "." + data.extension : "";
         thumb_url = data.thumb_url;
         thumb_url_actual = thumb_url;
         document.getElementById('thumb-preview').src = thumb_url || "#";
         document.getElementById('thumb-preview').style.display = thumb_url ? 'block' : 'none';
         let thumb = document.getElementById('thumb-preview');
         if (thumb_url) {
           thumb.setAttribute('data-mediapath', '');
           thumb.setAttribute('data-mediaformat', '');
         }
         document.getElementById("prepare-msg").style.display = "none";
         document.getElementById("progress-container").style.display = "block";
         updateProgressBar(0); updateProgressStats(0, 0);
         timerId = setInterval(pollProgress, 1200);
       })
       .catch(() => {
         showToast("Network error.", true);
         resetButton();
       });
    });
    function pollProgress() {
      if (!downloadId) return;
      fetch("/progress/" + downloadId)
        .then(res=>res.json())
        .then(data=>{
          var p = parseFloat(data.percent || "0");
          updateProgressBar(p);
          updateProgressStats(data.downloaded_bytes || 0, data.total_bytes || 0);
          if (data.finished) {
            clearInterval(timerId);
            resetButton();
            showToast("Download complete: " + lastFileName, false);
            speechNotify("Download complete.");
            showQRCode(lastFileName);
            showLinks();
          }
        })
        .catch(()=>{
          clearInterval(timerId);
          showToast("Download failed or cancelled.", true);
          resetButton();
        });
    }
    function updateProgressBar(pct) {
      var bar = document.getElementById("progress-bar");
      bar.style.width = pct + "%";
      bar.innerText = pct.toFixed(1) + "%";
    }
    function updateProgressStats(d, t) {
      document.getElementById("progress-downloaded").innerText = formatBytes(d);
      document.getElementById("progress-total").innerText = formatBytes(t);
    }
    function formatBytes(bytes) {
      if (bytes === 0) return "0 B";
      var k = 1024,sizes = ["B", "KB", "MB", "GB", "TB"],i = Math.floor(Math.log(bytes) / Math.log(k));
      return (bytes / Math.pow(k, i)).toFixed(2) + " " + sizes[i];
    }
    function resetButton() {
      var btn = document.getElementById("download-btn");
      btn.disabled = false;
      btn.innerText = "⬇️ Download";
    }
    function showToast(msg, isError){
      var t = document.getElementById('toast');
      t.textContent=msg;
      t.style.background=isError?'#fd5c63':'#5eead4';
      t.classList.add("visible");
      t.onclick = () => t.classList.remove("visible");
      setTimeout(() => t.classList.remove("visible"), isError ? 4800 : 12000);
    }
    function speechNotify(msg){
      if (!("speechSynthesis" in window)) return;
      var utter=new SpeechSynthesisUtterance(msg);
      window.speechSynthesis.speak(utter);
    }
    function showQRCode(filename){
      if(!filename) return;
      var qr=document.getElementById("qr-code"),
          tip=document.getElementById("qr-tip");
      qr.src="/qrcode/"+encodeURIComponent(filename)+"?t="+Date.now();
      qr.style.display="block";
      tip.style.display="block";
      setTimeout(function(){
        qr.style.display="none";
        tip.style.display="none";
      }, 300000); // 5 min
    }
    function showLinks() {
      document.getElementById('download-links').style.display = 'block';
      let vid = document.getElementById('video-link');
      let base = lastFileName.substring(0, lastFileName.lastIndexOf(".")) || lastFileName;
      let ext = lastFileName.split('.').pop();
      vid.href = "/download/" + encodeURIComponent(lastFileName);
      vid.setAttribute("download", lastFileName);
      let thumb = document.getElementById('thumb-preview');
      thumb.setAttribute('data-mediapath', vid.href);
      thumb.setAttribute('data-mediaformat', ext);
    }
    function copyUrl(sel) {
      let el = document.querySelector(sel);
      let temp = document.createElement("input");
      temp.value = location.origin + el.getAttribute('href');
      document.body.appendChild(temp);
      temp.select();
      document.execCommand("copy");
      document.body.removeChild(temp);
      showToast("Copied: " + temp.value, false);
    }
    function downloadThumbnail() {
      if (!thumb_url_actual) {
        showToast('No thumbnail available for this media.', true);
        return;
      }
      fetch('/getthumb?url=' + encodeURIComponent(thumb_url_actual))
        .then(response => {
          if (!response.ok) throw new Error('Failed to fetch thumbnail.');
          return response.blob();
        })
        .then(blob => {
          let a = document.createElement('a');
          a.style.display = 'none';
          a.href = window.URL.createObjectURL(blob);
          let filename = lastFileName ? lastFileName.replace(/\.[^/.]+$/, "") + ".jpg" : "thumbnail.jpg";
          a.download = filename;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(a.href);
          document.body.removeChild(a);
        })
        .catch(() => showToast('Failed to download thumbnail.', true));
    }
    function copyThumbUrl() {
      if(!thumb_url_actual) {
        showToast('No thumbnail URL available.', true);
        return;
      }
      let downloadUrl = location.origin + "/getthumb?url=" + encodeURIComponent(thumb_url_actual);
      let temp = document.createElement("input");
      temp.value = downloadUrl;
      document.body.appendChild(temp);
      temp.select();
      document.execCommand("copy");
      document.body.removeChild(temp);
      showToast("Copied thumbnail download URL: " + temp.value, false);
    }
    document.getElementById('thumb-preview').addEventListener('click', function() { openMediaModal(); });
    function openMediaModal() {
      let thumb = document.getElementById('thumb-preview');
      let path = thumb.getAttribute('data-mediapath');
      let ext  = thumb.getAttribute('data-mediaformat');
      if (!path) return;
      let box = document.getElementById('media-player-box');
      box.innerHTML = '';
      if (ext === 'mp3' || ext === 'm4a') {
        box.innerHTML = `<audio controls autoplay style="width:360px;max-width:93vw;"><source src="${path}" type="audio/${ext == 'mp3' ? 'mpeg' : 'mp4'}"></audio>`;
      } else if (ext === 'mp4') {
        box.innerHTML = `<video controls autoplay style="width:360px;max-width:93vw;"><source src="${path}" type="video/mp4"></video>`;
      } else {
        box.innerHTML = `<div style="color:#fcc; font-weight:bold;">Cannot preview this file type.</div>`;
      }
      document.getElementById('media-modal').classList.add('active');
    }
    function closeMediaModal(event) {
      event.stopPropagation();
      if (event.target.id === 'media-modal' || event.target.id === 'modal-close') {
        document.getElementById('media-modal').classList.remove('active');
        let box = document.getElementById('media-player-box');
        box.innerHTML = '';
      }
    }
  </script>
</body>
</html>
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

def fetch_video_title_and_thumb(url, fmt, mp3quality, mp4quality):
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get("title", "unknown")
            ext = "m4a" if (fmt == "mp3" and mp3quality == "m4a_128") else ("mp3" if fmt == "mp3" else "mp4")
            safe_title = "".join([c if c.isalnum() or c in " ._-()" else "_" for c in title]).strip()
            thumb_url = info.get("thumbnail")
            return safe_title, ext, thumb_url
    except Exception:
        return "unknown", "", None

def download_video(url, fmt, mp3quality, mp4quality, out_path, download_id):
    def hook(d):
        d["download_id"] = download_id
        progress_hook(d)
    if fmt == "mp3":
        if mp3quality == "m4a_128":
            ydl_opts = {
                "format": "bestaudio[ext=m4a]/bestaudio/best",
                "outtmpl": out_path + ".%(ext)s",
                "quiet": True,
                "no_warnings": True,
                "progress_hooks": [hook],
            }
        else:
            q_map = {"mp3_128": "128", "mp3_48": "48", "mp3_256": "256"}
            bitrate = q_map.get(mp3quality, "128")
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": out_path + ".%(ext)s",
                "postprocessors": [
                    {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": bitrate}
                ],
                "quiet": True,
                "no_warnings": True,
                "progress_hooks": [hook],
            }
    else:
        vid_map = {
            "480": "bestvideo[height<=480]+bestaudio/best",
            "720": "bestvideo[height<=720]+bestaudio/best",
            "1080": "bestvideo[height<=1080]+bestaudio/best",
            "1440": "bestvideo[height<=1440]+bestaudio/best",
            "2160": "bestvideo[height<=2160]+bestaudio/best",
        }
        quality = vid_map.get(mp4quality, vid_map["720"])
        ydl_opts = {
            "format": quality,
            "outtmpl": out_path + ".%(ext)s",
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [hook],
        }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

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
            'cookiefile': COOKIES_FILE,
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
    return render_template_string(HTML)

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
    public_url = request.host_url.replace("http://", "https://")
    file_url = f"{public_url}download/{filename}"
    img = qrcode.make(file_url)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, "PNG")
    img_byte_arr.seek(0)
    return send_file(img_byte_arr, mimetype="image/png")

@app.route("/manifest.json")
def serve_manifest():
    return send_from_directory('static', 'manifest.json')

@app.route("/sw.js")
def serve_sw():
    return send_from_directory('static', 'sw.js')

@app.route("/.well-known/assetlinks.json")
def serve_assetlinks():
    return send_from_directory('static/.well-known', 'assetlinks.json', mimetype='application/json')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
