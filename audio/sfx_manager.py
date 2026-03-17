"""
SFX Manager  TheScienceOfYou
Manages SFX timestamps and overlays.
"""

import os
import json
import re

def clean_sfx_library():
    """Placeholder for SFX cleaning logic."""
    print("[SFX] Cleaning library (placeholder)")
    pass

def calculate_sfx_timestamps(script, timeline, audio_duration_ms):
    """
    Calculates exact millisecond timestamps for SFX based on trigger phrases.
    """
    if not timeline or not script:
        return []
    
    results = []
    # Very basic estimation: (word_index / total_words) * duration
    words = script.split()
    total_words = len(words)
    
    for item in timeline:
        phrase = item.get("trigger_phrase", "")
        sound = item.get("sound", "")
        if phrase and sound:
            try:
                # Find phrase position
                phrase_idx = script.find(phrase)
                if phrase_idx != -1:
                    ratio = phrase_idx / len(script)
                    timestamp_ms = int(ratio * audio_duration_ms)
                    results.append({
                        "timestamp_ms": timestamp_ms,
                        "sound": sound,
                        "volume": item.get("volume", 0.5)
                    })
            except:
                continue
    return results

def overlay_sfx_on_audio(audio_path, sfx_data, output_path):
    """Overlays SFX onto voiceover."""
    from pydub import AudioSegment
    try:
        voice = AudioSegment.from_file(audio_path)
        for sfx in sfx_data:
            sound_name = sfx.get('sound') or sfx.get('sfx')
            if not sound_name:
                continue
                
            sfx_file = f"sfx/{sound_name}.mp3"
            if os.path.exists(sfx_file):
                effect = AudioSegment.from_file(sfx_file)
                # Adjust volume
                vol = sfx.get('volume', 0.5)
                effect = effect + (20 * vol - 10) 
                voice = voice.overlay(effect, position=sfx.get('timestamp_ms', 0))
        
        voice.export(output_path, format="mp3")
        return output_path
    except Exception as e:
        print(f"[SFX] Overlay error: {e}")
        import shutil
        shutil.copy2(audio_path, output_path)
        return output_path
