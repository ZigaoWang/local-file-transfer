import os
from flask import Flask, request, send_from_directory, render_template_string, redirect, url_for, flash, jsonify
import webbrowser
import threading
import socket
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_cors import CORS
import mimetypes
import shutil

app = Flask(__name__)
CORS(app)
app.secret_key = 'supersecretkey'  # Needed for flash messages
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Function to convert bytes to human-readable format
def sizeof_fmt(num, suffix='B'):
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Y', suffix)

# HTML template with enhanced styling and functionality
html_template = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Local File Transfer</title>
    <style>
        @font-face {
            font-family: 'San Francisco';
            src: url('https://apple.com/fonts/SanFrancisco/SF-Pro-Text-Regular.otf') format('opentype');
        }
        body {
            font-family: 'San Francisco', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            margin: 20px;
            background-color: #f9f9f9;
            color: #333;
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
            background-color: #007aff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        input[type="submit"]:hover {
            background-color: #005bb5;
        }
        ul {
            list-style-type: none;
            padding: 0;
        }
        li {
            margin-bottom: 10px;
            background-color: white;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 4px;
            display: flex;
            align-items: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        a {
            text-decoration: none;
            color: #007aff;
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
        .delete-button, .download-button, .share-button, .preview-button {
            background-color: #ff3b30;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 5px 10px;
            cursor: pointer;
            margin-left: 5px;
        }
        .download-button { background-color: #34c759; }
        .share-button { background-color: #ff9500; }
        .preview-button { background-color: #ffcc00; }
        .delete-button:hover { background-color: #e60000; }
        .download-button:hover { background-color: #28a745; }
        .share-button:hover { background-color: #e68a00; }
        .preview-button:hover { background-color: #e6b800; }
        .file-details {
            display: flex;
            align-items: center;
            flex-grow: 1;
        }
        .drop-area {
            border: 2px dashed #ccc;
            border-radius: 4px;
            padding: 20px;
            text-align: center;
            color: #999;
            margin-bottom: 20px;
            transition: border-color 0.3s, background-color 0.3s;
        }
        .drop-area.dragging {
            border-color: #007aff;
            background-color: #e6f7ff;
        }
        .preview {
            max-width: 100px;
            max-height: 100px;
            margin-right: 10px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            object-fit: cover;
        }
        .icon {
            width: 100px;
            height: 100px;
            margin-right: 10px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            background-color: #f0f0f0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .icon img {
            max-width: 60%;
            max-height: 60%;
        }
        .clear-button {
            background-color: #ff3b30;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 10px 20px;
            cursor: pointer;
            margin-bottom: 20px;
            display: block;
        }
        .clear-button:hover {
            background-color: #e60000;
        }
        @media (max-width: 600px) {
            .file-details {
                width: 100%;
            }
            li {
                flex-direction: column;
                align-items: flex-start;
            }
            .delete-button, .download-button, .share-button, .preview-button {
                margin-top: 10px;
            }
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
    <div class="drop-area" id="drop-area">
        <p>Drag & Drop files or folders here or click to select</p>
    </div>
    <input type="file" id="fileElem" multiple webkitdirectory directory style="display:none">
    <button class="clear-button" onclick="clearAllFiles()">Clear All Files</button>
    <h2>Available files</h2>
    <ul id="file-list">
    {% if files %}
        {% for file, size, timestamp, is_dir in files %}
            <li>
                <div class="file-details">
                    {% if is_dir %}
                        <div class="icon">
                            <img src="https://img.icons8.com/ios-filled/50/000000/folder-invoices--v1.png" alt="Folder">
                        </div>
                        <div>
                            <a href="/browse/{{ subpath }}/{{ file }}">{{ file }}</a>
                            <span>{{ size }}, uploaded at {{ timestamp }}</span>
                        </div>
                    {% elif file.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')) %}
                        <img src="/files/{{ subpath }}/{{ file }}" alt="{{ file }}" class="preview">
                        <div>
                            <a href="/files/{{ subpath }}/{{ file }}" target="_blank">{{ file }}</a>
                            <span>{{ size }}, uploaded at {{ timestamp }}</span>
                        </div>
                    {% elif file.endswith(('.mp4', '.mov', '.avi')) %}
                        <div class="icon">
                            <img src="https://img.icons8.com/ios-filled/50/000000/video-file.png" alt="Video">
                        </div>
                        <div>
                            <a href="/files/{{ subpath }}/{{ file }}" target="_blank">{{ file }}</a>
                            <span>{{ size }}, uploaded at {{ timestamp }}</span>
                        </div>
                    {% elif file.endswith(('.txt', '.pdf', '.docx')) %}
                        <div class="icon">
                            <img src="https://img.icons8.com/ios-filled/50/000000/document.png" alt="Document">
                        </div>
                        <div>
                            <a href="/files/{{ subpath }}/{{ file }}" target="_blank">{{ file }}</a>
                            <span>{{ size }}, uploaded at {{ timestamp }}</span>
                        </div>
                    {% else %}
                        <div class="icon">
                            <img src="https://img.icons8.com/ios-filled/50/000000/file.png" alt="File">
                        </div>
                        <div>
                            <a href="/files/{{ subpath }}/{{ file }}" target="_blank">{{ file }}</a>
                            <span>{{ size }}, uploaded at {{ timestamp }}</span>
                        </div>
                    {% endif %}
                </div>
                <button class="download-button" onclick="downloadFile('{{ subpath }}/{{ file }}')">Download</button>
                <button class="share-button" onclick="shareFile('{{ subpath }}/{{ file }}')">Share</button>
                <button class="preview-button" onclick="previewFile('{{ subpath }}/{{ file }}')">Preview</button>
                <button class="delete-button" onclick="deleteFile('{{ subpath }}/{{ file }}')">Delete</button>
            </li>
        {% endfor %}
    {% else %}
        <p>No files</p>
    {% endif %}
    </ul>
    <script>
        const dropArea = document.getElementById('drop-area');
        const fileElem = document.getElementById('fileElem');

        dropArea.addEventListener('click', () => fileElem.click());

        fileElem.addEventListener('change', handleFiles);

        dropArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropArea.classList.add('dragging');
        });

        dropArea.addEventListener('dragleave', () => {
            dropArea.classList.remove('dragging');
        });

        dropArea.addEventListener('drop', (e) => {
            e.preventDefault();
            dropArea.classList.remove('dragging');
            const files = e.dataTransfer.files;
            handleFiles({ target: { files } });
        });

        function handleFiles(event) {
            const files = event.target.files;
            const formData = new FormData();
            for (let i = 0; i < files.length; i++) {
                formData.append('file', files[i]);
            }
            fetch('/upload', {
                method: 'POST',
                body: formData
            }).then(response => response.text()).then(data => {
                location.reload();
            }).catch(error => {
                alert('Error uploading files');
            });
        }

        function deleteFile(fileName) {
            if (confirm('Are you sure you want to delete this file?')) {
                fetch(`/delete/${fileName}`, {
                    method: 'DELETE'
                }).then(response => response.text()).then(data => {
                    location.reload();
                }).catch(error => {
                    alert('Error deleting file');
                });
            }
        }

        function clearAllFiles() {
            if (confirm('Are you sure you want to delete all files?')) {
                fetch(`/clear_all`, {
                    method: 'DELETE'
                }).then(response => response.text()).then(data => {
                    location.reload();
                }).catch(error => {
                    alert('Error deleting all files');
                });
            }
        }

        function downloadFile(fileName) {
            window.location.href = `/download/${fileName}`;
        }

        function shareFile(fileName) {
            const url = `${window.location.origin}/files/${fileName}`;
            navigator.clipboard.writeText(url).then(() => {
                alert('Link copied to clipboard');
            }).catch(err => {
                alert('Error copying link');
            });
        }

        function previewFile(fileName) {
            window.open(`/files/${fileName}`, '_blank');
        }
    </script>
</body>
</html>
"""

@app.route('/')
@app.route('/browse/<path:subpath>')
def index(subpath=''):
    abs_path = os.path.join(UPLOAD_FOLDER, subpath)
    files = []
    for f in os.listdir(abs_path):
        full_path = os.path.join(abs_path, f)
        is_dir = os.path.isdir(full_path)
        size = sizeof_fmt(os.path.getsize(full_path) if not is_dir else 0)
        timestamp = datetime.fromtimestamp(os.path.getmtime(full_path)).strftime('%Y-%m-%d %H:%M:%S')
        files.append((f, size, timestamp, is_dir))
    files.sort(key=lambda x: x[2], reverse=True)  # Sort by timestamp, most recent first
    return render_template_string(html_template, files=files, subpath=subpath)

@app.route('/upload', methods=['POST'])
def upload_file():
    files = request.files.getlist('file')
    for file in files:
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(url_for('index'))
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))
    flash('Files uploaded successfully', 'success')
    return redirect(url_for('index'))

@app.route('/files/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/delete/<path:filename>', methods=['DELETE'])
def delete_file(filename):
    try:
        path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        flash('File deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting file: {e}', 'danger')
    return '', 204

@app.route('/clear_all', methods=['DELETE'])
def clear_all_files():
    try:
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            try:
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
            except Exception as e:
                flash(f'Error deleting file: {e}', 'danger')
        flash('All files deleted successfully', 'success')
    except Exception as e:
        flash(f'Error clearing files: {e}', 'danger')
    return '', 204

@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # does not even have to be reachable
        s.connect(('10.254.254.254', 1))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = '127.0.0.1'
    finally:
        s.close()
    return local_ip

def open_browser(ip):
    webbrowser.open_new(f'http://{ip}:5000/')

if __name__ == "__main__":
    # Get the local IP address
    local_ip = get_local_ip()
    print(f"Server started at {local_ip}:5000")

    threading.Timer(1, open_browser, args=[local_ip]).start()
    app.run(host='0.0.0.0', port=5000)