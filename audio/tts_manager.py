"""
TTS Manager — TheScienceOfYou
Generates high-quality voiceovers using edge-tts.
Synchronizes subtitles into .srt format.
"""

import asyncio
import os
import re
import edge_tts
from config import TTS_VOICE

def generate_voiceover(text, output_path):
    """
    Synchronous wrapper for async TTS generation.
    Generates both .mp3 and .srt (subtitles).
    """
    srt_path = output_path.replace(".mp3", ".srt")
    
    # Clean text for TTS (remove ... for better flow if needed, but edge-tts handles them well)
    clean_text = text.replace("...", " ").replace("..", " ")
    
    try:
        asyncio.run(_async_generate_voiceover(clean_text, output_path, srt_path))
        print(f"[TTS] Generated: {output_path}")
        return output_path, srt_path
    except Exception as e:
        print(f"[TTS] Error: {e}")
        return None, None

async def _async_generate_voiceover(text, output_path, srt_path):
    communicate = edge_tts.Communicate(text, TTS_VOICE)
    submaker = edge_tts.SubMaker()
    
    with open(output_path, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.feed(chunk)
    
    with open(srt_path, "w", encoding="utf-8") as file:
        file.write(submaker.get_srt())


def get_voice_list():
    """Returns available English voices for reference."""
    try:
        import subprocess
        result = subprocess.run(["edge-tts", "--list-voices"], capture_output=True, text=True)
        print(result.stdout)
    except:
        pass
