from moviepy.editor import VideoFileClip, CompositeVideoClip, ColorClip
from moviepy.video.fx.all import resize, crop
from PIL import Image
import numpy as np
from typing import Optional, List, Dict
import os
from datetime import datetime
from .config import get_file_paths, CLIPS_DIR, MAX_CLIP_DURATION, MIN_CLIP_DURATION
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
        segment: dict,
        clip_number: int
    ) -> Optional[str]:
        """Create a single vertical format clip"""
        file_paths = get_file_paths(video_id)
        
        try:
            # Load video
            video = VideoFileClip(file_paths['video'])
            
            # Validate timestamps against actual video duration
            video_duration = video.duration
            t_start = float(segment['start_time'])
            t_end = float(segment['end_time'])
            
            # Validate timestamps
            if not (0 <= t_start < video_duration and 
                   t_start < t_end <= video_duration and 
                   MIN_CLIP_DURATION <= (t_end - t_start) <= MAX_CLIP_DURATION):
                print(f"Invalid clip timestamps: start={t_start}, end={t_end}, duration={video_duration}")
                video.close()
                return None

            # Extract clip
            clip = video.subclip(t_start, t_end)
            
            # Convert to vertical format
            vertical_clip = self.create_vertical_clip(clip)
            
            # Use the exact title_suggestion for the filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            clip_filename = f"{segment['title_suggestion']}.mp4"
            clip_path = os.path.join(self.clips_dir, clip_filename)
            
            # If file exists, add timestamp
            if os.path.exists(clip_path):
                clip_filename = f"{segment['title_suggestion']}_{timestamp}.mp4"
                clip_path = os.path.join(self.clips_dir, clip_filename)
            
            # Write clip to file
            vertical_clip.write_videofile(
                clip_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile=f'temp-audio-{video_id}-{clip_number}.m4a',
                remove_temp=True,
                threads=4,
                preset='ultrafast'  # For development; use 'medium' for production
            )
            
            return clip_path
            
        except Exception as e:
            print(f"Error creating clip {clip_number} for video {video_id}: {str(e)}")
            return None
        finally:
            # Ensure video is closed
            if 'video' in locals():
                video.close()

    def process_analysis(self, video_id: str, analysis_data: CompleteAnalysis) -> List[Dict]:
        """Process analysis data and create all clips"""
        clips_info = []
        
        try:
            # Access the shorts_suggestions through the Pydantic model
            suggestions = analysis_data.analysis.shorts_suggestions
            
            for i, segment in enumerate(suggestions, 1):
                print(f"\nCreating clip {i}/{len(suggestions)}")
                
                # Convert Pydantic model to dict for processing
                segment_dict = segment.model_dump()
                
                clip_path = self.create_clip(video_id, segment_dict, i)
                if clip_path:
                    clips_info.append({
                        'clip_number': i,
                        'clip_path': clip_path,
                        'segment': segment_dict,
                        'created_at': datetime.utcnow().isoformat()
                    })
                
            return clips_info
            
        except Exception as e:
            print(f"Error processing clips for video {video_id}: {str(e)}")
            return clips_info
