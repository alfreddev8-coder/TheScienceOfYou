"""
Satisfying Background Video Source — TheScienceOfYou
Downloads satisfying clips from TikTok accounts that post
clean satisfying content (no text overlays, no captions).

Primary: TikTok satisfying accounts (via yt-dlp)
Fallback: Pexels stock satisfying clips

YouTube is NOT used (bot blocks on GitHub Actions).
"""

import os
import json
import random
import subprocess
import time
import sys
from core.utils import get_ytdlp_cmd

BG_DIR = "satisfying_bg_videos"
USED_BG_FILE = "data/used_bg_videos.json"

# ─────────────────────────────────────────────────────────────────
#  TIKTOK ACCOUNTS WITH CLEAN SATISFYING CONTENT (NO TEXT)
#  These accounts post pure visual satisfying content
#  Add more accounts as you find them
# ─────────────────────────────────────────────────────────────────
SATISFYING_TIKTOK_ACCOUNTS = [
    "kirkmaxson",
    "watchlike87",
    "hasnain._0009",
    "soapsoul.asmr",
    "oddlysatisfying",
    "kinetic.graphics",
    "factoryzone1",
]

# Direct TikTok video search terms (used with yt-dlp)
TIKTOK_SEARCH_TERMS = [
    "satisfying 3d animation no text",
    "satisfying kinetic sand asmr",
    "satisfying soap cutting clean",
    "satisfying slime mixing colorful",
    "satisfying paint pouring art",
    "oddly satisfying compilation",
    "satisfying liquid simulation",
    "satisfying sand art clean",
    "satisfying clay cutting asmr",
    "satisfying marble run loop",
    "satisfying domino chain",
    "colorful satisfying loop video",
    "satisfying 4k no text no caption",
    "satisfying abstract animation loop",
    "asmr satisfying no talking",
]


def load_used_bg() -> list:
    if os.path.exists(USED_BG_FILE):
        try:
            with open(USED_BG_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_used_bg(video_id: str):
    used = load_used_bg()
    used.append(video_id)
    os.makedirs(os.path.dirname(USED_BG_FILE), exist_ok=True)
    with open(USED_BG_FILE, "w") as f:
        json.dump(used, f, indent=2)

def reset_used_bg():
    os.makedirs(os.path.dirname(USED_BG_FILE), exist_ok=True)
    with open(USED_BG_FILE, "w") as f:
        json.dump([], f)


def get_account_videos(account: str, max_videos: int = 30) -> list:
    """Gets video URLs from a TikTok account."""
    try:
        cmd = get_ytdlp_cmd() + [
            "--flat-playlist",
            "--print", "url",
            "--playlist-items", f"1-{max_videos}",
            "--no-warnings",
            f"https://www.tiktok.com/@{account}",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        
        if result.returncode == 0 and result.stdout.strip():
            urls = [u.strip() for u in result.stdout.strip().split('\n') if u.strip() and 'tiktok.com' in u]
            print(f"[BG] Found {len(urls)} videos from @{account}")
            return urls
        else:
            if result.stderr:
                print(f"[BG] @{account} stderr: {result.stderr[:100]}")
        return []
    except subprocess.TimeoutExpired:
        print(f"[BG] Timeout @{account}")
        return []
    except Exception as e:
        print(f"[BG] Error @{account}: {e}")
        return []


def search_tiktok_videos(query: str, max_results: int = 10) -> list:
    """Searches TikTok for satisfying videos using yt-dlp."""
    try:
        cmd = get_ytdlp_cmd() + [
            "--flat-playlist",
            "--print", "url",
            "--playlist-items", f"1-{max_results}",
            "--no-warnings",
            "--quiet",
            f"ttsearch:{query}",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0 and result.stdout.strip():
            urls = [u.strip() for u in result.stdout.strip().split('\n') if u.strip()]
            print(f"[BG] TikTok search found {len(urls)} for '{query}'")
            return urls
        
        # Fallback: try without ttsearch prefix
        cmd = get_ytdlp_cmd() + [
            "--flat-playlist",
            "--print", "url",
            "--playlist-items", f"1-{max_results}",
            "--no-warnings",
            "--quiet",
            f"https://www.tiktok.com/search?q={query.replace(' ', '+')}"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0 and result.stdout.strip():
            urls = [u.strip() for u in result.stdout.strip().split('\n') if u.strip()]
            print(f"[BG] TikTok URL search found {len(urls)}")
            return urls
        
        return []
    except Exception as e:
        print(f"[BG] TikTok search error: {e}")
        return []


def download_tiktok_video(video_url: str, output_path: str) -> bool:
    """Downloads a single TikTok video."""
    try:
        # Remove existing file
        if os.path.exists(output_path):
            os.remove(output_path)
        
        cmd = get_ytdlp_cmd() + [
            "-o", output_path,
            "--format", "best[ext=mp4]/best",
            "--no-check-certificates",
            "--no-warnings",
            "--no-playlist",
            "--socket-timeout", "30",
            video_url
        ]
        
        print(f"[BG] Downloading: {video_url[:60]}...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        # Check if file exists at output path
        if os.path.exists(output_path) and os.path.getsize(output_path) > 50000:
            size_mb = os.path.getsize(output_path) / (1024*1024)
            print(f"[BG] Downloaded: {size_mb:.1f}MB")
            return True
        
        # Check for file with different extension
        base = os.path.splitext(output_path)[0]
        for ext in ['.mp4', '.webm', '.mkv', '.mp4.part']:
            alt = base + ext
            if os.path.exists(alt) and os.path.getsize(alt) > 50000:
                if alt != output_path:
                    try:
                        os.rename(alt, output_path)
                    except:
                        pass
                size_mb = os.path.getsize(output_path) / (1024*1024)
                print(f"[BG] Downloaded (alt ext): {size_mb:.1f}MB")
                return True
        
        if result.stderr:
            print(f"[BG] Download stderr: {result.stderr[:200]}")
        
        print(f"[BG] Download failed for: {video_url[:60]}")
        return False
        
    except subprocess.TimeoutExpired:
        print(f"[BG] Download timeout")
        return False
    except Exception as e:
        print(f"[BG] Download error: {e}")
        return False


def get_satisfying_background() -> str | None:
    """Gets ONE satisfying background video from TikTok accounts."""
    os.makedirs(BG_DIR, exist_ok=True)
    used = load_used_bg()
    
    # Shuffle accounts for variety
    accounts = SATISFYING_TIKTOK_ACCOUNTS.copy()
    random.shuffle(accounts)
    
    for account in accounts:
        print(f"[BG] Trying @{account}...")
        videos = get_account_videos(account)
        
        if not videos:
            continue
        
        # Filter out used videos
        available = [v for v in videos if v not in used]
        if not available:
            available = videos  # Reuse if all used
        
        # Try downloading up to 3 videos from this account
        random.shuffle(available)
        for video_url in available[:3]:
            video_hash = str(abs(hash(video_url)))[:10]
            output = os.path.join(BG_DIR, f"bg_{video_hash}.mp4")
            
            if download_tiktok_video(video_url, output):
                save_used_bg(video_url)
                return output
    
    # Fallback to TikTok search
    print("[BG] TikTok accounts failed. Trying TikTok search...")
    search_term = random.choice(TIKTOK_SEARCH_TERMS)
    videos = search_tiktok_videos(search_term)
    if videos:
        available = [v for v in videos if v not in used]
        if available:
            video_url = random.choice(available[:3])
            video_hash = str(abs(hash(video_url)))[:10]
            output = os.path.join(BG_DIR, f"bg_search_{video_hash}.mp4")
            if download_tiktok_video(video_url, output):
                save_used_bg(video_url)
                return output

    # Last resort: Pexels fallback
    print("[BG] TikTok failed. Trying Pexels fallback...")
    return get_pexels_satisfying_fallback()


def get_pexels_satisfying_fallback() -> str | None:
    """Downloads a satisfying clip from Pexels as last resort."""
    try:
        from video.pexels_source import search_pexels_videos, download_pexels_clip
    except ImportError:
        try:
            from pexels_source import search_pexels_videos, download_pexels_clip
        except ImportError:
            print("[BG] Cannot import Pexels source")
            return _direct_pexels_fallback()
    
    os.makedirs(BG_DIR, exist_ok=True)
    
    pexels_terms = [
        "abstract colorful liquid",
        "satisfying animation loop",
        "colorful particles motion",
        "water splash slow motion",
        "abstract art flowing",
        "colorful smoke slow motion",
        "liquid paint mixing",
        "abstract 3d render",
    ]
    
    query = random.choice(pexels_terms)
    results = search_pexels_videos(query, per_page=5, orientation="portrait")
    
    for result in results:
        clip_id = result.get("id", str(random.randint(10000, 99999)))
        output = os.path.join(BG_DIR, f"pexels_fallback_{clip_id}.mp4")
        
        if download_pexels_clip(result.get("url", ""), output):
            print(f"[BG] Pexels fallback: {output}")
            return output
    
    print("[BG] All sources failed")
    return None


def _direct_pexels_fallback() -> str | None:
    """Direct Pexels API call if pexels_source module unavailable."""
    import requests
    from config import PIXABAY_API_KEY
    
    if not PIXABAY_API_KEY:
        print("[BG] No Pixabay API key for fallback")
        return None
    
    os.makedirs(BG_DIR, exist_ok=True)
    
    terms = ["abstract colorful", "liquid slow motion", "particles animation"]
    query = random.choice(terms)
    
    try:
        params = {
            "key": PIXABAY_API_KEY,
            "q": query,
            "per_page": 5,
            "video_type": "film",
        }
        resp = requests.get("https://pixabay.com/api/videos/", params=params, timeout=15)
        
        if resp.status_code == 200:
            hits = resp.json().get("hits", [])
            for hit in hits:
                videos = hit.get("videos", {})
                for quality in ["medium", "small"]:
                    if quality in videos:
                        url = videos[quality]["url"]
                        output = os.path.join(BG_DIR, f"pixabay_{hit['id']}.mp4")
                        
                        dl = requests.get(url, timeout=60, stream=True)
                        if dl.status_code == 200:
                            with open(output, "wb") as f:
                                for chunk in dl.iter_content(8192):
                                    f.write(chunk)
                            if os.path.getsize(output) > 50000:
                                print(f"[BG] Pixabay fallback: {output}")
                                return output
                        break
    except Exception as e:
        print(f"[BG] Pixabay fallback error: {e}")
    
    return None


def cleanup_old_bg(keep: int = 3):
    """Removes old background videos to save space."""
    if not os.path.exists(BG_DIR):
        return
    files = []
    for f in os.listdir(BG_DIR):
        fp = os.path.join(BG_DIR, f)
        if os.path.isfile(fp):
            files.append((fp, os.path.getmtime(fp)))
    files.sort(key=lambda x: x[1], reverse=True)
    for fp, _ in files[keep:]:
        try:
            os.remove(fp)
            print(f"[Cleanup] Removed: {fp}")
        except:
            pass

def cleanup_old_bg(keep: int = 3):
    """Removes old downloaded background videos from TikTok to save space."""
    if not os.path.exists(BG_DIR):
        return
    files = []
    for f in os.listdir(BG_DIR):
        fp = os.path.join(BG_DIR, f)
        if os.path.isfile(fp):
            files.append((fp, os.path.getmtime(fp)))
    files.sort(key=lambda x: x[1], reverse=True)
    for fp, _ in files[keep:]:
        try:
            os.remove(fp)
            print(f"[Cleanup] Removed: {fp}")
        except:
            pass
