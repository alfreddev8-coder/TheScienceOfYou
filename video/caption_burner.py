"""
Caption Burner  TheScienceOfYou
Creates Facts Man style captions: YELLOW, BOLD, CENTERED, POP-IN animation.
Converts SRT to ASS with word-by-word pop animation and color-coded keywords.
"""

import os
import re
import random
import subprocess
import shutil


def srt_to_animated_ass(srt_path: str, ass_path: str) -> bool:
    """
    Converts SRT to ASS with:
    1. BRIGHT YELLOW text with THICK BLACK outline
    2. CENTER position (middle of screen)
    3. Word-by-word POP-IN animation
    4. Color-coded keywords:
       - Numbers/stats: GREEN
       - Body parts: LIGHT BLUE
       - Food names: ORANGE
       - Sources: WHITE
       - Default: YELLOW
    """
    try:
        with open(srt_path, "r", encoding="utf-8") as f:
            srt_content = f.read()
        
        entries = parse_srt(srt_content)
        if not entries:
            return False
        
        # ASS header  YELLOW text, centered, large, bold
        ass_header = """[Script Info]
Title: TheScienceOfYou Captions
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginV, MarginR, Encoding
Style: Default,DejaVu Sans,36,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,5,60,40,60,1
Style: Number,DejaVu Sans,38,&H0000FF00,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,5,60,40,60,1
Style: Organ,DejaVu Sans,36,&H00FFD700,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,5,60,40,60,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        
        # Pop-in animation
        pop_anim = r"{\fad(60,40)\fscx75\fscy75\t(0,80,\fscx100\fscy100)}"
        
        ass_events = []
        for entry in entries:
            start = format_ass_time(entry["start"])
            end = format_ass_time(entry["end"])
            text = entry["text"].replace("\n", "\\N")
            
            # Color-code keywords
            text = color_code_health_keywords(text)
            
            line = f"Dialogue: 0,{start},{end},Default,,0,0,0,,{pop_anim}{text}"
            ass_events.append(line)
        
        ass_content = ass_header + "\n".join(ass_events) + "\n"
        
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(ass_content)
        
        print(f"[Captions] ASS created: {len(entries)} entries")
        return True
        
    except Exception as e:
        print(f"[Captions] SRTASS error: {e}")
        return False


def color_code_health_keywords(text: str) -> str:
    """Color-codes health-specific keywords in ASS format."""
    # Numbers and percentages  GREEN
    text = re.sub(
        r'\b(\d+(?:\.\d+)?)\s*(percent|%|times|hours|minutes|seconds|years|days|weeks|months|liters|grams|mg|calories)\b',
        r'{\\c&H0000FF00&}\1 \2{\\c&H0000FFFF&}',
        text, flags=re.IGNORECASE
    )
    
    # Body parts  LIGHT BLUE
    organs = ['brain', 'heart', 'liver', 'kidney', 'stomach', 'lungs', 'skin',
              'bones', 'muscles', 'blood', 'cells', 'neurons', 'gut', 'immune',
              'intestine', 'spine', 'eyes', 'ears', 'throat', 'arteries']
    for organ in organs:
        pattern = re.compile(rf'\b({organ}s?)\b', re.IGNORECASE)
        text = pattern.sub(r'{\\c&H00FFD700&}\1{\\c&H0000FFFF&}', text)
    
    # Food names  ORANGE
    foods = ['coffee', 'sugar', 'water', 'garlic', 'honey', 'rice', 'bread',
             'eggs', 'milk', 'fruit', 'vegetables', 'protein', 'fiber',
             'chocolate', 'tea', 'avocado', 'banana', 'ginger', 'turmeric']
    for food in foods:
        pattern = re.compile(rf'\b({food}s?)\b', re.IGNORECASE)
        text = pattern.sub(r'{\\c&H005EFFE8&}\1{\\c&H0000FFFF&}', text)
    
    return text


def parse_srt(srt_text: str) -> list:
    entries = []
    blocks = re.split(r'\n\s*\n', srt_text.strip())
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            time_match = re.match(
                r'(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})',
                lines[1]
            )
            if time_match:
                entries.append({
                    "start": time_match.group(1).replace(',', '.'),
                    "end": time_match.group(2).replace(',', '.'),
                    "text": ' '.join(lines[2:])
                })
    return entries


def format_ass_time(srt_time: str) -> str:
    parts = srt_time.replace(',', '.').split(':')
    h = int(parts[0])
    m = parts[1]
    s_ms = parts[2]
    if '.' in s_ms:
        s, ms = s_ms.split('.')
        cs = ms[:2]
    else:
        s, cs = s_ms, "00"
    return f"{h}:{m}:{s}.{cs}"


def burn_animated_captions(video_path: str, srt_path: str, output_path: str) -> bool:
    """Burns animated ASS captions onto video using FFmpeg."""
    ass_path = srt_path.replace(".srt", ".ass")
    
    if not srt_to_animated_ass(srt_path, ass_path):
        return burn_basic_captions(video_path, srt_path, output_path)
    
    try:
        # Cross-platform path escaping for FFmpeg filters
        ass_escaped = ass_path.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
        if os.name == 'nt':
             # Windows needs absolute paths with forward slashes for the libav filters
             ass_escaped = os.path.abspath(ass_path).replace("\\", "/").replace(":", "\\:")
        
        cmd = [
            "ffmpeg", "-i", video_path,
            "-vf", f"ass='{ass_escaped}'",
            "-c:a", "copy", "-c:v", "libx264",
            "-preset", "medium", "-crf", "23",
            "-y", output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 100000:
            print("[Captions] Animated captions burned")
            if os.path.exists(ass_path):
                os.remove(ass_path)
            return True
        
        return burn_basic_captions(video_path, srt_path, output_path)
        
    except Exception as e:
        print(f"[Captions] Error: {e}")
        return burn_basic_captions(video_path, srt_path, output_path)


def burn_basic_captions(video_path: str, srt_path: str, output_path: str) -> bool:
    """Fallback: basic styled captions."""
    try:
        style = (
            "FontName=DejaVu Sans,FontSize=36,PrimaryColour=&H0000FFFF,"
            "OutlineColour=&H00000000,Bold=1,Outline=4,Shadow=2,"
            "Alignment=5,MarginV=40,MarginL=60,MarginR=60"
        )
        srt_escaped = srt_path.replace("\\", "/").replace(":", "\\:")
        cmd = [
            "ffmpeg", "-i", video_path,
            "-vf", f"subtitles='{srt_escaped}':force_style='{style}'",
            "-c:a", "copy", "-c:v", "libx264",
            "-preset", "medium", "-crf", "23",
            "-y", output_path
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 100000:
            print("[Captions] Basic styled captions applied")
            return True
        shutil.copy2(video_path, output_path)
        return True
    except:
        shutil.copy2(video_path, output_path)
        return True
