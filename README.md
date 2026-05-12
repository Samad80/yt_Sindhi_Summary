---
title: Sindhu — YouTube Sindhi Summarizer
emoji: 🌊
colorFrom: indigo
colorTo: red
sdk: gradio
sdk_version: "4.44.0"
app_file: app.py
pinned: false
license: mit
short_description: يوٽيوب ويڊيو خلاصو — سنڌيءَ ۾
---

# 🌊 Sindhu — YouTube Sindhi Summarizer
### يوٽيوب ويڊيو خلاصو — سنڌيءَ ۾

A web app that extracts a YouTube transcript, summarizes it into 3 bullet points, and translates into natural conversational **Sindhi** — powered by Google Gemini API (free).

## Setup

1. Fork/clone this Space
2. Go to **Settings → Secrets** and add: `GEMINI_API_KEY=AIza...your-key`
3. Get a free key at → https://aistudio.google.com/apikey

## Project Structure

```
├── app.py            ← FastAPI app (HF Spaces entry point)
├── transcript.py     ← YouTube transcript extraction
├── summarizer.py     ← Gemini summarization + Sindhi translation
├── index.html        ← Ajrak-themed RTL frontend
└── requirements.txt
```

## API

### `POST /summarize`
```json
{ "url": "https://www.youtube.com/watch?v=..." }
```

### `GET /health`
```json
{ "status": "ok" }
```

## Tips

- **Best videos:** TED Talks, BBC, educational channels (always have captions)
- **Free tier limits:** 500 requests/day, 10 requests/minute on Gemini free tier
- If you hit rate limits, wait a few minutes and try again
