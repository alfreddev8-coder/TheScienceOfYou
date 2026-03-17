"""
Shared Utilities  TheScienceOfYou
"""

import sys
import shutil

def get_ytdlp_cmd():
    """Gets the correct yt-dlp command for the current platform."""
    # Try direct command first
    if shutil.which("yt-dlp"):
        return ["yt-dlp"]
    # Fallback: call as Python module
    return [sys.executable, "-m", "yt_dlp"]
