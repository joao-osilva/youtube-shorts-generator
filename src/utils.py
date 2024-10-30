from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException

def is_portuguese_title(title: str) -> bool:
    """Check if the title is in Portuguese using language detection."""
    try:
        return detect(title) == 'pt'
    except LangDetectException:
        return False

def parse_duration(duration_str: str) -> float:
    """Convert ISO 8601 duration format to minutes."""
    hours = minutes = seconds = 0
    duration = duration_str[2:]  # Remove PT from start
    
    if 'H' in duration:
        hours, duration = duration.split('H')
        hours = int(hours)
    if 'M' in duration:
        minutes, duration = duration.split('M')
        minutes = int(minutes)
    if 'S' in duration:
        seconds = int(duration.replace('S', ''))
    
    return round(hours * 60 + minutes + seconds / 60, 2)

def format_video_info(video: dict) -> str:
    """Format video information for display."""
    return (
        f"Title: {video['title']}\n"
        f"Channel: {video['channel']}\n"
        f"Views: {video['views']:,}\n"
        f"Likes: {video['likes']:,}\n"
        f"Duration: {video['duration_mins']} minutes\n"
        f"URL: https://youtube.com/watch?v={video['video_id']}\n"
    )

def format_timestamp(timestamp: str) -> str:
    """Format ISO timestamp to readable format."""
    from datetime import datetime
    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
