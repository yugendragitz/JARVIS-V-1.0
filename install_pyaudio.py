"""
PyAudio Installation Helper for JARVIS
Run this script to attempt installation of PyAudio
"""

import subprocess
import sys
import platform

def main():
    print("=" * 60)
    print("PyAudio Installation Helper for JARVIS")
    print("=" * 60)
    
    python_version = sys.version_info
    print(f"\nPython Version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    print(f"Platform: {platform.system()} {platform.architecture()[0]}")
    
    if python_version.minor >= 14:
        print("\n⚠️  You're running Python 3.14+ (bleeding edge)")
        print("PyAudio may not have pre-built wheels for this version yet.")
        print("\nOptions:")
        print("1. Use Python 3.12 or 3.13 instead (recommended)")
        print("2. Build PyAudio from source (requires Visual Studio Build Tools)")
        print("3. Use JARVIS in text mode: python main.py --text")
        
        print("\n" + "=" * 60)
        print("To install Visual Studio Build Tools:")
        print("1. Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/")
        print("2. Install 'Desktop development with C++'")
        print("3. Then run: pip install pyaudio")
        print("=" * 60)
        return
    
    print("\nAttempting to install PyAudio...")
    
    # Method 1: Direct pip install
    print("\n[Method 1] Trying pip install...")
    result = subprocess.run([sys.executable, "-m", "pip", "install", "pyaudio"], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ PyAudio installed successfully!")
        return
    
    print("❌ Direct pip install failed")
    
    # Method 2: pipwin
    print("\n[Method 2] Trying pipwin...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pipwin"], 
                  capture_output=True, text=True)
    result = subprocess.run(["pipwin", "install", "pyaudio"], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ PyAudio installed via pipwin!")
        return
    
    print("❌ pipwin installation failed")
    
    # Method 3: Download wheel manually
    print("\n[Method 3] Manual wheel installation")
    print("Try downloading a wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio")
    print(f"Look for: PyAudio‑0.2.14‑cp{python_version.major}{python_version.minor}‑...")
    
    print("\n" + "=" * 60)
    print("If all methods fail, run JARVIS in text mode:")
    print("  python main.py --text")
    print("=" * 60)

if __name__ == "__main__":
    main()
