import os
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

# API Keys
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY", "")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")

# DRY_RUN: reads from env var. Set GHA secret DRY_RUN=false to enable real uploads.
DRY_RUN = os.environ.get("DRY_RUN", "true").lower() == "true"

# YouTube OAuth (loaded from environment)
YOUTUBE_TOKEN_JSON = os.environ.get("YOUTUBE_TOKEN_JSON", "")

# Channel Identity
CHANNEL_NAME = "TheScienceOfYou"
CHANNEL_HANDLE = "@TheScienceOfYou"
CHANNEL_SLOGAN = "Your body is talking. We translate."
CHANNEL_URL = ""  # Fill after channel creation

# Playlists (fill IDs after creation)
PLAYLIST_BODY_SCIENCE = os.environ.get("PLAYLIST_BODY_SCIENCE", "")
PLAYLIST_FOOD_SCIENCE = os.environ.get("PLAYLIST_FOOD_SCIENCE", "")

# Models
PRIMARY_MODEL = "llama-3.3-70b-versatile"
FALLBACK_MODEL = "llama-3.1-70b-versatile"

# Video Settings
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
TARGET_FPS = 30
ZOOM_FACTOR = 1.20
SHORTS_MAX_DURATION = 58
VOICEOVER_SPEED = 1.15
TTS_VOICE = "en-US-AndrewNeural"  # Warm, authoritative male voice

# Audio Levels
MUSIC_VOLUME_DB = -14  # ~20% perceived (like Facts Man)
SFX_VOLUME_DB = -10    # ~40% perceived (subtle accents)

# Background Sources
KUAISHOU_SOURCE = "kuaishou.com"
PEXELS_SOURCE = "pexels.com"
