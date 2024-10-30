from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from .config import MAX_CLIP_DURATION, MIN_CLIP_DURATION

class ShortsSegment(BaseModel):
    start_time: float = Field(..., ge=0)
    end_time: float
    content: str
    title_suggestion: str
    hook_factor: int = Field(..., ge=1, le=10)
    reasoning: str
    tags: List[str]

    @validator('end_time')
    def validate_end_time(cls, v, values):
        if 'start_time' in values:
            duration = v - values['start_time']
            if not MIN_CLIP_DURATION <= duration <= MAX_CLIP_DURATION:
                raise ValueError(f'Clip duration must be between {MIN_CLIP_DURATION} and {MAX_CLIP_DURATION} seconds')
            if v <= values['start_time']:
                raise ValueError('end_time must be greater than start_time')
        return v

class ShortsAnalysisResponse(BaseModel):
    shorts_suggestions: List[ShortsSegment]

class AnalysisMetadata(BaseModel):
    video_id: str
    title: str
    analysis_timestamp: datetime
    model: str
    video_duration: float  # Add video duration to metadata

class CompleteAnalysis(BaseModel):
    metadata: AnalysisMetadata
    analysis: ShortsAnalysisResponse
