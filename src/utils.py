from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
from datetime import datetime
import pytz

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
        f"ID: {video['video_id']}\n"
        f"Duration: {format_duration(video['duration_seconds'])}\n"
        f"Views: {video.get('view_count', 'N/A'):,}\n"
        f"Likes: {video.get('like_count', 'N/A'):,}\n"
        f"Comments: {video.get('comment_count', 'N/A'):,}"
    )

def format_timestamp(timestamp_str: str) -> str:
    """Format timestamp string to readable format"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.astimezone(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S UTC')
    except Exception as e:
        return timestamp_str

def format_duration(seconds: int) -> str:
    """Format duration in seconds to readable format"""
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"
