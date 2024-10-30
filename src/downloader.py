from typing import Optional, Dict
import yt_dlp
import os
import json
from pydub import AudioSegment
from .config import get_file_paths

class VideoDownloader:
    def __init__(self):
        self.ydl_opts = {
            'format': 'mp4',
            'quiet': True,
            'no_warnings': True,
        }

    def get_status(self, video_id: str) -> Dict[str, bool]:
        """Get processing status for a video"""
        file_paths = get_file_paths(video_id)
        if os.path.exists(file_paths['status']):
            with open(file_paths['status'], 'r') as f:
                return json.load(f)
        return {
            'video_downloaded': False,
            'audio_extracted': False,
            'transcribed': False
        }

    def update_status(self, video_id: str, status_update: Dict[str, bool]):
        """Update processing status for a video"""
        file_paths = get_file_paths(video_id)
        current_status = self.get_status(video_id)
        current_status.update(status_update)
        
        with open(file_paths['status'], 'w') as f:
            json.dump(current_status, f, indent=2)

    def download_video(self, video_id: str) -> Optional[str]:
        """Download video if not already downloaded"""
        file_paths = get_file_paths(video_id)
        status = self.get_status(video_id)

        # Check if video already exists
        if status['video_downloaded'] and os.path.exists(file_paths['video']):
            print(f"Video {video_id} already downloaded")
            return file_paths['video']

        self.ydl_opts['outtmpl'] = file_paths['video']

        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
                if os.path.exists(file_paths['video']):
                    self.update_status(video_id, {'video_downloaded': True})
                    return file_paths['video']
        except Exception as e:
            print(f"Error downloading video {video_id}: {str(e)}")
        return None

    def extract_audio(self, video_id: str) -> Optional[str]:
        """Extract audio if not already extracted"""
        file_paths = get_file_paths(video_id)
        status = self.get_status(video_id)

        # Check if audio already exists
        if status['audio_extracted'] and os.path.exists(file_paths['audio']):
            print(f"Audio for {video_id} already extracted")
            return file_paths['audio']

        try:
            audio = AudioSegment.from_file(file_paths['video'])
            audio.export(file_paths['audio'], format="mp3")
            
            if os.path.exists(file_paths['audio']):
                self.update_status(video_id, {'audio_extracted': True})
                return file_paths['audio']
        except Exception as e:
            print(f"Error extracting audio for {video_id}: {str(e)}")
        return None

    def cleanup_video(self, video_id: str):
        """Remove downloaded video file"""
        file_paths = get_file_paths(video_id)
        try:
            if os.path.exists(file_paths['video']):
                os.remove(file_paths['video'])
        except Exception as e:
            print(f"Error removing video file for {video_id}: {str(e)}")
