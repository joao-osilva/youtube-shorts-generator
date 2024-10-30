from googleapiclient.discovery import build
from typing import List, Dict, Any
from .utils import parse_duration, is_portuguese_title
from .config import (
    YOUTUBE_API_KEY, 
    MAX_RESULTS, 
    REGION_CODE, 
    MAX_DURATION_MINUTES,
    MIN_DURATION_MINUTES,
    get_yesterday_timestamps
)

def is_shorts_video(video_data: Dict[str, Any]) -> bool:
    """
    Check if a video is a YouTube Short based on multiple criteria:
    1. Duration (Shorts are typically < 1 minute)
    2. Title containing #shorts
    3. Video URL format
    4. Video dimensions (vertical ratio)
    """
    title = video_data.get('snippet', {}).get('title', '').lower()
    video_id = video_data.get('id', '')
    
    # Check title for #shorts hashtag
    if any(tag in title for tag in ['#shorts', '#short', '#youtubeshorts']):
        return True
    
    # Check if video is from Shorts URL
    if video_id.startswith('shorts/'):
        return True
        
    return False

def get_top_videos() -> List[Dict[str, Any]]:
    """Retrieve yesterday's top viewed regular videos (not Shorts) from Brazil."""
    if not YOUTUBE_API_KEY:
        raise ValueError("YouTube API key not found in environment variables")

    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    yesterday_start, yesterday_end = get_yesterday_timestamps()
    
    try:
        # Initial search for videos
        search_response = youtube.search().list(
            part='id,snippet',
            maxResults=50,  # Request more to account for filtering
            type='video',
            order='viewCount',
            regionCode=REGION_CODE,
            publishedAfter=yesterday_start,
            publishedBefore=yesterday_end,
            videoDuration='medium',  # Only medium length videos (4-20 minutes)
            fields='items(id(videoId),snippet(title,channelId,channelTitle))'
        ).execute()
        
        if not search_response.get('items'):
            return []
            
        # Get detailed video information
        video_ids = [item['id']['videoId'] for item in search_response['items']]
        
        videos_response = youtube.videos().list(
            part='snippet,contentDetails,statistics,status',
            id=','.join(video_ids),
            fields='items(id,snippet(title,channelTitle,publishedAt,description),contentDetails(duration,dimension),statistics(viewCount,likeCount),status(uploadStatus,privacyStatus))'
        ).execute()
        
        filtered_videos = []
        for video in videos_response.get('items', []):
            # Skip if video is not available or is private
            if (video['status']['uploadStatus'] != 'processed' or 
                video['status']['privacyStatus'] != 'public'):
                continue
                
            # Skip if it's a Shorts video
            if is_shorts_video(video):
                continue
                
            # Get duration in minutes
            duration_mins = parse_duration(video['contentDetails']['duration'])
            
            # Skip videos outside our duration range
            if duration_mins >= MAX_DURATION_MINUTES or duration_mins < MIN_DURATION_MINUTES:
                continue
                
            # Skip non-Portuguese titles
            if not is_portuguese_title(video['snippet']['title']):
                continue
                
            filtered_videos.append({
                'video_id': video['id'],
                'title': video['snippet']['title'],
                'channel': video['snippet']['channelTitle'],
                'views': int(video['statistics']['viewCount']),
                'likes': int(video['statistics'].get('likeCount', 0)),
                'duration_mins': duration_mins,
                'published_at': video['snippet']['publishedAt'],
                'dimension': video['contentDetails']['dimension']
            })
        
        # Sort by views and get top results
        return sorted(filtered_videos, key=lambda x: x['views'], reverse=True)[:MAX_RESULTS]
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return []
