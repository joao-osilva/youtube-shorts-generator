from typing import Optional
from openai import OpenAI
import json
import os
from datetime import datetime
from .config import (
    OPENAI_API_KEY, 
    get_file_paths,
    MAX_CLIP_DURATION,
    MIN_CLIP_DURATION,
    MAX_CLIPS_PER_VIDEO,
    RELEVANCE_LANGUAGE
)
from .schemas import CompleteAnalysis, AnalysisMetadata, ShortsAnalysisResponse

class ContentAnalyzer:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def analyze_for_shorts(self, video_id: str) -> Optional[CompleteAnalysis]:
        """Analyze transcription to identify potential shorts segments"""
        file_paths = get_file_paths(video_id)
        
        # Check if analysis already exists
        if os.path.exists(file_paths['analysis']):
            print(f"Analysis for {video_id} already exists")
            with open(file_paths['analysis'], 'r', encoding='utf-8') as f:
                return CompleteAnalysis.model_validate_json(f.read())

        # Load transcription
        with open(file_paths['transcript'], 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)

        # Get video duration from transcription data
        video_duration = transcript_data['stats']['duration_seconds']
        
        # Prepare content for analysis
        video_title = transcript_data['metadata']['title']
        full_text = transcript_data['transcription']['text']

        # Determine language-specific examples and requirements
        if RELEVANCE_LANGUAGE == 'pt':
            title_examples = [
                "😱 O Momento ÉPICO do Vini Jr! #shorts",
                "🏆 Brasileiro BRILHA na Champions! #shorts",
                "⚽ A Verdade Sobre o Futebol Europeu #shorts"
            ]
            tag_examples = ["futebol", "brasileiros", "champions", "viral"]
            title_lang = "Brazilian Portuguese"
        else:  # default to English
            title_examples = [
                "😱 EPIC Football Moment! #shorts",
                "🏆 Amazing Game Highlights! #shorts",
                "⚽ The Truth About Soccer #shorts"
            ]
            tag_examples = ["football", "soccer", "sports", "viral"]
            title_lang = "English"

        system_prompt = f"""You are an expert YouTube Shorts content creator and editor. 
Analyze the video transcript and return a JSON response with the most engaging segments for Shorts.

The video is {video_duration} seconds long. All segments must be within this duration.

Your response must be a JSON object with exactly this structure:
{{
    "shorts_suggestions": [
        {{
            "start_time": <number between 0 and {video_duration}>,
            "end_time": <number between start_time and {video_duration}>,
            "content": "exact segment text",
            "title_suggestion": "title in {title_lang} (example: '{title_examples[0]}')",
            "hook_factor": <number 1-10>,
            "reasoning": "why this makes a good Short",
            "tags": ["tag1", "tag2", "..."]
        }}
    ]
}}

Requirements for segments:
- start_time must be between 0 and {video_duration} seconds
- end_time must be between start_time and {video_duration} seconds
- Each segment must be between {MIN_CLIP_DURATION} and {MAX_CLIP_DURATION} seconds
- Segments must not overlap with each other

Requirements for titles (title_suggestion):
- Must be in {title_lang}
- Include #shorts at the end
- Can include emojis
- Should be attention-grabbing
- Maximum 100 characters
- Examples:
  * "{title_examples[0]}"
  * "{title_examples[1]}"
  * "{title_examples[2]}"

Requirements for tags:
- All tags in {title_lang}
- Use relevant terms for the content
- Include trending hashtags
- Examples: {tag_examples}

Additional Requirements:
- Return maximum {MAX_CLIPS_PER_VIDEO} segments
- Each segment must be between {MIN_CLIP_DURATION} and {MAX_CLIP_DURATION} seconds
- Hook factor must be between 1 and 10
- Content must be self-contained and engaging"""

        user_prompt = f"""Analyze this video content and provide a JSON response with the best segments for Shorts:

Title: {video_title}

Full Transcript:
{full_text}

Return a JSON with exactly the required structure containing 3-5 of the most compelling segments.
Focus on moments that are attention-grabbing, self-contained, and would make viewers interested in the full video."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo-1106",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
            )

            # Parse response and validate with Pydantic
            raw_analysis = json.loads(response.choices[0].message.content)
            print(f"Raw analysis: {json.dumps(raw_analysis, indent=2)}")  # Debug print
            shorts_analysis = ShortsAnalysisResponse.model_validate(raw_analysis)
            
            # Validate timestamps before returning
            valid_suggestions = []
            for suggestion in shorts_analysis.shorts_suggestions:
                if (0 <= suggestion.start_time < video_duration and 
                    suggestion.start_time < suggestion.end_time <= video_duration and
                    MIN_CLIP_DURATION <= (suggestion.end_time - suggestion.start_time) <= MAX_CLIP_DURATION):
                    valid_suggestions.append(suggestion)
                else:
                    print(f"Skipping invalid segment: {suggestion.start_time} to {suggestion.end_time}")

            shorts_analysis.shorts_suggestions = valid_suggestions

            # Create complete analysis with metadata
            complete_analysis = CompleteAnalysis(
                metadata=AnalysisMetadata(
                    video_id=video_id,
                    title=video_title,
                    analysis_timestamp=datetime.utcnow(),
                    model="gpt-3.5-turbo-1106",
                    video_duration=video_duration  # Add video duration to metadata
                ),
                analysis=shorts_analysis
            )

            # Save analysis
            with open(file_paths['analysis'], 'w', encoding='utf-8') as f:
                f.write(complete_analysis.model_dump_json(indent=2))

            return complete_analysis

        except json.JSONDecodeError as e:
            print(f"JSON parsing error for {video_id}: {str(e)}")
            return None
        except Exception as e:
            print(f"Error analyzing content for {video_id}: {str(e)}")
            print(f"Raw response: {response.choices[0].message.content}")  # Debug print
            return None
