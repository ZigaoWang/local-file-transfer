# Local File Transfer

Welcome to **Local File Transfer**, a simple and efficient way to transfer files locally over your network. This tool allows you to upload, download, share, and manage files through a web interface on your local network.

## Features

- **Drag & Drop File Upload**: Easily upload files by dragging them into the web interface.
- **Search Files**: Quickly find files using the built-in search functionality.
- **Download and Share**: Download files or copy their shareable link directly from the interface.
- **File Management**: Delete individual files or clear all files at once.
- **Responsive Design**: A user-friendly interface that works seamlessly on both desktop and mobile devices.

## Getting Started

### Prerequisites

- Python 3.6+
- Flask
- Flask-CORS

### Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/ZigaoWang/local-file-transfer.git
   cd local-file-transfer
   ```

2. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**

   ```bash
   python main.py
   ```

4. **Open the Application**

   The application will open automatically in your default web browser. You can also manually open `http://<local_ip>:5000/` in your browser.

### Directory Structure

```
local-file-transfer/
├── uploads/              # Directory for uploaded files
├── main.py               # Main application script
├── requirements.txt      # Python dependencies
└── README.md             # Project documentation
```

### Usage

#### Upload Files

1. Drag & drop files into the upload section or click the "Select Files" button.
2. The progress bar will show the upload status.
3. Once uploaded, files will be listed in the file list.

#### Search Files

- Use the search bar to filter files by their names.

#### Manage Files

- **Download**: Click the download button to save the file to your device.
- **Share**: Click the share button to copy the file's URL to your clipboard.
- **Delete**: Click the delete button to remove the file.
- **Clear All Files**: Click the "Clear All Files" button to delete all files from the server.

### Customization

- Modify the `UPLOAD_FOLDER` variable in `app.py` to change the upload directory.
- Customize the HTML template and styles in `app.py` to change the appearance.

## Contributing

We welcome contributions! If you would like to contribute, please fork the repository and submit a pull request.

### License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Author

Made with 💜 by Zigao Wang.

## Contact

If you have any questions or feedback, feel free to reach out to Zigao Wang at [a@zigao.wang].