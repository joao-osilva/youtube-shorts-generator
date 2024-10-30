from src.youtube_client import get_top_videos
from src.utils import format_video_info, format_timestamp
from src.downloader import VideoDownloader
from src.transcriber import Transcriber
from src.analyzer import ContentAnalyzer
from src.config import (
    RESULTS_DIR, 
    MAX_RESULTS, 
    REGION_CODE, 
    get_file_paths
)
from src.clipper import VideoClipper
from datetime import datetime, timezone, timedelta
import os
import json

def process_video(video: dict, downloader: VideoDownloader, transcriber: Transcriber, analyzer: ContentAnalyzer, clipper: VideoClipper) -> dict:
    """Process a single video: download, extract audio, transcribe, analyze, and create clips"""
    video_id = video['video_id']
    
    # Get current processing status
    status = downloader.get_status(video_id)
    video['processing_status'] = status
    
    # Download video
    print(f"\nProcessing video: {video['title']}")
    video_path = downloader.download_video(video_id)
    if not video_path:
        return video
    
    # Extract audio
    print("Extracting audio...")
    audio_path = downloader.extract_audio(video_id)
    if not audio_path:
        return video
    
    # Transcribe audio
    print("Transcribing audio...")
    transcription_data = transcriber.transcribe(video_id, video)
    if transcription_data:
        # Include basic transcription info in the video results
        video['transcription'] = {
            'file_path': get_file_paths(video_id)['transcript'],
            'language': transcription_data['metadata']['language_code'],
            'duration_seconds': transcription_data['stats']['duration_seconds'],
            'word_count': transcription_data['stats']['word_count'],
            'segment_count': transcription_data['stats']['segment_count']
        }
        
        # Analyze content for Shorts opportunities
        print("Analyzing content for Shorts opportunities...")
        analysis_data = analyzer.analyze_for_shorts(video_id)
        if analysis_data:
            # Create clips from analysis
            print("\nCreating video clips...")
            clips_info = clipper.process_analysis(video_id, analysis_data)
            
            # Save clips info
            clips_info_path = get_file_paths(video_id)['clips_info']
            with open(clips_info_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'video_id': video_id,
                    'clips_created': len(clips_info),
                    'created_at': datetime.utcnow().isoformat(),
                    'clips': clips_info
                }, f, indent=2)
            
            video['shorts_analysis'] = {
                'file_path': get_file_paths(video_id)['analysis'],
                'suggestions_count': len(analysis_data.analysis.shorts_suggestions),
                'clips_created': len(clips_info),
                'clips_info_path': clips_info_path
            }
    
    # Get final status
    video['processing_status'] = downloader.get_status(video_id)
    return video

def main():
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y-%m-%d')
    
    print(f"\nConfiguration:")
    print(f"- Fetching {MAX_RESULTS} videos")
    print(f"- Region: {REGION_CODE}")
    print(f"- Date: {yesterday_str}")
    print("\nStarting video processing...\n")
    
    videos = get_top_videos()
    
    if not videos:
        print("No videos found or an error occurred.")
        return
    
    print(f"Found {len(videos)} videos to process.\n")
    
    # Initialize processors
    downloader = VideoDownloader()
    transcriber = Transcriber()
    analyzer = ContentAnalyzer()
    clipper = VideoClipper()
    
    # Process each video
    processed_videos = []
    for i, video in enumerate(videos, 1):
        print(f"\nProcessing video {i}/{len(videos)}:")
        print(f"{format_video_info(video)}")
        print(f"Published: {format_timestamp(video['published_at'])}")
        
        processed_video = process_video(
            video.copy(), 
            downloader, 
            transcriber, 
            analyzer,
            clipper
        )
        processed_videos.append(processed_video)
        
        # Save results after each video
        results_file = os.path.join(RESULTS_DIR, f"results_{yesterday_str}.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'date': yesterday_str,
                    'region': REGION_CODE,
                    'videos_requested': MAX_RESULTS,
                    'videos_processed': len(processed_videos),
                    'last_updated': datetime.utcnow().isoformat()
                },
                'videos': processed_videos
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\nResults saved to {results_file}")

if __name__ == "__main__":
    main()
