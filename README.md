# YouTube Shorts Generator 🎬

An automated tool that analyzes YouTube videos, identifies engaging segments, and creates optimized Shorts content.

## Features ✨

- 📥 Downloads YouTube videos
- 🎯 Identifies engaging segments for Shorts
- 🗣️ Transcribes video content
- 🤖 AI-powered content analysis
- ✂️ Automatically creates vertical format clips
- 🇧🇷 Optimized for Brazilian Portuguese content

## Requirements 📋
- Python 3.11+
- OpenAI API Key
- YouTube API Key

## Project Structure 📁
```bash
youtube-shorts-generator/
├── src/
│ ├── analyzer.py # AI content analysis
│ ├── clipper.py # Video clip creation
│ ├── config.py # Configuration and paths
│ ├── downloader.py # YouTube video download
│ ├── schemas.py # Pydantic models
│ ├── transcriber.py # Audio transcription
│ ├── utils.py # Utility functions
│ └── youtube_client.py # YouTube client
├── data/
│ ├── videos/ # Downloaded videos
│ ├── audio/ # Extracted audio
│ ├── transcripts/ # Video transcriptions
│ ├── analysis/ # Shorts analysis
│ └── clips/ # Generated Shorts
├── main.py # Main execution script
└── README.md
```

## Configuration ⚙️

1. Create a `.env` file in the root directory:
```env
OPENAI_API_KEY=your_openai_api_key_here
YOUTUBE_API_KEY=your_youtube_api_key_here
MAX_RESULTS=2
REGION_CODE=BR
```

2. The application will automatically:
   - Fetch the top videos from YouTube based on your configuration
   - Process videos from the previous day
   - Use the specified region code (default: BR)
   - Process the number of videos defined in MAX_RESULTS

## How It Works 🔄

1. **Download**: Downloads YouTube videos using yt-dlp
2. **Transcribe**: Uses Whisper to transcribe audio content
3. **Analyze**: Uses OpenAI GPT to identify engaging segments
4. **Generate**: Creates vertical format clips optimized for Shorts

### Processing Steps:

1. **Video Download**
   - Downloads video in best quality
   - Extracts audio for transcription

2. **Transcription**
   - Transcribes audio using Whisper
   - Saves timestamped transcription

3. **Content Analysis**
   - Analyzes transcription for engaging segments
   - Identifies 3-5 potential Shorts clips
   - Generates Portuguese titles and tags

4. **Clip Generation**
   - Creates vertical format (9:16)
   - Adds blurred background when needed
   - Optimizes for Shorts format
   - Names clips using suggested titles

## Usage 🚀

1. Clone the repository:
```bash
git clone https://github.com/yourusername/youtube-shorts-generator.git
cd youtube-shorts-generator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your environment variables in `.env`

4. Run the generator:
```bash
python main.py
```

The tool will:
- Fetch yesterday's top videos from YouTube
- Download each video
- Generate transcriptions
- Analyze content for potential Shorts
- Create vertical format clips
- Save processing results in JSON format

### Results

The tool generates a daily results file (`results_YYYY-MM-DD.json`) containing:
- Processing metadata (date, region, video counts)
- For each video:
  - Basic information (title, ID, publish date)
  - Transcription details
  - Analysis results
  - Generated clips information
  - Processing status

### Data Structure

All generated files are organized in the `data/` directory:
- `video/`: Original downloaded videos
- `audio/`: Extracted audio files
- `transcripts/`: Video transcriptions
- `analysis/`: AI analysis results
- `clips/`: Generated Shorts clips

## Output 📤

The tool generates:
- Transcription files (JSON)
- Analysis reports (JSON)
- Vertical format clips ready for Shorts
- Processing status logs

### Clip Format:
- Resolution: 1080x1920 (9:16)
- Format: MP4 with H.264 encoding
- Duration: < 60 seconds
- Filename: Based on generated Portuguese title

## Error Handling 🔧

The tool includes error handling for:
- Download failures
- Transcription errors
- Analysis failures
- Video processing issues
- File system operations

## Contributing 🤝

Feel free to:
- Open issues
- Submit PRs
- Suggest improvements
- Report bugs

## License 📄

MIT License
