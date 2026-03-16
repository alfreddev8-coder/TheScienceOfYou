"""
Video Assembler — TheScienceOfYou
Assembles vertical 9:16 videos for Shorts (single clip)
and horizontal/vertical for Long-form (multiple clips).
"""

import os
import subprocess
from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeVideoClip,
    concatenate_videoclips, TextClip
)
from config import TARGET_WIDTH, TARGET_HEIGHT, TARGET_FPS, ZOOM_FACTOR


def process_background_to_vertical(bg_path: str, target_duration: float):
    """
    Processes background video to VERTICAL 9:16 (1080x1920).
    120% zoom to fill screen and alter content.
    Centers on the interesting part of the clip.
    """
    bg = VideoFileClip(bg_path)
    sw, sh = bg.size
    sr = sw / sh
    tr = TARGET_WIDTH / TARGET_HEIGHT
    
    print(f"[Video] Source: {sw}x{sh}, Target: {TARGET_WIDTH}x{TARGET_HEIGHT}")
    
    if sr > tr:
        scale_h = TARGET_HEIGHT * ZOOM_FACTOR
        scale_w = scale_h * sr
    elif sr < tr:
        scale_w = TARGET_WIDTH * ZOOM_FACTOR
        scale_h = scale_w / sr
    else:
        scale_w = TARGET_WIDTH * ZOOM_FACTOR
        scale_h = TARGET_HEIGHT * ZOOM_FACTOR
    
    bg = bg.resize((int(scale_w), int(scale_h)))
    
    cw, ch = bg.size
    cx, cy = cw / 2, ch / 2
    y_off = -int(ch * 0.02)
    
    x1 = max(0, int(cx - TARGET_WIDTH / 2))
    y1 = max(0, int(cy - TARGET_HEIGHT / 2) + y_off)
    x2 = x1 + TARGET_WIDTH
    y2 = y1 + TARGET_HEIGHT
    
    if x2 > cw: x1, x2 = max(0, cw - TARGET_WIDTH), cw
    if y2 > ch: y1, y2 = max(0, ch - TARGET_HEIGHT), ch
    
    bg = bg.crop(x1=x1, y1=y1, x2=x2, y2=y2)
    
    if bg.size != (TARGET_WIDTH, TARGET_HEIGHT):
        bg = bg.resize((TARGET_WIDTH, TARGET_HEIGHT))
    
    if bg.duration < target_duration:
        loops = int(target_duration / bg.duration) + 1
        bg = concatenate_videoclips([bg] * loops)
    
    bg = bg.subclip(0, target_duration)
    print(f"[Video] Processed: {TARGET_WIDTH}x{TARGET_HEIGHT}, {bg.duration:.1f}s, {ZOOM_FACTOR*100:.0f}% zoom")
    
    return bg


def assemble_short(bg_video_path: str, audio_path: str, output_path: str) -> bool:
    """Assembles a Short: single background + mixed audio."""
    try:
        audio = AudioFileClip(audio_path)
        duration = audio.duration
        
        bg = process_background_to_vertical(bg_video_path, duration)
        bg = bg.without_audio()
        final = bg.set_audio(audio)
        
        # Watermark via FFmpeg later (no ImageMagick dependency)
        
        print(f"[Assembly] Rendering Short...")
        final.write_videofile(
            output_path, codec="libx264", audio_codec="aac",
            preset="medium", threads=2, fps=TARGET_FPS, logger=None
        )
        
        audio.close(); bg.close(); final.close()
        
        size = os.path.getsize(output_path) / (1024*1024)
        print(f"[Assembly] Short ready: {size:.1f}MB")
        return True
        
    except Exception as e:
        print(f"[Assembly] Error: {e}")
        import traceback; traceback.print_exc()
        return False


def assemble_longform(clip_paths: list, audio_path: str, output_path: str) -> bool:
    """Assembles long-form: multiple Pexels clips + mixed audio."""
    try:
        audio = AudioFileClip(audio_path)
        duration = audio.duration
        
        clips = []
        for cp in clip_paths:
            try:
                c = VideoFileClip(cp)
                if c.duration and c.duration > 0.5:
                    clips.append(c)
            except:
                continue
        
        if not clips:
            print("[Assembly] No valid clips")
            return False
        
        # Calculate how long each clip should play
        clip_duration = duration / len(clips)
        
        processed = []
        for c in clips:
            if c.duration > clip_duration:
                c = c.subclip(0, clip_duration)
            processed.append(c.resize((1920, 1080)))  # 16:9 for long-form
        
        bg = concatenate_videoclips(processed, method="compose")
        
        if bg.duration < duration:
            loops = int(duration / bg.duration) + 1
            bg = concatenate_videoclips([bg] * loops, method="compose")
        
        bg = bg.subclip(0, duration)
        bg = bg.without_audio()
        final = bg.set_audio(audio)
        
        final.write_videofile(
            output_path, codec="libx264", audio_codec="aac",
            preset="medium", threads=2, fps=30, logger=None
        )
        
        audio.close(); bg.close(); final.close()
        for c in clips: c.close()
        
        size = os.path.getsize(output_path) / (1024*1024)
        print(f"[Assembly] Long-form ready: {size:.1f}MB")
        return True
        
    except Exception as e:
        print(f"[Assembly] Long-form error: {e}")
        return False


def add_watermark_ffmpeg(video_path: str, text: str = "TheScienceOfYou", opacity: float = 0.20) -> bool:
    """Adds watermark using FFmpeg (no ImageMagick needed)."""
    output = video_path.replace(".mp4", "_wm.mp4")
    try:
        cmd = [
            "ffmpeg", "-i", video_path,
            "-vf", f"drawtext=text='{text}':fontsize=18:fontcolor=white@{opacity}:x=w-tw-20:y=h-th-20:fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "-c:a", "copy", "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-y", output
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if os.path.exists(output) and os.path.getsize(output) > 100000:
            os.remove(video_path)
            os.rename(output, video_path)
            print("[Watermark] Added")
            return True
        if os.path.exists(output): os.remove(output)
        return False
    except:
        if os.path.exists(output): os.remove(output)
        return False


def apply_visual_enhancements(video_path: str) -> bool:
    """Applies warm bright color grading for health content."""
    output = video_path.replace(".mp4", "_enhanced.mp4")
    try:
        # Warm, bright, slightly saturated — opposite of dark psychology
        cmd = [
            "ffmpeg", "-i", video_path,
            "-vf", "eq=brightness=0.04:contrast=1.12:saturation=1.08,vignette=PI/5,unsharp=3:3:0.3:3:3:0.0",
            "-c:a", "copy", "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-y", output
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if os.path.exists(output) and os.path.getsize(output) > 100000:
            os.remove(video_path)
            os.rename(output, video_path)
            print("[Enhance] Visual enhancements applied")
            return True
        if os.path.exists(output): os.remove(output)
        return False
    except:
        if os.path.exists(output): os.remove(output)
        return False


def ensure_shorts_duration(video_path: str, max_dur: float = 58.0) -> str:
    """Trims video if over 58 seconds."""
    try:
        v = VideoFileClip(video_path)
        if v.duration <= max_dur:
            v.close()
            return video_path
        print(f"[Duration] {v.duration:.1f}s → trimming to {max_dur}s")
        trimmed = video_path.replace(".mp4", "_trim.mp4")
        t = v.subclip(0, max_dur)
        t.write_videofile(trimmed, codec="libx264", audio_codec="aac",
                         preset="medium", threads=2, logger=None)
        v.close(); t.close()
        os.remove(video_path)
        os.rename(trimmed, video_path)
        return video_path
    except:
        return video_path
