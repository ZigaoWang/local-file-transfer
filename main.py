import os
from flask import Flask, request, send_from_directory, render_template_string, redirect, url_for, flash
import webbrowser
import threading
import socket
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flash messages
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# HTML template with enhanced styling and functionality
html_template = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Local File Transfer</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
        }
        h1, h2 {
            color: #333;
        }
        form {
            margin-bottom: 20px;
        }
        input[type="file"] {
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 4px;
        }
        input[type="submit"] {
            padding: 10px 20px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        input[type="submit"]:hover {
            background-color: #45a049;
        }
        ul {
            list-style-type: none;
            padding: 0;
        }
        li {
            margin-bottom: 10px;
        }
        a {
            text-decoration: none;
            color: #4CAF50;
        }
        a:hover {
            text-decoration: underline;
        }
        .alert {
            padding: 15px;
            background-color: #f44336;
            color: white;
            margin-bottom: 20px;
        }
        .alert.success {
            background-color: #4CAF50;
        }
    </style>
</head>
<body>
    <h1>Local File Transfer</h1>
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div class="alert {{ category }}">{{ message }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    <h2>Upload a file</h2>
    <form action="/upload" method="post" enctype="multipart/form-data">
        <input type="file" name="file">
        <input type="submit" value="Upload">
    </form>
    <h2>Available files</h2>
    <ul>
    {% for file, size, timestamp in files %}
        <li>
            <a href="/files/{{ file }}">{{ file }}</a> ({{ size }} bytes, uploaded at {{ timestamp }})
        </li>
    {% endfor %}
    </ul>
    <form action="/download_all" method="post">
        <input type="submit" value="Download All Files">
    </form>
</body>
</html>
"""

@app.route('/')
def index():
    files = [(f, os.path.getsize(os.path.join(UPLOAD_FOLDER, f)), datetime.fromtimestamp(os.path.getmtime(os.path.join(UPLOAD_FOLDER, f))).strftime('%Y-%m-%d %H:%M:%S')) for f in os.listdir(UPLOAD_FOLDER)]
    return render_template_string(html_template, files=files)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('index'))
    file.save(os.path.join(UPLOAD_FOLDER, file.filename))
    flash('File uploaded successfully', 'success')
    return redirect(url_for('index'))

@app.route('/files/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/download_all', methods=['POST'])
def download_all():
    # Logic to download all files as a zip (not implemented for simplicity)
    flash('Download all files functionality is not implemented yet', 'danger')
    return redirect(url_for('index'))

def open_browser(ip):
    webbrowser.open_new(f'http://{ip}:5000/')

if __name__ == "__main__":
    # Get the local IP address
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"Server started at {local_ip}:5000")

    threading.Timer(1, open_browser, args=[local_ip]).start()
    app.run(host='0.0.0.0', port=5000)
