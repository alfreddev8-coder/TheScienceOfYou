"""
YouTube Uploader - TheScienceOfYou
Handles authentication, video upload, and playlist management.
"""

import os
import time
import socket
import random
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# Token file path
TOKEN_FILE = "token.json"
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

# Retry settings - only use exceptions that actually exist in Python 3.10
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
RETRIABLE_EXCEPTIONS = (
    socket.error,
    socket.timeout,
    ConnectionError,
    TimeoutError,
    OSError
)

# Playlist SEO Data
PLAYLIST_INFO = {
    "body_science": {
        "title": "TheScienceOfYou: Body Science",
        "description": (
            "Ever wonder what happens inside your body? We break down human biology, "
            "organ functions, and the miracles of the human body in simple daily facts. "
            "From heart health to brain science, we translate what your body is trying to tell you. "
            "Every fact is backed by scientific research. #bodyscience #biology #healthhacks"
        )
    },
    "food_science": {
        "title": "TheScienceOfYou: Food Science",
        "description": (
            "The surprising science behind the food you eat! Discover how nutrition, vitamins, "
            "and minerals actually affect your biological systems. We destroy health myths with "
            "actual research and breakdown the science of food to help you eat smarter. "
            "Your body is talking... we translated the menu. #foodscience #nutrition #healthyeating"
        )
    }
}


def authenticate_youtube():
    """Authenticates using token.json and returns a YouTube service object."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("[YouTube] Refreshing token...")
            try:
                creds.refresh(Request())
                # Save refreshed token
                with open(TOKEN_FILE, "w") as f:
                    f.write(creds.to_json())
            except Exception as e:
                print(f"[YouTube] Token refresh failed: {e}")
                return None
        else:
            print("[YouTube] Error: No valid token found. Run generate_youtube_token.py first.")
            return None

    return build("youtube", "v3", credentials=creds)


def get_or_create_playlist(youtube, playlist_type):
    """Resolves a playlist type to an ID, creating it if it does not exist."""
    if playlist_type not in PLAYLIST_INFO:
        return None

    target_title = PLAYLIST_INFO[playlist_type]["title"]
    target_desc = PLAYLIST_INFO[playlist_type]["description"]

    try:
        response = youtube.playlists().list(
            part="snippet", mine=True, maxResults=50
        ).execute()

        for item in response.get("items", []):
            if item["snippet"]["title"] == target_title:
                print(f"[YouTube] Found existing playlist: {target_title}")
                return item["id"]

        # Create it if not found
        print(f"[YouTube] Creating SEO playlist: {target_title}")
        create_response = youtube.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": target_title,
                    "description": target_desc
                },
                "status": {
                    "privacyStatus": "public"
                }
            }
        ).execute()
        return create_response["id"]

    except Exception as e:
        print(f"[YouTube] Playlist error: {e}")
        return None


def add_to_playlist(youtube, video_id, playlist_id):
    """Adds a video to a playlist."""
    try:
        youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    }
                }
            }
        ).execute()
        print(f"[YouTube] Added to playlist: {playlist_id}")
    except Exception as e:
        print(f"[YouTube] Playlist add error: {e}")


def upload_video(youtube, filepath, title, description, playlist_type=None, playlist_id=None, privacy="private"):
    """
    Uploads a video to YouTube with resumable upload support.
    Accepts either playlist_type (auto-resolves) or playlist_id (direct).
    Default privacy is 'private' for safety.
    """
    if not youtube:
        return None

    # Resolve playlist ID
    resolved_playlist_id = playlist_id
    if not resolved_playlist_id and playlist_type:
        try:
            from config import PLAYLIST_BODY_SCIENCE, PLAYLIST_FOOD_SCIENCE
            if playlist_type == "body_science" and PLAYLIST_BODY_SCIENCE:
                resolved_playlist_id = PLAYLIST_BODY_SCIENCE
            elif playlist_type == "food_science" and PLAYLIST_FOOD_SCIENCE:
                resolved_playlist_id = PLAYLIST_FOOD_SCIENCE
            else:
                resolved_playlist_id = get_or_create_playlist(youtube, playlist_type)
        except Exception:
            resolved_playlist_id = get_or_create_playlist(youtube, playlist_type)

    print(f"[YouTube] Starting upload: {title} ({privacy})")

    # Generate tags from hashtags in description
    tags = [t.strip("#").lower() for t in description.split() if t.startswith("#")]

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags[:20],
            "categoryId": "27"  # Education
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(filepath, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    error = None
    retry = 0
    max_retries = 10

    while response is None:
        try:
            if retry > 0:
                print(f"  Uploading... (retry {retry})")
            else:
                print("  Uploading...")
            status, response = request.next_chunk()
            if response is not None and "id" in response:
                video_id = response["id"]
                print(f"[YouTube] Upload successful! Video ID: {video_id}")
                if resolved_playlist_id:
                    add_to_playlist(youtube, video_id, resolved_playlist_id)
                return video_id
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = f"Retriable HTTP error {e.resp.status}: {e.content}"
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error = f"Retriable network error: {e}"

        if error:
            print(f"  {error}")
            retry += 1
            if retry > max_retries:
                print("[YouTube] Max retries exceeded.")
                return None
            sleep_time = random.random() * (2 ** retry)
            print(f"  Retrying in {sleep_time:.2f}s...")
            time.sleep(sleep_time)
            error = None

    return None


def set_thumbnail(youtube, video_id, thumbnail_path):
    """Uploads a custom thumbnail for a video."""
    if not youtube or not video_id or not os.path.exists(thumbnail_path):
        return False
    try:
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
        ).execute()
        print(f"[YouTube] Thumbnail set for {video_id}")
        return True
    except Exception as e:
        print(f"[YouTube] Thumbnail error: {e}")
        return False
