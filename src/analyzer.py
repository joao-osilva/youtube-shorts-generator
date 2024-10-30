from typing import Optional
from openai import OpenAI
import json
import os
from datetime import datetime
from .config import OPENAI_API_KEY, get_file_paths
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

        # Prepare content for analysis
        video_title = transcript_data['metadata']['title']
        full_text = transcript_data['transcription']['text']

        system_prompt = """You are an expert YouTube Shorts content creator and editor for the Brazilian market. 
Analyze the video transcript and return a JSON response with the most engaging segments for Shorts (under 60 seconds).

Your response must be a JSON object with exactly this structure:
{
    "shorts_suggestions": [
        {
            "start_time": <number>,
            "end_time": <number>,
            "content": "exact segment text",
            "title_suggestion": "título em português (exemplo: '🔥 Vini Jr DESTRUIU em Campo! #shorts')",
            "hook_factor": <number 1-10>,
            "reasoning": "why this makes a good Short",
            "tags": ["tag1 em português", "tag2 em português", "..."]
        }
    ]
}

Requirements for Brazilian titles (title_suggestion):
- Must be in Brazilian Portuguese
- Include #shorts at the end
- Can include emojis
- Should be attention-grabbing
- Maximum 100 characters
- Examples:
  * "😱 O Momento ÉPICO do Vini Jr! #shorts"
  * "🏆 Brasileiro BRILHA na Champions! #shorts"
  * "⚽ A Verdade Sobre o Futebol Europeu #shorts"

Requirements for Brazilian tags:
- All tags in Portuguese
- Use Brazilian football terms
- Include relevant Brazilian hashtags
- Examples: ["futebol", "brasileiros", "champions", "viral"]"""

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
            
            # Create complete analysis with metadata
            complete_analysis = CompleteAnalysis(
                metadata=AnalysisMetadata(
                    video_id=video_id,
                    title=video_title,
                    analysis_timestamp=datetime.utcnow(),
                    model="gpt-3.5-turbo-1106"
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
