"""
Audio Mixer  TheScienceOfYou
Mixes voice, music, and SFX.
"""

import os
from pydub import AudioSegment
from config import MUSIC_VOLUME_DB

def speed_up_audio(input_path, speed=1.15, output_path="temp/voice_fast.mp3", srt_path=None):
    """Speeds up audio using ffmpeg and scales SRT timestamps to match."""
    os.makedirs("temp", exist_ok=True)
    import subprocess
    import re
    
    try:
        # 1. Speed up audio
        cmd = [
            "ffmpeg", "-i", input_path,
            "-filter:a", f"atempo={speed}",
            "-y", output_path
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        # 2. Scale SRT if provided
        if srt_path and os.path.exists(srt_path):
            with open(srt_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            def scale_time(match):
                # HH:MM:SS,mmm
                h, m, s, ms = map(int, re.split('[:|,]', match.group(0)))
                total_ms = (h * 3600000) + (m * 60000) + (s * 1000) + ms
                scaled_ms = int(total_ms / speed)
                
                s, ms = divmod(scaled_ms, 1000)
                m, s = divmod(s, 60)
                h, m = divmod(m, 60)
                return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

            # Regex for SRT timestamps: 00:00:00,000
            time_pattern = r"\d{2}:\d{2}:\d{2},\d{3}"
            scaled_content = re.sub(time_pattern, scale_time, content)
            
            with open(srt_path, "w", encoding="utf-8") as f:
                f.write(scaled_content)
            print(f"[Mixer] Scaled SRT timestamps by 1/{speed}")

        return output_path
    except Exception as e:
        print(f"[Mixer] Speed-up error: {e}")
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
