"""
TheScienceOfYou  Main Automation Pipeline
Health Science YouTube Channel

Daily: 5 Shorts + 2 Long-form
"""

import os
import sys

# --- MONKEY PATCH FOR MOVIEPY PIL DEPENDENCY (Pillow >= 10) ---
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS
# --------------------------------------------------------------

# Set console to UTF-8 for emojis
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Fallback for older python
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import json
import gc
import shutil

# Ensure tracking files exist
def ensure_tracking_files():
    """Ensure all required tracking files exist and are valid."""
    os.makedirs("data", exist_ok=True)
    os.makedirs("temp", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    
    track_files = [
        "data/used_topics.json", 
        "data/used_kuaishou_videos.json",
        "data/used_music.json", 
        "data/video_database.json",
        "data/sfx_manifest.json", 
        "data/pending_series.json",
        "posted_videos.json" # Root tracking file
    ]
    
    for f in track_files:
        if not os.path.exists(f) or os.path.getsize(f) == 0:
            with open(f, "w") as fp:
                if "manifest" in f:
                    json.dump({}, fp)
                else:
                    json.dump([], fp)
            print(f"[Init] Created {f}")
        else:
            try:
                with open(f, "r") as fp:
                    json.load(fp)
            except json.JSONDecodeError:
                with open(f, "w") as fp:
                    json.dump({}, fp if "manifest" in f else [], fp)
                print(f"[Init] Reset corrupted {f}")

ensure_tracking_files()

from core.content_source import get_next_topic
from core.ai_content import (
    generate_short_content, generate_longform_content,
    create_seo_filename, fix_description
)
from audio.sfx_manager import clean_sfx_library, calculate_sfx_timestamps, overlay_sfx_on_audio
from audio.tts_manager import generate_voiceover
from audio.audio_mixer import speed_up_audio, mix_final_audio
from audio.music_manager import get_background_music
from video.kuaishou_source import get_satisfying_background, cleanup_old_bg
from video.pexels_source import get_longform_background_clips, get_shorts_fallback_clip, cleanup_pexels_clips
from video.video_assembler import (
    assemble_short, assemble_longform,
    add_watermark_ffmpeg, apply_visual_enhancements, ensure_shorts_duration
)
from video.caption_burner import burn_animated_captions
from video.thumbnail_generator import generate_thumbnail
from upload.comment_bot import post_pinned_comment
from upload.youtube_uploader import upload_video, set_thumbnail, authenticate_youtube
from config import DRY_RUN, VOICEOVER_SPEED, CHANNEL_NAME, CHANNEL_HANDLE


def create_short(playlist: str = None):
    """Creates and uploads ONE Short video."""
    print(f"\n{'='*50}")
    print(f"  TheScienceOfYou  Creating Short ({playlist or 'auto'})")
    print(f"{'='*50}\n")
    
    # Step 1: Get topic
    print("[1/12] Getting topic...")
    topic_data = get_next_topic(playlist)
    print(f"  Topic: {topic_data['topic'][:60]}...")
    
    # Step 2: Generate AI content
    print("[2/12] Generating AI script...")
    content = generate_short_content(topic_data)
    if not content:
        print("[FATAL] Content generation failed")
        return False
    print(f"  Title: {content.get('title', 'N/A')}")
    print(f"  Words: {len(content.get('script', '').split())}")
    
    # Step 3: TTS voiceover
    print("[3/12] Generating high-quality voiceover...")
    voiceover_raw = "temp/voiceover_raw.mp3"
    voice_path, srt_path = generate_voiceover(content["script"], voiceover_raw)
    
    if not voice_path or not os.path.exists(voice_path):
        print("  [Error] TTS failed")
        return False
    
    # Step 4: Speed up
    print(f"[4/12] Speeding up ({VOICEOVER_SPEED}x) & Scaling subtitles...")
    fast_voice = speed_up_audio(voiceover_raw, VOICEOVER_SPEED, "temp/voiceover_fast.mp3", srt_path=srt_path)
    
    # Step 5: SFX overlay
    print("[5/12] Overlaying SFX...")
    from pydub import AudioSegment
    audio = AudioSegment.from_file(fast_voice)
    sfx_ts = calculate_sfx_timestamps(content["script"], content.get("sfx_timeline", []), len(audio))
    sfx_voice = "temp/voiceover_sfx.mp3"
    if sfx_ts:
        overlay_sfx_on_audio(fast_voice, sfx_ts, sfx_voice)
    else:
        shutil.copy2(fast_voice, sfx_voice)
    
    # Step 6: Background music
    print("[6/12] Getting background music...")
    music_path = get_background_music()
    
    # Step 7: Mix audio
    print("[7/12] Mixing audio...")
    final_audio = mix_final_audio(sfx_voice, music_path, None, "temp/final_audio.mp3")
    
    # Step 8: Background video from TikTok Accounts
    print("[8/12] Getting satisfying background...")
    try:
        bg_path = get_satisfying_background()
    except Exception as e:
        print(f"  [Error] Background sourcing failed: {e}")
        bg_path = None
    
    credits = []
    
    if not bg_path:
        print("  TikTok accounts failed, trying Pexels fallback...")
        try:
            from video.pexels_source import get_shorts_fallback_clip
            bg_path, fallback_credits = get_shorts_fallback_clip(topic_data.get("topic", "satisfying health science"))
            if fallback_credits:
                credits.extend(fallback_credits)
        except Exception as e:
            print(f"  [Error] Pexels fallback failed: {e}")
    
    if not bg_path:
        print("[FATAL] No background video available. Cannot continue.")
        return False
    
    # Step 9: Assemble vertical video
    print("[9/12] Assembling 9:16 vertical video (120% zoom)...")
    seo_filename = create_seo_filename(content.get("title", "health-science"))
    output_path = f"output/{seo_filename}"
    
    intermediate = "temp/intermediate.mp4"
    if not assemble_short(bg_path, final_audio or sfx_voice, intermediate):
        return False
    
    # Step 10: Visual enhancements + watermark
    print("[10/12] Enhancing visuals + watermark...")
    apply_visual_enhancements(intermediate)
    add_watermark_ffmpeg(intermediate, "TheScienceOfYou", 0.20)
    
    # Step 11: Burn captions
    print("[11/12] Burning yellow pop-in captions...")
    burn_animated_captions(intermediate, srt_path, output_path)
    
    # Step 12: Duration check
    print("[12/12] Checking duration...")
    ensure_shorts_duration(output_path, 58.0)
    
def format_description(content, video_type="short", credits=None):
    """Formats a professional science report description with cross-linking."""
    problem = content.get("problem_box", "Every body is different, but the science is clear.")
    bullets = "\n".join([f"• {b}" for b in content.get("science_bullets", [])])
    action = content.get("actionable_tip", "Stay curious and stay healthy.")
    seo_body = content.get("description_seo_body", "")
    hashtags = content.get("hashtags", "#health #science #bodyscience")
    tags = content.get("tags", "")
    playlist = content.get("playlist", "body_science")
    
    # Cross-linking logic
    related_link = f"https://youtube.com/{CHANNEL_HANDLE}"
    try:
        if os.path.exists("data/video_database.json"):
            with open("data/video_database.json", "r") as f:
                db = json.load(f)
                target_type = "long" if video_type == "short" else "short"
                relevant = [v for v in db if v.get("playlist") == playlist and v.get("type") == target_type]
                if relevant:
                    related_link = f"https://youtu.be/{relevant[0]['id']}"
                elif any(v.get("type") == target_type for v in db):
                    any_target = [v for v in db if v.get("type") == target_type]
                    related_link = f"https://youtu.be/{any_target[0]['id']}"
    except: pass

    full_desc = (
        f"🚨 THE PROBLEM: {problem}\n\n"
        f"🔬 THE SCIENCE:\n{bullets}\n\n"
        f"✅ THE SOLUTION: {action}\n\n"
        f"🎓 EDUCATIONAL NOTES: {seo_body}\n\n"
        f"{'📺 WATCH DEEP DIVE:' if video_type == 'short' else '🎬 WATCH QUICK TIPS:'} {related_link}\n\n"
        f"------------------------------------------\n"
        f"science of your body every single day\n"
        f"{CHANNEL_HANDLE}\n\n"
        f"Educational purposes only. Consult doctor.\n"
        f"Robot voice generated. Original research and script.\n"
        f"{{CREDITS_PLACEHOLDER}}\n\n"
        f"{hashtags}\n\n"
        f"[SEO TAGS]: {tags}"
    )
    
    full_desc = fix_description(full_desc)
    if credits:
        credits_text = f"\n background footage:\n" + "\n".join([f"   {c} (pexels)" for c in credits])
        full_desc = full_desc.replace("{{CREDITS_PLACEHOLDER}}", credits_text)
    else:
        full_desc = full_desc.replace("{{CREDITS_PLACEHOLDER}}", "\n background: satisfying visuals")
        
    return full_desc


def create_short(playlist: str = None):
    """Creates and uploads ONE Short video."""
    print(f"\n{'='*50}")
    print(f"  TheScienceOfYou  Creating Short ({playlist or 'auto'})")
    print(f"{'='*50}\n")
    
    # Step 1: Get topic
    print("[1/12] Getting topic...")
    topic_data = get_next_topic(playlist)
    print(f"  Topic: {topic_data['topic'][:60]}...")
    
    # Step 2: Generate Content
    print("[2/12] Generating AI script & Professional Metadata...")
    content = generate_short_content(topic_data)
    if not content:
        print("[FATAL] Content generation failed")
        return False
        
    # Step 3: TTS
    print("[3/12] Generating voiceover...")
    voiceover_raw, srt_path = generate_voiceover(content["script"], "temp/voiceover_raw.mp3")
    if not voiceover_raw:
        print("[FATAL] TTS failed")
        return False
    
    # Step 4: Speed up
    print(f"[4/12] Speeding up ({VOICEOVER_SPEED}x) & Scaling subtitles...")
    fast_voice = speed_up_audio(voiceover_raw, VOICEOVER_SPEED, "temp/voiceover_fast.mp3", srt_path=srt_path)
    
    # Step 5: SFX overlay
    print("[5/12] Overlaying SFX...")
    sfx_voice = overlay_sfx_on_audio(fast_voice, content.get("sfx_timeline", []), "temp/voiceover_sfx.mp3")
    
    # Step 6: Background music
    print("[6/12] Getting background music...")
    music_path = get_background_music()
    
    # Step 7: Mix audio
    print("[7/12] Mixing audio...")
    final_audio = mix_final_audio(sfx_voice, music_path, playlist, "temp/final_audio_short.mp3")
    
    # Step 8: Visuals
    print("[8/12] Getting satisfying background...")
    bg_path = get_satisfying_background()
    if not bg_path:
        print("[FATAL] No background video found")
        return False
        
    # Step 9: Assemble
    print("[9/12] Assembling 9:16 vertical video (120% zoom)...")
    intermediate = "temp/intermediate_short.mp4"
    if not assemble_short(bg_path, final_audio, intermediate):
        print("[FATAL] Assembly failed")
        return False
        
    # Step 10: Effects
    print("[10/12] Enhancing visuals + watermark...")
    apply_visual_enhancements(intermediate)
    add_watermark_ffmpeg(intermediate, CHANNEL_NAME, 0.1)
    
    # Step 11: Captions
    print("[11/12] Burning yellow pop-in captions...")
    output_path = f"output/short_{int(time.time())}.mp4"
    burn_animated_captions(intermediate, srt_path, output_path)
    
    # Step 12: Cleanup & Duration Check
    print("[12/12] Checking duration...")
    ensure_shorts_duration(output_path, SHORTS_MAX_DURATION)
    
    # Upload
    if DRY_RUN:
        print(f"[OFFLINE] DRY_RUN enabled. Skipping upload.")
        print(f"  Final video saved at: {output_path}")
        return True

    print("[UPLOAD] Uploading to YouTube...")
    full_description = format_description(content, "short")
    
    youtube = authenticate_youtube()
    video_id = upload_video(youtube, output_path, content["title"], full_description, playlist_type=playlist, privacy="public")
    pinned = content.get("pinned_comment")
    post_pinned_comment(youtube, video_id, pinned)
    
    # Cleanup
    cleanup_old_bg(3)
    cleanup_pexels_clips(3)
    for temp in ["temp/voiceover_raw.mp3", "temp/voiceover_fast.mp3",
                 "temp/voiceover_sfx.mp3", "temp/final_audio.mp3",
                 "temp/intermediate.mp4"]:
        if os.path.exists(temp): os.remove(temp)
    
    gc.collect()
    print(f"\n[DONE] Short created: {seo_filename}")
    return True


def create_longform(playlist: str = None):
    """Creates and uploads ONE long-form video."""
    print(f"\n{'='*50}")
    print(f"  TheScienceOfYou  Creating Long-form ({playlist or 'auto'})")
    print(f"{'='*50}\n")
    
    # Step 1: Get topic
    print("[1/14] Getting topic...")
    topic_data = get_next_topic(playlist)
    print(f"  Topic: {topic_data['topic'][:60]}...")
    
    # Step 2: Generate AI content
    print("[2/14] Generating AI script (long-form)...")
    content = generate_longform_content(topic_data)
    if not content:
        print("[FATAL] Content generation failed")
        return False
    print(f"  Title: {content.get('title', 'N/A')}")
    print(f"  Words: {len(content.get('script', '').split())}")
    
    # Step 3: TTS voiceover
    print("[3/14] Generating voiceover...")
    voice_path, srt_path = generate_voiceover(content["script"], "temp/longform_voiceover.mp3")
    if not voice_path:
        return False
        
    # Step 4: Background music
    print("[4/14] Getting background music...")
    music_path = get_background_music()
    
    # Step 5: Mix audio
    print("[5/14] Mixing final audio...")
    final_audio = mix_final_audio(voice_path, music_path, None, "temp/longform_final_audio.mp3")
    
    # Step 6: Background clips (Pexels)
    print("[6/14] Getting Pexels background clips...")
    try:
        clips, credits = get_longform_background_clips(content["script"])
    except Exception as e:
        print(f"  [Error] Pexels clips failed: {e}")
        clips, credits = [], []
        
    if not clips:
        print("  [Warning] No specialized clips found, using satisfying fallback...")
        try:
            bg_path = get_satisfying_background()
            if bg_path: clips = [bg_path]
        except Exception:
            pass
            
    if not clips:
        print("[FATAL] No video clips available")
        return False
        
    # Step 7: Assemble long-form video
    print("[7/14] Assembling 16:9 horizontal video...")
    seo_filename = create_seo_filename(content.get("title", "health-science-deepdive"))
    output_path = f"output/{seo_filename}"
    intermediate = "temp/longform_intermediate.mp4"
    
    if not assemble_longform(clips, final_audio, intermediate):
        print("[FATAL] Assembly failed")
        return False
        
    # Step 8: Visual enhancements
    print("[8/14] Enhancing visuals...")
    apply_visual_enhancements(intermediate)
    
    # Step 9: Watermark
    print("[9/14] Adding watermark...")
    add_watermark_ffmpeg(intermediate, "TheScienceOfYou", 0.15)
    
    # Step 10: Burn captions (optional for long-form, but good for engagement)
    print("[10/14] Burning captions...")
    burn_animated_captions(intermediate, srt_path, output_path)
    
    # Step 11: Generate Thumbnail
    print("[11/14] Generating thumbnail...")
    thumb_path = f"output/{seo_filename.replace('.mp4', '.jpg')}"
    generate_thumbnail(output_path, content.get("title", ""), content.get("hook", ""), thumb_path)
    
    # Step 12: Upload
    if DRY_RUN:
        print(f"[OFFLINE] DRY_RUN enabled. Saved at: {output_path}")
        return True
        
    print("[12/14] Uploading to YouTube...")
    full_description = format_description(content, "long", credits=credits)
        
    youtube = authenticate_youtube()
    video_id = upload_video(youtube, output_path, content["title"], full_description, playlist_type=playlist, privacy="public")
    
    # Step 13: Set Thumbnail
    if video_id and os.path.exists(thumb_path):
        print("[13/14] Setting thumbnail...")
        set_thumbnail(youtube, video_id, thumb_path)
        
    # Step 14: Pinned Comment
    if video_id:
        print("[14/14] Posting pinned comment...")
        pinned = content.get("pinned_comment")
        post_pinned_comment(youtube, video_id, pinned)
        
    # Cleanup
    cleanup_pexels_clips(5)
    for f in ["temp/longform_voiceover.mp3", "temp/longform_final_audio.mp3", 
              "temp/longform_intermediate.mp4", "temp/longform_voiceover.srt"]:
        if os.path.exists(f): os.remove(f)
        
    print(f"\n[DONE] Long-form created: {seo_filename}")
    return True


#  ENTRY POINT 
if __name__ == "__main__":
    v_type = sys.argv[1] if len(sys.argv) > 1 else "short"
    pl = sys.argv[2] if len(sys.argv) > 2 else None
    
    # First run: clean SFX library
    clean_sfx_library()
    
    if v_type == "short":
        create_short(pl)
    elif v_type == "long":
        create_longform(pl)
    elif v_type == "batch_shorts":
        schedules = [("body_science", 3), ("food_science", 2)]
        for pl_name, count in schedules:
            for i in range(count):
                print(f"\n--- Short {i+1}/{count} for {pl_name} ---")
                create_short(pl_name)
    elif v_type == "batch_long":
        create_longform("body_science")
        create_longform("food_science")
