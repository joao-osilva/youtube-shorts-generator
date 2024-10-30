from pydantic import BaseModel, Field, conlist, conint
from typing import List
from datetime import datetime

class ShortsSegment(BaseModel):
    start_time: float = Field(
        ..., 
        description="Start time of the segment in seconds",
        ge=0
    )
    end_time: float = Field(
        ..., 
        description="End time of the segment in seconds (must be less than start_time + 60)",
        ge=0
    )
    content: str = Field(
        ..., 
        description="The exact text content of the segment"
    )
    title_suggestion: str = Field(
        ..., 
        description="Catchy title suggestion for the Shorts video"
    )
    hook_factor: conint(ge=1, le=10) = Field(
        ..., 
        description="Rating from 1-10 indicating how engaging the segment is"
    )
    reasoning: str = Field(
        ..., 
        description="Detailed explanation of why this segment would make a good Short"
    )
    tags: List[str] = Field(
        ..., 
        description="List of relevant hashtags for the Short",
        min_length=1,
        max_length=10
    )

    def model_post_init(self, _):
        if self.end_time - self.start_time > 60:
            raise ValueError("Segment duration must be less than 60 seconds")
        if self.end_time <= self.start_time:
            raise ValueError("End time must be after start time")

class ShortsAnalysisResponse(BaseModel):
    shorts_suggestions: List[ShortsSegment] = Field(
        ..., 
        description="List of 3-5 suggested segments for Shorts videos",
        min_length=3,
        max_length=5
    )

class AnalysisMetadata(BaseModel):
    video_id: str
    title: str
    analysis_timestamp: datetime
    model: str

class CompleteAnalysis(BaseModel):
    metadata: AnalysisMetadata
    analysis: ShortsAnalysisResponse
