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
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Y', suffix)


# Function to get local IP address
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
        .upload-section {
            margin-bottom: 20px;
            padding: 20px;
            border: 2px dashed #ccc;
            border-radius: 4px;
            text-align: center;
            transition: border-color 0.3s, background-color 0.3s;
        }
        .upload-section.dragging {
            border-color: #007aff;
            background-color: #e6f7ff;
        }
        .upload-section input[type="file"] {
            display: none;
        }
        .upload-button {
            padding: 10px 20px;
            background-color: #007aff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .upload-button:hover {
            background-color: #005bb5;
        }
        .progress-bar {
            display: none;
            width: 100%;
            background-color: #f3f3f3;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 10px;
        }
        .progress-bar div {
            height: 20px;
            background-color: #007aff;
            width: 0%;
            transition: width 0.3s;
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
            flex-wrap: wrap;
        }
        a {
            text-decoration: none;
            color: #007aff;
            word-break: break-all;
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
            flex-wrap: wrap;
        }
        .file-info {
            display: flex;
            flex-direction: column;
        }
        .file-info span {
            font-size: 0.9em;
            color: #666;
        }
        .search-bar {
            margin-bottom: 20px;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 4px;
            width: 100%;
            box-sizing: border-box;
        }
        .sort-buttons {
            margin-bottom: 20px;
        }
        .sort-button {
            padding: 10px;
            background-color: #007aff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 5px;
        }
        .sort-button:hover {
            background-color: #005bb5;
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
    <div class="upload-section" id="upload-section">
        <p>Drag & Drop files here or click to select files</p>
        <input type="file" id="fileElem" multiple>
        <button class="upload-button" onclick="document.getElementById('fileElem').click()">Select Files</button>
        <div class="progress-bar" id="progress-bar">
            <div></div>
        </div>
    </div>
    <input type="text" id="search-bar" class="search-bar" placeholder="Search files...">
    <div class="sort-buttons">
        <button class="sort-button" onclick="sortFiles('name')">Sort by Name</button>
        <button class="sort-button" onclick="sortFiles('size')">Sort by Size</button>
        <button class="sort-button" onclick="sortFiles('date')">Sort by Date</button>
    </div>
    <button class="clear-button" onclick="clearAllFiles()">Clear All Files</button>
    <h2>Available files</h2>
    <ul id="file-list">
    {% if files %}
        {% for file, size, timestamp, is_dir in files %}
            <li>
                <div class="file-details">
                    {% if file.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')) %}
                        <img src="/files/{{ subpath }}/{{ file }}" alt="{{ file }}" class="preview">
                        <div class="file-info">
                            <a href="/files/{{ subpath }}/{{ file }}" target="_blank">{{ file }}</a>
                            <span>{{ size }}, uploaded at {{ timestamp }}</span>
                        </div>
                    {% elif file.endswith(('.mp4', '.mov', '.avi')) %}
                        <div class="icon">
                            <img src="https://img.icons8.com/ios-filled/50/000000/video-file.png" alt="Video">
                        </div>
                        <div class="file-info">
                            <a href="/files/{{ subpath }}/{{ file }}" target="_blank">{{ file }}</a>
                            <span>{{ size }}, uploaded at {{ timestamp }}</span>
                        </div>
                    {% elif file.endswith(('.txt', '.pdf', '.docx')) %}
                        <div class="icon">
                            <img src="https://img.icons8.com/ios-filled/50/000000/document.png" alt="Document">
                        </div>
                        <div class="file-info">
                            <a href="/files/{{ subpath }}/{{ file }}" target="_blank">{{ file }}</a>
                            <span>{{ size }}, uploaded at {{ timestamp }}</span>
                        </div>
                    {% else %}
                        <div class="icon">
                            <img src="https://img.icons8.com/ios-filled/50/000000/file.png" alt="File">
                        </div>
                        <div class="file-info">
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
        const uploadSection = document.getElementById('upload-section');
        const fileElem = document.getElementById('fileElem');
        const localIp = "{{ local_ip }}";
        const progressBar = document.getElementById('progress-bar');
        const searchBar = document.getElementById('search-bar');
        const fileList = document.getElementById('file-list');

        uploadSection.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadSection.classList.add('dragging');
        });

        uploadSection.addEventListener('dragleave', () => {
            uploadSection.classList.remove('dragging');
        });

        uploadSection.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadSection.classList.remove('dragging');
            const files = e.dataTransfer.files;
            handleFiles({ target: { files } });
        });

        fileElem.addEventListener('change', handleFiles);

        searchBar.addEventListener('input', filterFiles);

        function handleFiles(event) {
            const files = event.target.files;
            const formData = new FormData();
            for (let i = 0; i < files.length; i++) {
                formData.append('file', files[i]);
            }
            const xhr = new XMLHttpRequest();
            xhr.open('POST', '/upload', true);
            xhr.upload.onprogress = function(e) {
                if (e.lengthComputable) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    progressBar.style.display = 'block';
                    progressBar.firstElementChild.style.width = percentComplete + '%';
                }
            };
            xhr.onload = function() {
                if (xhr.status === 200) {
                    location.reload();
                } else {
                    alert('Error uploading files');
                }
            };
            xhr.send(formData);
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
            const url = `http://${localIp}:5000/files/${fileName}`;
            navigator.clipboard.writeText(url).then(() => {
                alert('Link copied to clipboard');
            }).catch(err => {
                alert('Error copying link');
            });
        }

        function previewFile(fileName) {
            window.open(`/files/${fileName}`, '_blank');
        }

        function filterFiles() {
            const filter = searchBar.value.toLowerCase();
            const files = fileList.getElementsByTagName('li');
            Array.from(files).forEach((file) => {
                const fileName = file.querySelector('a').textContent.toLowerCase();
                if (fileName.includes(filter)) {
                    file.style.display = '';
                } else {
                    file.style.display = 'none';
                }
            });
        }

        function sortFiles(criteria) {
            const files = Array.from(fileList.getElementsByTagName('li'));
            files.sort((a, b) => {
                const aText = a.querySelector('a').textContent;
                const bText = b.querySelector('a').textContent;
                const aSize = parseFloat(a.querySelector('.file-info span').textContent);
                const bSize = parseFloat(b.querySelector('.file-info span').textContent);
                const aDate = new Date(a.querySelector('.file-info span').textContent);
                const bDate = new Date(b.querySelector('.file-info span').textContent);

                if (criteria === 'name') {
                    return aText.localeCompare(bText);
                } else if (criteria === 'size') {
                    return aSize - bSize;
                } else if (criteria === 'date') {
                    return bDate - aDate;
                }
            });
            files.forEach((file) => fileList.appendChild(file));
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
    local_ip = get_local_ip()
    return render_template_string(html_template, files=files, subpath=subpath, local_ip=local_ip)


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


def open_browser(ip):
    webbrowser.open_new(f'http://{ip}:5000/')


if __name__ == "__main__":
    # Get the local IP address
    local_ip = get_local_ip()
    print(f"Server started at {local_ip}:5000")

    threading.Timer(1, open_browser, args=[local_ip]).start()
    app.run(host='0.0.0.0', port=5000)