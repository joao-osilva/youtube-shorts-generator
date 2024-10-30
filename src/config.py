from datetime import datetime, timezone, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Video fetch configuration
MAX_RESULTS = int(os.getenv("MAX_RESULTS", "10"))  # Default to 10 videos
REGION_CODE = os.getenv("REGION_CODE", "BR")
MIN_DURATION_MINUTES = 4
MAX_DURATION_MINUTES = 21

# Directory setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Data directories
AUDIO_DIR = os.path.join(DATA_DIR, "audio")
VIDEO_DIR = os.path.join(DATA_DIR, "video")
TRANSCRIPT_DIR = os.path.join(DATA_DIR, "transcripts")
RESULTS_DIR = os.path.join(DATA_DIR, "results")
STATUS_DIR = os.path.join(DATA_DIR, "status")
ANALYSIS_DIR = os.path.join(DATA_DIR, "analysis")
CLIPS_DIR = os.path.join(DATA_DIR, "clips")

# Create all necessary directories
DIRS = [AUDIO_DIR, VIDEO_DIR, TRANSCRIPT_DIR, RESULTS_DIR, STATUS_DIR, ANALYSIS_DIR, CLIPS_DIR]
for directory in DIRS:
    os.makedirs(directory, exist_ok=True)

def get_file_paths(video_id: str) -> dict[str, str]:
    """Get all file paths for a given video ID"""
    return {
        'video': os.path.join(VIDEO_DIR, f"{video_id}.mp4"),
        'audio': os.path.join(AUDIO_DIR, f"{video_id}.mp3"),
        'transcript': os.path.join(TRANSCRIPT_DIR, f"{video_id}.json"),
        'status': os.path.join(STATUS_DIR, f"{video_id}.json"),
        'analysis': os.path.join(ANALYSIS_DIR, f"{video_id}_shorts.json"),
        'clips_info': os.path.join(CLIPS_DIR, f"{video_id}_clips.json")
    }

def get_yesterday_timestamps() -> tuple[str, str]:
    """Return RFC 3339 formatted timestamps for yesterday"""
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    
    yesterday_start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    return yesterday_start.isoformat(), yesterday_end.isoformat()
