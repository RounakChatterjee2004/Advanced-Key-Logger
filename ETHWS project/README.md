# Advanced Keylogger System with MongoDB Integration

This is a comprehensive monitoring system with a secure Streamlit-based admin dashboard. The system includes a client application for data collection and a dashboard for viewing and managing collected data, supporting both local files and MongoDB-based storage.

## Features

### Admin Dashboard
- Secure login with bcrypt password hashing
- View keyboard logs, screenshots, webcam pictures, and microphone recordings
- Display system information and browser history
- Automatic decryption of encrypted files
- Download all logs as a zip file
- Clean, intuitive user interface
- Multi-user monitoring support with MongoDB

### Client Application
- User-friendly GUI for controlling monitoring
- Selectable monitoring options (keylogging, screenshots, webcam, microphone, etc.)
- Secure data transmission to MongoDB
- Customizable collection intervals
- Minimal resource usage

### Database Integration
- MongoDB support for scalable data storage
- Secure credential management
- Multi-user data separation
- Timestamp-based data retrieval

## Installation

### Admin Dashboard
1. Clone this repository:
```bash
git clone https://github.com/quitehacker/Advanced-Keylogger-with-Webcam-and-Microphone-Spy.git
cd Advanced-Keylogger-with-Webcam-and-Microphone-Spy
```

2. Install required Python dependencies:
```bash
pip install streamlit bcrypt cryptography pillow scipy pymongo dnspython
```

3. Run the dashboard in local file mode (no MongoDB):
```bash
streamlit run app.py
```

4. Or run the MongoDB-enhanced version:
```bash
streamlit run app_mongo.py
```

5. Login with the default credentials:
   - Username: `admin`
   - Password: `P@ssw0rd!`

### Client Application

1. Install Python and required dependencies:
```bash
pip install pymongo pillow cryptography pynput scipy sounddevice opencv-python requests tkinter browserhistory
```

2. Install PyInstaller to build the executable:
```bash
pip install pyinstaller
```

3. Build the client executable:
```bash
python build_exe.py
```

4. Distribute the resulting `SystemMonitor.zip` to target systems

### MongoDB Setup

1. Create a MongoDB Atlas account at https://www.mongodb.com/cloud/atlas
2. Create a new cluster and database
3. Create a database user with read/write permissions
4. Get your MongoDB connection URI from the Atlas dashboard
5. Update the `MONGO_URI` in both `db_utils.py` and `client_keylogger.py`

## Usage

### Admin Dashboard

1. **Login Screen**: Access with admin credentials
2. **Dashboard Navigation**: Use the sidebar to switch between different data views
3. **System Selection**: When using MongoDB, you can select different monitored systems
4. **Data Browsing**: View keystrokes, screenshots, webcam pictures, and other collected data
5. **Data Download**: Use the download option to export data as a ZIP archive

### Client Application

1. **Launch**: Run the SystemMonitor.exe executable
2. **Configure**: Select which monitoring options to enable
3. **Start/Stop**: Use the buttons to control the monitoring process
4. **View Logs**: Basic activity logging is shown in the application window

## Security Considerations

- The admin password is stored using bcrypt hashing for security
- Data transmission to MongoDB uses encrypted connections
- The client application encrypts local data when possible
- All access to the system should be properly authorized
- This system should only be used for legitimate purposes with proper authorization

## Technical Details

- The system uses MongoDB for scalable data storage
- Client-server communication uses PyMongo for database operations
- The client executable is built using PyInstaller
- Streamlit provides the admin dashboard interface
- Monitoring functions run as separate processes to ensure reliability

## Troubleshooting

- **MongoDB Connection Issues**: Verify connection string and network access
- **Client Build Errors**: Ensure all dependencies are installed
- **Data Not Appearing**: Check that the client is actively monitoring
- **Dashboard Login Issues**: Verify credentials and server status
