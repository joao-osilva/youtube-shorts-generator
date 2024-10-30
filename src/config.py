from dotenv import load_dotenv
import os

load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

# YouTube Search Parameters
MAX_RESULTS = int(os.getenv('MAX_RESULTS', '2'))
REGION_CODE = os.getenv('REGION_CODE', 'US')
SEARCH_DAYS = int(os.getenv('SEARCH_DAYS', '1'))
RELEVANCE_LANGUAGE = os.getenv('RELEVANCE_LANGUAGE', 'en')
SEARCH_QUERY = os.getenv('SEARCH_QUERY', '')
MIN_VIEW_COUNT = int(os.getenv('MIN_VIEW_COUNT', '1000'))

# Validate language setting
VALID_LANGUAGES = ['en', 'pt']
if RELEVANCE_LANGUAGE not in VALID_LANGUAGES:
    print(f"Warning: Invalid language '{RELEVANCE_LANGUAGE}'. Using default 'en'")
    RELEVANCE_LANGUAGE = 'en'

# Video Processing Parameters
MAX_VIDEO_DURATION = int(os.getenv('MAX_VIDEO_DURATION', '1200'))
MIN_VIDEO_DURATION = int(os.getenv('MIN_VIDEO_DURATION', '120'))

# Shorts/Clips Parameters
MAX_CLIP_DURATION = int(os.getenv('MAX_CLIP_DURATION', '60'))
MIN_CLIP_DURATION = int(os.getenv('MIN_CLIP_DURATION', '15'))
MAX_CLIPS_PER_VIDEO = int(os.getenv('MAX_CLIPS_PER_VIDEO', '5'))

# Directory Structure
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
VIDEO_DIR = os.path.join(DATA_DIR, 'videos')
AUDIO_DIR = os.path.join(DATA_DIR, 'audio')
TRANSCRIPT_DIR = os.path.join(DATA_DIR, 'transcripts')
ANALYSIS_DIR = os.path.join(DATA_DIR, 'analysis')
CLIPS_DIR = os.path.join(DATA_DIR, 'clips')
RESULTS_DIR = os.path.join(DATA_DIR, 'results')

# Create directories if they don't exist
for directory in [DATA_DIR, VIDEO_DIR, AUDIO_DIR, TRANSCRIPT_DIR, 
                 ANALYSIS_DIR, CLIPS_DIR, RESULTS_DIR]:
    os.makedirs(directory, exist_ok=True)

def get_file_paths(video_id: str) -> dict[str, str]:
    """Get all file paths for a given video ID"""
    return {
        'video': os.path.join(VIDEO_DIR, f"{video_id}.mp4"),
        'audio': os.path.join(AUDIO_DIR, f"{video_id}.mp3"),
        'transcript': os.path.join(TRANSCRIPT_DIR, f"{video_id}.json"),
        'status': os.path.join(RESULTS_DIR, f"{video_id}_status.json"),
        'analysis': os.path.join(ANALYSIS_DIR, f"{video_id}_shorts.json"),
        'clips_info': os.path.join(CLIPS_DIR, f"{video_id}_clips.json")
    }
