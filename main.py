import os
from flask import Flask, request, send_from_directory, render_template_string, redirect, url_for, flash, jsonify
import webbrowser
import threading
import socket
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_cors import CORS
import mimetypes

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
            justify-content: space-between;
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
        .delete-button {
            background-color: #ff3b30;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 5px 10px;
            cursor: pointer;
        }
        .delete-button:hover {
            background-color: #e60000;
        }
        .file-details {
            display: flex;
            flex-direction: column;
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
        @media (max-width: 600px) {
            .file-details {
                width: 100%;
            }
            li {
                flex-direction: column;
                align-items: flex-start;
            }
            .delete-button {
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
        <p>Drag & Drop files here or click to select files</p>
    </div>
    <input type="file" id="fileElem" multiple style="display:none">
    <h2>Available files</h2>
    <ul id="file-list">
    {% for file, size, timestamp in files %}
        <li>
            <div class="file-details">
                {% if file.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')) %}
                    <img src="/files/{{ file }}" alt="{{ file }}" class="preview">
                {% elif file.endswith(('.mp4', '.mov', '.avi')) %}
                    <div class="icon">
                        <img src="https://img.icons8.com/ios-filled/50/000000/video-file.png" alt="Video">
                    </div>
                {% elif file.endswith(('.txt', '.pdf', '.docx')) %}
                    <div class="icon">
                        <img src="https://img.icons8.com/ios-filled/50/000000/document.png" alt="Document">
                    </div>
                {% else %}
                    <div class="icon">
                        <img src="https://img.icons8.com/ios-filled/50/000000/file.png" alt="File">
                    </div>
                {% endif %}
                <div>
                    <a href="/files/{{ file }}">{{ file }}</a>
                    <span>{{ size }}, uploaded at {{ timestamp }}</span>
                </div>
            </div>
            <button class="delete-button" onclick="deleteFile('{{ file }}')">Delete</button>
        </li>
    {% endfor %}
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
            fetch(`/delete/${fileName}`, {
                method: 'DELETE'
            }).then(response => response.text()).then(data => {
                location.reload();
            }).catch(error => {
                alert('Error deleting file');
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    files = [(f, sizeof_fmt(os.path.getsize(os.path.join(UPLOAD_FOLDER, f))), datetime.fromtimestamp(os.path.getmtime(os.path.join(UPLOAD_FOLDER, f))).strftime('%Y-%m-%d %H:%M:%S')) for f in os.listdir(UPLOAD_FOLDER)]
    return render_template_string(html_template, files=files)

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

@app.route('/files/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    try:
        os.remove(os.path.join(UPLOAD_FOLDER, filename))
        flash('File deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting file: {e}', 'danger')
    return '', 204

def open_browser(ip):
    webbrowser.open_new(f'http://{ip}:5000/')

if __name__ == "__main__":
    # Get the local IP address
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"Server started at {local_ip}:5000")

    threading.Timer(1, open_browser, args=[local_ip]).start()
    app.run(host='0.0.0.0', port=5000)