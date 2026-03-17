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


def format_srt_time(ms):
    """Converts milliseconds to SRT time format: HH:MM:SS,mmm"""
    s, ms = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


async def _async_generate_voiceover(text, output_path, srt_path):
    """Async TTS generation with word-level fallback."""
    communicate = edge_tts.Communicate(text, TTS_VOICE)
    
    words_data = [] # List of (word, start_ms, end_ms)
    sentences_data = [] # List of (text, start_ms, end_ms)

    with open(output_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                # Convert 100ns units to ms
                start_ms = chunk["offset"] // 10000
                duration_ms = chunk["duration"] // 10000
                words_data.append((chunk["text"], start_ms, start_ms + duration_ms))
            elif chunk["type"] == "SentenceBoundary":
                start_ms = chunk["offset"] // 10000
                duration_ms = chunk["duration"] // 10000
                sentences_data.append((chunk["text"], start_ms, start_ms + duration_ms))

    srt_lines = []
    
    # Use word data if available, else split sentences
    final_data = []
    if words_data:
        final_data = words_data
    elif sentences_data:
        print("[TTS] No word boundaries found. Splitting sentences manually...")
        for s_text, s_start, s_end in sentences_data:
            s_words = s_text.split()
            if not s_words: continue
            
            s_duration = s_end - s_start
            # Distribute duration based on word length relative to total sentence length
            total_chars = sum(len(w) for w in s_words)
            current_ms = s_start
            for w in s_words:
                w_dur = (len(w) / total_chars) * s_duration
                final_data.append((w, int(current_ms), int(current_ms + w_dur)))
                current_ms += w_dur
    else:
        # Absolute last resort
        print("[TTS] Warning: No timing data found at all.")
        final_data = [(text, 0, 58000)]

    # Generate SRT formatted content
    for i, (w_text, w_start, w_end) in enumerate(final_data, 1):
        start_str = format_srt_time(w_start)
        end_str = format_srt_time(w_end)
        srt_lines.append(f"{i}\n{start_str} --> {end_str}\n{w_text}\n")

    srt_content = "\n".join(srt_lines)
    with open(srt_path, "w", encoding="utf-8") as srt_file:
        srt_file.write(srt_content)

    print(f"[TTS] SRT written: {srt_path} ({len(final_data)} words)")
