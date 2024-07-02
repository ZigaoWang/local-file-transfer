import os
from flask import Flask, request, send_from_directory, render_template_string
import webbrowser
import threading
import socket

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# HTML template
html_template = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Local File Transfer</title>
</head>
<body>
    <h1>Local File Transfer</h1>
    <h2>Upload a file</h2>
    <form action="/upload" method="post" enctype="multipart/form-data">
        <input type="file" name="file">
        <input type="submit" value="Upload">
    </form>
    <h2>Available files</h2>
    <ul>
    {% for file in files %}
        <li><a href="/files/{{ file }}">{{ file }}</a></li>
    {% endfor %}
    </ul>
</body>
</html>
"""

@app.route('/')
def index():
    files = os.listdir(UPLOAD_FOLDER)
    return render_template_string(html_template, files=files)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    file.save(os.path.join(UPLOAD_FOLDER, file.filename))
    return 'File uploaded successfully'

@app.route('/files/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

def open_browser(ip):
    webbrowser.open_new(f'http://{ip}:5000/')

if __name__ == "__main__":
    # Get the local IP address
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"Server started at {local_ip}:5000")

    threading.Timer(1, open_browser, args=[local_ip]).start()
    app.run(host='0.0.0.0', port=5000)
