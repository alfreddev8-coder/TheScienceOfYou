"""
Music Manager  TheScienceOfYou
Retrieves background music.
"""

import os
import random

def get_background_music():
    """Returns path to a random background music file."""
    music_dir = "bg_music"
    if not os.path.exists(music_dir):
        os.makedirs(music_dir, exist_ok=True)
        return None
    
    files = [os.path.join(music_dir, f) for f in os.listdir(music_dir) 
             if f.endswith(('.mp3', '.wav', '.ogg'))]
    
    if not files:
        return None
    
    return random.choice(files)
