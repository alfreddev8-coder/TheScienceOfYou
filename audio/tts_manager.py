"""
TTS Manager - TheScienceOfYou
Generates high-quality voiceovers using edge-tts.
Synchronizes subtitles into .srt format.
"""

import asyncio
import os
import edge_tts
from config import TTS_VOICE


def generate_voiceover(text, output_path):
    """
    Synchronous wrapper for async TTS generation.
    Generates both .mp3 and .srt (subtitles).
    """
    srt_path = output_path.replace(".mp3", ".srt")

    # Clean text for TTS - keep ellipses for natural pauses
    clean_text = text.strip()

    try:
        asyncio.run(_async_generate_voiceover(clean_text, output_path, srt_path))
        print(f"[TTS] Generated: {output_path}")
        return output_path, srt_path
    except Exception as e:
        print(f"[TTS] Error: {e}")
        import traceback
        traceback.print_exc()
        return None, None


async def _async_generate_voiceover(text, output_path, srt_path):
    """Async TTS generation compatible with edge-tts v6 and v7."""
    communicate = edge_tts.Communicate(text, TTS_VOICE)
    submaker = edge_tts.SubMaker()

    with open(output_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                try:
                    submaker.feed(chunk)
                except Exception:
                    # Generic fallback within chunk loop
                    pass
            elif chunk["type"] == "SentenceBoundary":
                # Fallback: if we only get sentences, treat them as points for submaker
                # This ensures we at least have sentence-level captions
                try:
                    submaker.feed(chunk)
                except Exception:
                    pass

    # Write SRT - handle both API versions
    try:
        srt_content = submaker.get_srt()
    except Exception:
        srt_content = ""

    # Emergency Fallback: If SRT is still empty, create one giant block for the whole video
    if not srt_content.strip():
        print("[TTS] Warning: SRT still empty. Using single-block fallback.")
        srt_content = f"1\n00:00:00,000 --> 00:00:58,000\n{text}\n"

    with open(srt_path, "w", encoding="utf-8") as srt_file:
        srt_file.write(srt_content)

    print(f"[TTS] SRT written: {srt_path} ({len(srt_content)} chars)")
