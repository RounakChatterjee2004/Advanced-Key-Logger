# Advanced System Monitor (Keylogger)

## Overview
This is a comprehensive system monitoring tool with capabilities to:
- Log keystrokes
- Capture screenshots
- Record from webcam
- Record from microphone
- Collect system information
- Track application usage

All data is stored both locally and in MongoDB.

## Quick Start (Windows)

### Option 1: Run Directly (Simplest)
1. Download both `SimpleKeylogger.py` and `SimpleKeylogger.bat`
2. Place them in the same folder
3. Double-click on `SimpleKeylogger.bat`
4. The batch file will:
   - Check if Python is installed
   - Install required dependencies
   - Start the keylogger application

### Option 2: Run Python Script Directly
1. Ensure Python 3.8+ is installed
2. Install dependencies: `pip install pymongo pynput pillow requests`
3. Optionally install: `pip install opencv-python scipy sounddevice`
4. Run: `python SimpleKeylogger.py`

## Features and Functionality

- **Keylogging**: Records all keystrokes with timestamps
- **Screenshots**: Takes screenshots at regular intervals
- **Webcam Capture**: Takes photos from webcam periodically
- **Microphone Recording**: Records audio at intervals
- **System Information**: Collects detailed system and network info
- **Application Tracking**: Monitors running applications

## Data Storage

### Local Storage
All collected data is stored locally in the following directory:
`C:\Users\[Username]\Documents\SystemLogs\`

### MongoDB Storage
Data is also sent to MongoDB using the following connection:
`mongodb+srv://rounakchatterjee501:rounak501@cluster0.zouzehl.mongodb.net/`

## Viewing Collected Data

To view the collected data, use the admin dashboard:
- See the admin_dashboard files in the original package
- Run: `streamlit run app_mongo.py`
- Login with: admin / P@ssw0rd!

## Important Notes

1. This tool should only be used for legitimate monitoring purposes
2. Unauthorized monitoring of computer systems may be illegal
3. Features requiring optional packages will be disabled if those packages aren't installed

## Troubleshooting

- **Missing Features**: Some features like webcam or microphone recording require additional packages
- **MongoDB Connection Error**: The application will still work in local-only mode if MongoDB is unavailable