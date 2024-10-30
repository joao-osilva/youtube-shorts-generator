from moviepy.editor import VideoFileClip, CompositeVideoClip, ColorClip
from moviepy.video.fx.all import resize, crop
from PIL import Image
import numpy as np
from typing import Optional, List
import os
from datetime import datetime
from .config import get_file_paths, CLIPS_DIR
from .schemas import CompleteAnalysis, ShortsSegment

# Update Pillow/PIL constants for newer versions
Image.ANTIALIAS = Image.Resampling.LANCZOS

class VideoClipper:
    def __init__(self):
        self.clips_dir = CLIPS_DIR
        os.makedirs(self.clips_dir, exist_ok=True)
        # Shorts dimensions (1080x1920 for 9:16 aspect ratio)
        self.target_width = 1080
        self.target_height = 1920

    def create_blurred_background(self, clip) -> VideoFileClip:
        """Create a blurred background effect using available MoviePy effects"""
        # Resize to fill height
        bg = resize(clip, height=self.target_height)
        
        # Make it blurry by scaling down and up
        bg = resize(bg, width=bg.w//4)  # Scale down
        bg = resize(bg, width=bg.w*4)   # Scale up (creates blur effect)
        
        # Darken the background
        bg = bg.set_opacity(0.3)
        
        # Add a dark overlay
        dark_overlay = ColorClip(
            size=(self.target_width, self.target_height),
            color=(0, 0, 0)
        ).set_opacity(0.5)
        
        return CompositeVideoClip([bg, dark_overlay])

    def create_vertical_clip(self, clip) -> VideoFileClip:
        """Convert horizontal video to vertical Shorts format"""
        # Get original dimensions
        w, h = clip.size
        
        # Calculate scaling to maintain aspect ratio while fitting height
        scale = self.target_height / h
        new_w = int(w * scale)
        
        # Resize video maintaining aspect ratio
        resized_clip = resize(clip, height=self.target_height)
        
        if new_w > self.target_width:
            # If wider than target, crop to width
            x_center = resized_clip.w/2 - self.target_width/2
            resized_clip = crop(resized_clip, 
                              x1=x_center, 
                              width=self.target_width)
        else:
            # If narrower than target, add blurred background
            background = self.create_blurred_background(clip)
            
            # Position main clip in center
            x_pos = (self.target_width - new_w) // 2
            resized_clip = resized_clip.set_position((x_pos, 0))
            
            # Composite with background
            resized_clip = CompositeVideoClip(
                [background, resized_clip],
                size=(self.target_width, self.target_height)
            )

        return resized_clip

    def create_clip(
        self,
        video_id: str,
        segment: ShortsSegment,
        index: int
    ) -> Optional[str]:
        """Create a single clip from a segment"""
        try:
            file_paths = get_file_paths(video_id)
            source_path = file_paths['video']
            
            # Use the exact title_suggestion for the filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            clip_filename = f"{segment.title_suggestion}.mp4"
            clip_path = os.path.join(self.clips_dir, clip_filename)
            
            # If file exists, add timestamp
            if os.path.exists(clip_path):
                clip_filename = f"{segment.title_suggestion}_{timestamp}.mp4"
                clip_path = os.path.join(self.clips_dir, clip_filename)
            
            # Load video and create clip
            with VideoFileClip(source_path) as video:
                # Extract clip using segment timestamps
                clip = video.subclip(segment.start_time, segment.end_time)
                
                # Convert to vertical format
                vertical_clip = self.create_vertical_clip(clip)
                
                # Write clip to file
                vertical_clip.write_videofile(
                    clip_path,
                    codec='libx264',
                    audio_codec='aac',
                    temp_audiofile=f'temp-audio-{video_id}-{index}.m4a',
                    remove_temp=True,
                    threads=4,
                    preset='ultrafast'  # For development; use 'medium' for production
                )
                
            return clip_path
            
        except Exception as e:
            print(f"Error creating clip {index} for video {video_id}: {str(e)}")
            return None

    def process_analysis(self, video_id: str, analysis: CompleteAnalysis) -> List[dict]:
        """Process all segments from an analysis"""
        clips_info = []
        
        for i, segment in enumerate(analysis.analysis.shorts_suggestions, 1):
            print(f"\nCreating clip {i}/{len(analysis.analysis.shorts_suggestions)}")
            clip_path = self.create_clip(video_id, segment, i)
            
            if clip_path:
                clip_info = {
                    'clip_path': clip_path,
                    'segment': segment.model_dump(),
                    'index': i,
                    'duration': segment.end_time - segment.start_time,
                    'created_at': datetime.utcnow().isoformat(),
                    'format': {
                        'width': self.target_width,
                        'height': self.target_height,
                        'aspect_ratio': '9:16'
                    }
                }
                clips_info.append(clip_info)
                print(f"Clip {i} created successfully: {clip_path}")
            
        return clips_info
