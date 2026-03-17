"""
Audio Mixer  TheScienceOfYou
Mixes voice, music, and SFX.
"""

import os
from pydub import AudioSegment
from config import MUSIC_VOLUME_DB

def speed_up_audio(input_path, speed=1.05, output_path="temp/voice_fast.mp3"):
    """Speeds up audio using ffmpeg."""
    os.makedirs("temp", exist_ok=True)
    import subprocess
    try:
        cmd = [
            "ffmpeg", "-i", input_path,
            "-filter:a", f"atempo={speed}",
            "-y", output_path
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return output_path
    except:
        return input_path

def mix_final_audio(voice_path, music_path, env_path, output_path):
    """Mixes voice and background music."""
    try:
        voice = AudioSegment.from_file(voice_path)
        if music_path and os.path.exists(music_path):
            music = AudioSegment.from_file(music_path)
            # Loop music to fit voice duration
            if len(music) < len(voice):
                loops = int(len(voice) / len(music)) + 1
                music = music * loops
            music = music[:len(voice)]
            # Lower volume
            music = music + MUSIC_VOLUME_DB
            # Overlay
            final = music.overlay(voice)
        else:
            final = voice
            
        final.export(output_path, format="mp3")
        return output_path
    except Exception as e:
        print(f"[Mixer] Error: {e}")
        return voice_path
