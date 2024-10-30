from typing import Optional, Dict, Any
from openai import OpenAI
import os
import json
from datetime import datetime
from .config import OPENAI_API_KEY, get_file_paths

class Transcriber:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def transcribe(self, video_id: str, video_metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Transcribe audio if not already transcribed using latest OpenAI API.
        Returns full transcription response including text, segments, and metadata.
        """
        file_paths = get_file_paths(video_id)
        
        # Check if transcription already exists
        if os.path.exists(file_paths['transcript']):
            print(f"Transcription for {video_id} already exists")
            with open(file_paths['transcript'], 'r', encoding='utf-8') as f:
                return json.load(f)

        try:
            with open(file_paths['audio'], "rb") as audio_file:
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="pt",
                    response_format="verbose_json",
                    timestamp_granularities=["segment", "word"],
                )
                
                # Create comprehensive transcription data
                transcription_data = {
                    'metadata': {
                        'video_id': video_id,
                        'title': video_metadata.get('title'),
                        'channel': video_metadata.get('channel'),
                        'published_at': video_metadata.get('published_at'),
                        'views': video_metadata.get('views'),
                        'duration_mins': video_metadata.get('duration_mins'),
                        'transcribed_at': datetime.utcnow().isoformat(),
                        'model': "whisper-1",
                        'language_code': response.language
                    },
                    'transcription': {
                        'text': response.text,
                        'segments': [
                            {
                                'id': segment.id,
                                'start': segment.start,
                                'end': segment.end,
                                'text': segment.text,
                                'words': [
                                    {
                                        'word': word.word,
                                        'start': word.start,
                                        'end': word.end,
                                        'confidence': word.confidence
                                    }
                                    for word in segment.words
                                ] if hasattr(segment, 'words') else []
                            }
                            for segment in response.segments
                        ]
                    },
                    'stats': {
                        'segment_count': len(response.segments),
                        'word_count': sum(len(segment.words) for segment in response.segments if hasattr(segment, 'words')),
                        'duration_seconds': sum(segment.end - segment.start for segment in response.segments)
                    }
                }
                
                # Save detailed transcription as JSON
                with open(file_paths['transcript'], 'w', encoding='utf-8') as f:
                    json.dump(transcription_data, f, ensure_ascii=False, indent=2)
                
                # Update status
                status_path = file_paths['status']
                if os.path.exists(status_path):
                    with open(status_path, 'r') as f:
                        status = json.load(f)
                    status['transcribed'] = True
                    with open(status_path, 'w') as f:
                        json.dump(status, f, indent=2)
                
                return transcription_data
                
        except Exception as e:
            print(f"Error transcribing audio for {video_id}: {str(e)}")
            return None
