# YouTube Video Downloader

This project is a Python-based application designed to download YouTube videos easily using a browser extension and a backend server. It provides a streamlined workflow where the browser extension serves as a shortcut to trigger the download process via a backend server.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Backend Server](#backend-server)
  - [Browser Extension](#browser-extension)
- [Contributing](#contributing)
- [License](#license)

## Overview

The YouTube Video Downloader consists of two main components:
1. **Python Backend Server**: Receives download requests (including the YouTube video URL and desired format) and downloads the requested file (audio or video).
2. **Browser Extension**: Provides a convenient way to send download requests by offering a quick-access popup in the browser. The extension communicates directly with the backend server to initiate the download process.

### Workflow

1. The user visits a YouTube video and clicks the browser extension icon.
2. The extension shows a popup with options for the desired download format (audio or video).
3. When the user selects the format, the extension sends the YouTube URL and format choice to the backend server.
4. The backend server processes the request and downloads the video or audio based on the format selected.

## Features

- **Download YouTube Videos or Audio**: Choose between downloading full videos or audio-only files.
- **Seamless Integration**: Use the browser extension for quick access to the download functionality.
- **Python Backend**: A lightweight Python server handles the download process behind the scenes.

## Installation

### Prerequisites

- Python 3.x
- Browser supporting extensions (Chrome, Firefox, etc.)

### Backend Server Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/yourusername/ytvd.git
   cd ytvd/backend
   ```

2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Start the backend server:

   ```bash
   python server.py
   ```

   The server will start and listen for download requests.

### Browser Extension Installation

1. Navigate to the `browser_extension` directory:

   ```bash
   cd ytvd/browser_extension
   ```

2. Follow the browser-specific instructions to load the extension:
   - **Chrome**:
     - Open the Extensions page (`chrome://extensions/`).
     - Enable "Developer mode".
     - Click "Load unpacked" and select the `browser_extension` folder.
   - **Firefox**:
     - Open `about:debugging` in Firefox.
     - Click on "This Firefox" in the sidebar.
     - Click "Load Temporary Add-on" and select the `manifest.json` file from the `browser_extension` folder.

## Usage

### Backend Server

Once the server is running, it will listen for download requests from the browser extension. The server expects a request containing the YouTube URL and the download format (either audio or video).

### Browser Extension

1. Navigate to a YouTube video in your browser.
2. Click on the extension icon in your browser toolbar.
3. A popup will appear with format options (audio or video).
4. Select the desired format, and the extension will communicate the request to the backend server.
5. The server will handle the download and save the file locally.

## Contributing

Contributions are welcome! Feel free to submit a pull request or open an issue if you encounter any problems or have suggestions for new features.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.