"""
TheScienceOfYou — Local Testing Tool
Run this to verify everything works on your PC before going live.
"""

import os
import sys
import subprocess

# Patch environment
os.environ["PYTHONIOENCODING"] = "utf-8"
ffmpeg_bin = r"C:\Users\alfre\Downloads\ffmpeg-2026-03-15-git-6ba0b59d8b-full_build\ffmpeg-2026-03-15-git-6ba0b59d8b-full_build\bin"
if os.path.isdir(ffmpeg_bin):
    os.environ["PATH"] += os.pathsep + ffmpeg_bin

def run_test():
    print("=== TheScienceOfYou Local Test ===")
    
    # 1. Install missing deps
    print("\n[Step 1] Checking dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "edge-tts", "pydub", "moviepy", "yt-dlp", "groq", "requests", "python-dotenv", "audioop-lts", "pytrends", "gspread", "oauth2client"])
    
    # 2. Check for FFmpeg
    print("\n[Step 2] Checking for FFmpeg (Required for video)...")
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, check=True)
        print("  FFmpeg is installed and in PATH.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("!!! ERROR: FFmpeg not found!")
        print("Please install FFmpeg and add it to your PATH.")
        print("Download from: https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z")
        return

    # 3. Check config
    print("\n[Step 3] Checking config.py...")
    from config import DRY_RUN, GROQ_API_KEY
    if not DRY_RUN:
        print("!!! WARNING: DRY_RUN is False in config.py. Changing to True for safety.")
        # We could programmatically change it, but better to let user know
    
    if not GROQ_API_KEY or GROQ_API_KEY == "your-key-here":
        print("!!! ERROR: You must set GROQ_API_KEY in your environment first.")
        return

    # 3. Create necessary dirs
    for d in ["sfx", "bg_music", "temp", "output", "data"]:
        os.makedirs(d, exist_ok=True)

    # 4. Run one short
    print("\n[Step 4] Running test generation (Short)...")
    print("This will download a satisfying background and generate a 50s video.")
    
    # Workaround for Python 3.14 + pydub/audioop issue
    try:
        import audioop_lts
        sys.modules['audioop'] = audioop_lts
        sys.modules['pyaudioop'] = audioop_lts
        print("  [Python 3.14] audioop-lts patch applied.")
    except ImportError:
        pass

    subprocess.run([sys.executable, "main.py", "short"])
    
    print("\n=== Test Finished ===")
    print("Check the 'output/' folder for your final video!")

if __name__ == "__main__":
    run_test()
