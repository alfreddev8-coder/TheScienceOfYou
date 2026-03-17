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
    """Async TTS generation with strict word-level popping logic."""
    communicate = edge_tts.Communicate(text, TTS_VOICE)
    
    words_raw = [] 
    sentences_raw = []

    with open(output_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start_ms = chunk["offset"] // 10000
                duration_ms = chunk["duration"] // 10000
                words_raw.append((chunk["text"], start_ms, start_ms + duration_ms))
            elif chunk["type"] == "SentenceBoundary":
                start_ms = chunk["offset"] // 10000
                duration_ms = chunk["duration"] // 10000
                sentences_raw.append((chunk["text"], start_ms, start_ms + duration_ms))

    # Priority: words_raw if not empty, else sentences_raw
    source_data = words_raw if words_raw else sentences_raw
    final_data = []

    if source_data:
        for t_chunk, s_start, s_end in source_data:
            clean_t = t_chunk.strip()
            if not clean_t: continue
            
            # STRICT SPLIT: If a chunk is "But, have we", split into ["But,", "have", "we"]
            bits = clean_t.split()
            if len(bits) > 1:
                dur = s_end - s_start
                total_chars = sum(len(b) for b in bits)
                curr = s_start
                for b in bits:
                    b_dur = (len(b) / total_chars) * dur
                    final_data.append((b, int(curr), int(curr + b_dur)))
                    curr += b_dur
            else:
                final_data.append((clean_t, s_start, s_end))
    else:
        # Fallback for silent/failed data
        print("[TTS] Warning: No timing data found. Using full duration fallback.")
        final_data = [(text, 0, 58000)]

    # Generate SRT formatted content - strictly one word per entry
    srt_lines = []
    for i, (w_text, w_start, w_end) in enumerate(final_data, 1):
        # Prevent zero-length entries
        if w_end <= w_start: w_end = w_start + 100
        
        start_str = format_srt_time(w_start)
        end_str = format_srt_time(w_end)
        srt_lines.append(f"{i}\n{start_str} --> {end_str}\n{w_text}\n")

    srt_content = "\n".join(srt_lines)
    with open(srt_path, "w", encoding="utf-8") as srt_file:
        srt_file.write(srt_content)

    print(f"[TTS] SRT written: {srt_path} ({len(final_data)} words)")
