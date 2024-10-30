from typing import List, Optional
from googleapiclient.discovery import build
from datetime import datetime, timezone, timedelta
from langdetect import detect, LangDetectException
import re
from .config import (
    YOUTUBE_API_KEY,
    MAX_RESULTS,
    REGION_CODE,
    SEARCH_DAYS,
    MAX_VIDEO_DURATION,
    MIN_VIDEO_DURATION,
    SEARCH_QUERY,
    RELEVANCE_LANGUAGE,
    MIN_VIEW_COUNT
)

def clean_title(text: str) -> str:
    """Clean title text for language detection by removing special characters and emojis"""
    # Remove emojis and special characters
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    
    # Remove special characters and keep only letters, numbers and spaces
    cleaned = emoji_pattern.sub('', text)
    cleaned = re.sub(r'[^\w\s]', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned

def is_valid_english_title(text: str) -> bool:
    """
    Additional validation for English titles to filter out AI/bot/gacha content
    and titles with excessive special characters
    """
    # Clean and lowercase the text for checking
    cleaned_text = clean_title(text.lower())
    
    # Suspicious patterns that indicate non-English or AI/bot content
    suspicious_patterns = [
        r'gacha',
        r'bot[sṣ]?.*react',
        r'ʚ.*ɞ',         # Special character patterns
        r'[/|]{2,}',     # Multiple slashes or pipes
        r'fy/?n',        # Common in bot/reaction videos
        r'[-=]?[zṣ][-=]' # Stylized characters
    ]
    
    # Check for suspicious patterns
    for pattern in suspicious_patterns:
        if re.search(pattern, text.lower()):
            return False
    
    # Check ratio of special characters to regular characters
    special_char_ratio = len(re.findall(r'[^\w\s]', text)) / len(text) if text else 0
    if special_char_ratio > 0.3:  # If more than 30% special characters
        return False
        
    return True

def detect_language(text: str) -> Optional[str]:
    """Detect language of text, returning language code or None if detection fails"""
    try:
        # Clean the text first
        cleaned_text = clean_title(text)
        if not cleaned_text:
            print(f"Warning: No valid text remained after cleaning '{text}'")
            return None
            
        # Map langdetect codes to our supported languages
        lang_map = {
            'en': 'en',
            'pt': 'pt',
        }
        detected = detect(cleaned_text)
        
        # Additional validation for English content
        if detected == 'en' and not is_valid_english_title(text):
            print(f"Detected as English but failed additional validation: '{text}'")
            return None
            
        return lang_map.get(detected)
    except LangDetectException as e:
        print(f"Language detection failed for '{text}': {str(e)}")
        return None
    except Exception as e:
        print(f"Unexpected error in language detection for '{text}': {str(e)}")
        return None

def get_top_videos() -> List[dict]:
    """Fetch top videos from YouTube based on configuration"""
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=SEARCH_DAYS)
        
        # Base search parameters
        search_params = {
            'part': 'snippet',
            'type': 'video',
            'order': 'date',
            'regionCode': REGION_CODE,
            'relevanceLanguage': RELEVANCE_LANGUAGE,
            'maxResults': MAX_RESULTS * 2,  # Fetch extra to account for filtering
            'publishedAfter': start_date.isoformat(),
            'publishedBefore': end_date.isoformat()
        }
        
        # Add search query if provided
        if SEARCH_QUERY:
            search_params['q'] = (f"{SEARCH_QUERY}")
        
        print(f"\nSearching videos with parameters:")
        print(f"- Region: {REGION_CODE}")
        print(f"- Language: {RELEVANCE_LANGUAGE}")
        if SEARCH_QUERY:
            print(f"- Query: {SEARCH_QUERY}")
        print(f"- Date range: {start_date.date()} to {end_date.date()}")
        
        # Execute search
        search_response = youtube.search().list(**search_params).execute()
        
        if not search_response.get('items'):
            print("No videos found matching the criteria")
            return []
        
        # Get video details (duration, etc)
        video_ids = [item['id']['videoId'] for item in search_response['items']]
        videos_response = youtube.videos().list(
            part='contentDetails,snippet,statistics',
            id=','.join(video_ids)
        ).execute()
        
        # Process and filter videos
        videos = []
        for video in videos_response.get('items', []):
            title = video['snippet']['title']
            
            # Detect title language with additional validation
            detected_lang = detect_language(title)
            if detected_lang is None:
                print(f"Skipping video: Invalid or unsupported language content in '{title}'")
                continue
            if detected_lang != RELEVANCE_LANGUAGE:
                print(f"Skipping video '{title}': Wrong language "
                      f"(expected: {RELEVANCE_LANGUAGE}, detected: {detected_lang})")
                continue
            
            # Parse duration
            duration = video['contentDetails']['duration']
            duration_seconds = parse_duration(duration)
            
            # Get view count
            view_count = int(video['statistics'].get('viewCount', 0))
            
            # Skip videos with insufficient views or outside duration limits
            if view_count < MIN_VIEW_COUNT:
                print(f"Skipping video '{title}': Only {view_count:,} views")
                continue
            elif not MIN_VIDEO_DURATION <= duration_seconds <= MAX_VIDEO_DURATION:
                print(f"Skipping video '{title}': Duration out of range")
                continue
                
            videos.append({
                'video_id': video['id'],
                'title': title,
                'published_at': video['snippet']['publishedAt'],
                'duration_seconds': duration_seconds,
                'view_count': view_count,
                'like_count': int(video['statistics'].get('likeCount', 0)),
                'comment_count': int(video['statistics'].get('commentCount', 0)),
                'detected_language': detected_lang
            })
        
        if not videos:
            print("No valid videos found after filtering")
            return []
            
        # Sort by view count and return limited results
        videos.sort(key=lambda x: x['view_count'], reverse=True)
        filtered_videos = videos[:MAX_RESULTS]
        
        print(f"\nFound {len(filtered_videos)} valid videos:")
        for video in filtered_videos:
            print(f"- [{video['detected_language']}] {video['title']} ({video['view_count']:,} views)")
            
        return filtered_videos
        
    except Exception as e:
        print(f"Error fetching YouTube videos: {str(e)}")
        return []

def parse_duration(duration: str) -> int:
    """Convert ISO 8601 duration to seconds"""
    import re
    import isodate
    return int(isodate.parse_duration(duration).total_seconds())
