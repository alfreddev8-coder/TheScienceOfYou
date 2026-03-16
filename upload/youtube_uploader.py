import os
import time
import socket
import random
import http.client
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# Explicitly set the token path
TOKEN_FILE = "token.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.force-ssl"]

# Retry settings for resumable uploads
RETRIABLE_EXCEPTIONS = (http.client.NotConnected, http.client.IncompleteRead,
                        http.client.ImproperConnectionState, http.client.SocketTimeout,
                        socket.error, socket.timeout)
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

def authenticate_youtube():
    """Authenticates using token.json and returns a YouTube service object."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("[YouTube] Refreshing token...")
            creds.refresh(Request())
        else:
            print("[YouTube] Error: No valid token found. Run generate_youtube_token.py first.")
            return None
            
    return build("youtube", "v3", credentials=creds)

def upload_video(youtube, filepath, title, description, playlist_id=None, privacy="private"):
    """
    Uploads a video to YouTube with resumable support.
    Default privacy is 'private' for testing.
    """
    if not youtube: return None
    
    print(f"[YouTube] Starting upload: {title} ({privacy})")
    
    # Generate tags from description hashtags
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
            print(f"  Uploading... (retry {retry})" if retry > 0 else "  Uploading...")
            status, response = request.next_chunk()
            if response is not None:
                if "id" in response:
                    video_id = response["id"]
                    print(f"[YouTube] Upload successful! Video ID: {video_id}")
                    
                    # Add to playlist if provided
                    if playlist_id:
                        add_to_playlist(youtube, video_id, playlist_id)
                        
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
            
            sleep_time = random.random() * (2**retry)
            print(f"  Sleeping {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)
            
    return None

# Playlist SEO Data
PLAYLIST_INFO = {
    "body_science": {
        "title": "TheScienceOfYou: Body Science 🧬",
        "description": "Daily facts about the human body, organ functions, and biological miracles. Your body is talking. We translate."
    },
    "food_science": {
        "title": "TheScienceOfYou: Food Science 🍎",
        "description": "The surprising science behind the food you eat and how it affects your body. Fact-backed health secrets."
    }
}

def get_or_create_playlist(youtube, playlist_type):
    """Resolves a playlist type to an ID, creating it if necessary."""
    if playlist_type not in PLAYLIST_INFO:
        return None
    
    target_title = PLAYLIST_INFO[playlist_type]["title"]
    target_desc = PLAYLIST_INFO[playlist_type]["description"]
    
    try:
        # Check if it exists
        request = youtube.playlists().list(part="snippet", mine=True, maxResults=50)
        response = request.execute()
        
        for item in response.get("items", []):
            if item["snippet"]["title"] == target_title:
                return item["id"]
        
        # Create it if not found
        print(f"[YouTube] Creating SEO playlist: {target_title}")
        request = youtube.playlists().insert(
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
        )
        response = request.execute()
        return response["id"]
        
    except Exception as e:
        print(f"[YouTube] Playlist discovery/creation error: {e}")
        return None

def upload_video(youtube, filepath, title, description, playlist_type=None, privacy="private"):
    """
    Uploads a video to YouTube with resumable support.
    Default privacy is 'private' for testing.
    """
    if not youtube: return None
    
    # Resolve playlist ID if type is provided
    playlist_id = None
    if playlist_type:
        from config import PLAYLIST_BODY_SCIENCE, PLAYLIST_FOOD_SCIENCE
        # Check if we have an ID in env first
        if playlist_type == "body_science" and PLAYLIST_BODY_SCIENCE:
            playlist_id = PLAYLIST_BODY_SCIENCE
        elif playlist_type == "food_science" and PLAYLIST_FOOD_SCIENCE:
            playlist_id = PLAYLIST_FOOD_SCIENCE
        else:
            # Otherwise auto-create/resolve
            playlist_id = get_or_create_playlist(youtube, playlist_type)

    print(f"[YouTube] Starting upload: {title} ({privacy})")
    
    # Generate tags from description hashtags
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
            print(f"  Uploading... (retry {retry})" if retry > 0 else "  Uploading...")
            status, response = request.next_chunk()
            if response is not None:
                if "id" in response:
                    video_id = response["id"]
                    print(f"[YouTube] Upload successful! Video ID: {video_id}")
                    
                    # Add to playlist if provided
                    if playlist_id:
                        add_to_playlist(youtube, video_id, playlist_id)
                        
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
            
            sleep_time = random.random() * (2**retry)
            print(f"  Sleeping {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)
            
    return None
