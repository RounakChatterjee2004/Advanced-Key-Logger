import os
import zipfile
import shutil

def create_simple_package():
    """Create a simple package with the minimal files needed to run the keylogger"""
    print("Creating Simple Keylogger Package...")
    
    # Files to include
    files_to_include = [
        "SimpleKeylogger.py",
        "SimpleKeylogger.bat",
        "SimpleKeylogger_README.md"
    ]
    
    # Create a ZIP file
    zip_filename = "SimpleKeylogger.zip"
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in files_to_include:
            if os.path.exists(file):
                zipf.write(file)
            else:
                print(f"Warning: {file} not found")
    
    print(f"Package created: {zip_filename}")
    print("Download this file, extract it, and run SimpleKeylogger.bat")
    
    return zip_filename

if __name__ == "__main__":
    create_simple_package()