"""
TikTok Background Video Source  TheScienceOfYou
Downloads satisfying clips from TikTok for Shorts backgrounds using yt-dlp library.
"""

import os
import json
import random
import sys
import yt_dlp

TIKTOK_DIR = "tiktok_bg_videos"
USED_TIKTOK_FILE = "data/used_tiktok_videos.json"

SATISFYING_SEARCH_TERMS = [
    "satisfying 3d animation no text",
    "kinetic sand satisfying no talking",
    "liquid physics simulation satisfying",
    "oddly satisfying compilation no captions",
    "colorful satisfying loop 4k",
    "fluid simulation satisfying visuals",
    "satisfying geometry pattern loop",
    "satisfying sand art and sound",
    "colorful liquid pouring satisfying",
]

def load_used_tiktok() -> list:
    if os.path.exists(USED_TIKTOK_FILE):
        with open(USED_TIKTOK_FILE, "r") as f:
            try:
                data = json.load(f)
                return data if isinstance(data, list) else []
            except:
                return []
    return []

def save_used_tiktok(video_url: str):
    used = load_used_tiktok()
    used.append(video_url)
    os.makedirs(os.path.dirname(USED_TIKTOK_FILE), exist_ok=True)
    with open(USED_TIKTOK_FILE, "w") as f:
        json.dump(used, f, indent=2)

def search_tiktok_videos(query: str, max_results: int = 15) -> list:
    """Searches TikTok for satisfying videos using yt-dlp library."""
    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True,
        'playlist_items': f'1-{max_results}',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Use direct search URL which is more robust
            search_query = f"https://www.tiktok.com/search?q={query}"
            info = ydl.extract_info(search_query, download=False)
            
            if 'entries' in info:
                urls = [entry['url'] for entry in info['entries'] if 'url' in entry]
                print(f"[TikTok] Found {len(urls)} videos for '{query}'")
                return urls
        return []
    except Exception as e:
        print(f"[TikTok] Search error: {e}")
        return []

def download_tiktok_video(video_url: str, output_path: str) -> bool:
    """Downloads a single TikTok video using yt-dlp library."""
    ydl_opts = {
        'outtmpl': output_path,
        'format': 'best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
    }
    
    try:
        if os.path.exists(output_path):
            os.remove(output_path)
            
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
            
        if os.path.exists(output_path) and os.path.getsize(output_path) > 100000:
            print(f"[TikTok] Downloaded: {output_path}")
            return True
        return False
    except Exception as e:
        print(f"[TikTok] Download error: {e}")
        return False

def get_tiktok_background() -> str | None:
    """Main function: Gets ONE satisfying video from TikTok."""
    os.makedirs(TIKTOK_DIR, exist_ok=True)
    
    used = load_used_tiktok()
    search_term = random.choice(SATISFYING_SEARCH_TERMS)
    print(f"[TikTok] Searching for: {search_term}")
    
    all_videos = search_tiktok_videos(search_term)
    
    if not all_videos:
        return None
    
    available = [v for v in all_videos if v not in used]
    if not available:
        available = all_videos
    
    random.shuffle(available)
    
    for attempt, video_url in enumerate(available[:3], 1):
        video_hash = str(abs(hash(video_url)))[:8]
        output_path = os.path.join(TIKTOK_DIR, f"tiktok_{video_hash}.mp4")
        
        if download_tiktok_video(video_url, output_path):
            save_used_tiktok(video_url)
            return output_path
    
    return None

def cleanup_old_tiktok(keep: int = 3):
    if not os.path.exists(TIKTOK_DIR): return
    files = [(os.path.join(TIKTOK_DIR, f), os.path.getmtime(os.path.join(TIKTOK_DIR, f)))
             for f in os.listdir(TIKTOK_DIR) if os.path.isfile(os.path.join(TIKTOK_DIR, f))]
    files.sort(key=lambda x: x[1], reverse=True)
    for fp, _ in files[keep:]:
        try: os.remove(fp)
        except: pass
