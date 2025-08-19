# Descope AI GTM Engine - Prototype Overview

This prototype helps generate personalized outreach for leads in the authentication/SSO space using AI-driven insights. It collects signals from free sources, scores leads, and optionally creates draft outreach using LLMs and TTS.

## Dependencies (All Free)

- **Python 3.10+**
- **Python packages** (install via pip):
  ```bash
  pip install requests feedparser beautifulsoup4 python-dotenv hf_xet scipy torch bark-tts
  ```
- **FFmpeg** (for audio/video processing)
- **Optional:** Local Ollama installation enables LLM messaging via Llama 3

### Environment Variables
Create a `.env` file and include:
```env
GTM_DB_PATH=./gtm.db
SLACK_WEBHOOK=your_slack_webhook_url
OLLAMA_MODEL=llama3.2:3b
D_ID_KEY=your_d_id_api_key
```

### Ollama Setup
For AI-generated messaging:
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a fast model
ollama pull llama3.2:3b

# Start Ollama service
ollama serve
```

## Quickstart

```bash
# Initialize DB and bootstrap data
python main.py --bootstrap

# Run the demo workflow
python main.py --run-demo
```

## What Happens

1. **Creates a SQLite DB** (`gtm.db`) in the current directory
2. **Pulls free signals** from sources like GitHub issues, Hacker News, and RSS
3. **Enriches leads** using heuristics
4. **Scores leads** based on relevance to authentication/SSO space
5. **Generates personalized outreach**
6. **Creates multimedia assets** (audio via Bark TTS, video via D-ID API)
7. **Posts summary to Slack** (optional)


### FFmpeg Issues
```bash
# Install FFmpeg
# Ubuntu/Debian: sudo apt install ffmpeg
# macOS: brew install ffmpeg
# Windows: Download from https://ffmpeg.org/
```

## Notes

- **Prototype Status**: Uses simple agent-based classes for modularity
- **Free Tier Friendly**: Works entirely with free APIs and tools
- **Fallback Ready**: Continues working even when AI services fail
- **Extensible**: Easy to add new data sources and scoring criteria