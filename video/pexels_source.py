"""
Pexels Video Source  TheScienceOfYou
Downloads topic-matched stock footage from Pexels for long-form videos.
Multiple clips per video, matched to script content.
"""

import os
import json
import random
import requests
import time
from config import PIXABAY_API_KEY

PEXELS_DIR = "pexels_bg_clips"
PEXELS_API_KEY_ENV = os.environ.get("PEXELS_API_KEY", "")
# Pexels uses a separate API key from Pixabay
# If not set, we'll use Pixabay's video API as fallback

PEXELS_API_BASE = "https://api.pexels.com/videos"
PIXABAY_VIDEO_API = "https://pixabay.com/api/videos/"


def search_pexels_videos(query: str, per_page: int = 5, orientation: str = "portrait") -> list:
    """Searches Pexels for stock video clips."""
    api_key = PEXELS_API_KEY_ENV
    
    if api_key:
        try:
            headers = {"Authorization": api_key}
            params = {
                "query": query,
                "per_page": per_page,
                "orientation": orientation,
            }
            response = requests.get(PEXELS_API_BASE + "/search", 
                                    headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                for video in data.get("videos", []):
                    for file in video.get("video_files", []):
                        if file.get("quality") in ["hd", "sd"]:
                            results.append({
                                "url": file["link"],
                                "width": file.get("width", 0),
                                "height": file.get("height", 0),
                                "id": video.get("id", ""),
                                "photographer": video.get("user", {}).get("name", "Pexels"),
                            })
                            break
                return results
        except Exception as e:
            print(f"[Pexels] API error: {e}")
    
    # Fallback to Pixabay video API
    return search_pixabay_videos(query, per_page)


def search_pixabay_videos(query: str, per_page: int = 5) -> list:
    """Fallback: searches Pixabay for stock video clips."""
    if not PIXABAY_API_KEY:
        print("[Pixabay] No API key")
        return []
    
    try:
        params = {
            "key": PIXABAY_API_KEY,
            "q": query,
            "per_page": per_page,
            "video_type": "film",
        }
        response = requests.get(PIXABAY_VIDEO_API, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            results = []
            for hit in data.get("hits", []):
                videos = hit.get("videos", {})
                for quality in ["medium", "small", "tiny"]:
                    if quality in videos:
                        results.append({
                            "url": videos[quality]["url"],
                            "width": videos[quality].get("width", 0),
                            "height": videos[quality].get("height", 0),
                            "id": str(hit.get("id", "")),
                            "photographer": hit.get("user", "Pixabay"),
                        })
                        break
            return results
        
        return []
    except Exception as e:
        print(f"[Pixabay] Video search error: {e}")
        return []


def download_pexels_clip(url: str, output_path: str) -> bool:
    """Downloads a single video clip from Pexels/Pixabay."""
    try:
        response = requests.get(url, timeout=60, stream=True)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            if os.path.getsize(output_path) > 50000:
                return True
            else:
                os.remove(output_path)
                return False
        return False
    except Exception as e:
        print(f"[Pexels] Download error: {e}")
        return False


def get_longform_background_clips(keywords: list, clips_per_keyword: int = 4) -> tuple:
    """
    Downloads multiple clips from Pexels for long-form video.
    Returns (list of filepaths, list of credits).
    """
    os.makedirs(PEXELS_DIR, exist_ok=True)
    
    downloaded_clips = []
    credits = []
    
    for keyword in keywords:
        print(f"[Pexels] Searching: {keyword}")
        results = search_pexels_videos(keyword, per_page=clips_per_keyword)
        
        for i, result in enumerate(results[:clips_per_keyword]):
            clip_id = result.get("id", str(random.randint(10000, 99999)))
            output_path = os.path.join(PEXELS_DIR, f"clip_{clip_id}_{i}.mp4")
            
            if download_pexels_clip(result["url"], output_path):
                downloaded_clips.append(output_path)
                photographer = result.get("photographer", "Pexels")
                if photographer not in credits:
                    credits.append(photographer)
                print(f"[Pexels] Downloaded clip {len(downloaded_clips)}")
        
        time.sleep(1)  # Rate limiting
    
    print(f"[Pexels] Total clips: {len(downloaded_clips)}")
    return downloaded_clips, credits


def get_shorts_fallback_clip(topic: str) -> tuple:
    """
    Fallback for Shorts when Kuaishou fails.
    Gets a satisfying clip from Pexels/Pixabay.
    Returns (filepath, credits list).
    """
    os.makedirs(PEXELS_DIR, exist_ok=True)
    
    satisfying_terms = [
        "satisfying colorful liquid",
        "abstract 3d animation",
        "colorful particles motion",
        "water splash slow motion",
        "abstract art motion",
    ]
    
    query = random.choice(satisfying_terms)
    results = search_pexels_videos(query, per_page=5, orientation="portrait")
    
    if not results:
        results = search_pixabay_videos(query, per_page=5)
    
    for result in results:
        clip_id = result.get("id", str(random.randint(10000, 99999)))
        output_path = os.path.join(PEXELS_DIR, f"fallback_{clip_id}.mp4")
        
        if download_pexels_clip(result["url"], output_path):
            credits = [result.get("photographer", "Pexels")]
            return output_path, credits
    
    return None, []


def cleanup_pexels_clips(keep: int = 5):
    """Removes old Pexels clips."""
    if not os.path.exists(PEXELS_DIR):
        return
    files = [(os.path.join(PEXELS_DIR, f), os.path.getmtime(os.path.join(PEXELS_DIR, f)))
             for f in os.listdir(PEXELS_DIR) if os.path.isfile(os.path.join(PEXELS_DIR, f))]
    files.sort(key=lambda x: x[1], reverse=True)
    for fp, _ in files[keep:]:
        try:
            os.remove(fp)
        except:
            pass
