# Keylogger System - Complete Package

## Overview
This package contains both the client keylogger and the admin dashboard with MongoDB integration.

## Quick Start Guide

### Running the Keylogger Client
1. Navigate to the directory containing SimpleKeylogger.bat
2. Double-click SimpleKeylogger.bat to run the keylogger
3. The keylogger will install required dependencies and start monitoring

### Running the Admin Dashboard
1. Install required packages: `pip install -r requirements.txt`
2. Run the dashboard: `streamlit run app_mongo.py`
3. Log in with default credentials: admin / P@ssw0rd!

## MongoDB Configuration
The system is preconfigured to use the following MongoDB connection:
`mongodb+srv://rounakchatterjee501:rounak501@cluster0.zouzehl.mongodb.net/`

If you want to use your own MongoDB instance:
1. Edit the MONGO_URI in both SimpleKeylogger.py and db_utils.py
2. Restart both the client and dashboard

## Features
- Keylogging: Records all keystrokes with timestamps
- Screenshots: Takes screenshots at regular intervals
- Webcam Capture: Takes photos from webcam periodically
- Microphone Recording: Records audio at intervals
- System Information: Collects detailed system and network info
- Application Tracking: Monitors running applications

## Dashboard Features
- User Management: View all monitored systems
- Data Visualization: Review collected data by category
- Export: Download collected data for offline analysis

## Security Warning
This software should only be used for legitimate monitoring of your own systems or systems you are authorized to monitor.
