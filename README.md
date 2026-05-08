# 🌊 Sindhu — YouTube Sindhi Summarizer
### يوٽيوب ويڊيو خلاصو — سنڌيءَ ۾

A web app that extracts a YouTube transcript, summarizes it into 3 bullet points, and translates into natural conversational **Sindhi** — powered by Google Gemini API (free).

---

## 🏗 Project Structure

```
sindhu/
├── backend/
│   ├── main.py          ← FastAPI app + routes
│   ├── index.html       ← Frontend UI (must be in backend/ folder)
│   ├── transcript.py    ← YouTube transcript extraction + chunking
│   └── summarizer.py    ← Gemini API: summarize → Sindhi translate
├── requirements.txt
└── README.md
```

---

## ⚙️ Prerequisites

- Python 3.11+
- A free **Google Gemini API key** → https://aistudio.google.com/apikey

---

## 🚀 Quick Start

### 1. Set up virtual environment

```bash
cd sindhu

python -m venv .venv

# Activate — Mac/Linux:
source .venv/bin/activate

# Activate — Windows CMD:
.venv\Scripts\activate

# Activate — Windows PowerShell:
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Get your free Gemini API key

- Go to → https://aistudio.google.com/apikey
- Sign in with Google
- Click **Create API Key**
- Copy the key (starts with `AIza...`)

### 4. Set your API key

```bash
# Windows CMD:
set GEMINI_API_KEY=AIza...your-key-here...

# Windows PowerShell:
$env:GEMINI_API_KEY="AIza...your-key-here..."

# Mac/Linux:
export GEMINI_API_KEY=AIza...your-key-here...
```

### 5. Start Sindhu

```bash
cd backend
uvicorn main:app --reload --port 8001
```

### 6. Open in browser

→ **http://localhost:8001**

---

## 🧪 Example Test

Paste any YouTube URL with English captions, e.g.:
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

Click **خلاصو ڪريو ▶** and wait 5–15 seconds for results.

### curl test
```bash
curl -X POST http://localhost:8001/summarize \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

---

## ⚠️ Common Errors & Fixes

| Error | Fix |
|---|---|
| `Could not import module "main"` | Make sure you `cd backend` before running uvicorn |
| `GEMINI_API_KEY is not set` | Run `set GEMINI_API_KEY=AIza...` in the same terminal before uvicorn |
| `503 UNAVAILABLE` | Gemini servers busy — auto-retries 3 times, or wait a minute |
| `429 rate limit` | Free tier limit hit — wait a few minutes and try again |
| `No transcript found` | Video has no captions — try a different video |
| `429 Too Many Requests` (YouTube) | YouTube rate limiting your IP — wait 2–5 minutes |
| `Page not found 404` | Wrong port — make sure you're on http://localhost:8001 |

---

## 🎨 Features

- ✅ 3 bullet-point summary in Sindhi (MB Lateef font)
- ✅ Short paragraph explanation in Sindhi
- ✅ Language toggle — switch between سنڌي and English
- ✅ Collapsible transcript preview
- ✅ Auto-retry on Gemini rate limits and server errors
- ✅ Long transcript chunking → multi-pass summarization
- ✅ Ajrak-inspired RTL Sindhi UI

---

## 🔌 API

### `POST /summarize`
```json
{ "url": "https://www.youtube.com/watch?v=..." }
```

Response:
```json
{
  "bullet_summary_sindhi": ["...", "...", "..."],
  "explanation_sindhi": "...",
  "bullet_summary_english": ["...", "...", "..."],
  "explanation_english": "...",
  "transcript_preview": "..."
}
```

### `GET /health`
```json
{ "status": "ok" }
```

---

## 💡 Tips

- **Best videos to test:** TED Talks, BBC, educational channels — they always have captions
- **Key not working?** Set it in the **same terminal** window before running uvicorn
- **Deactivate venv when done:** `deactivate`
- **Free tier limits:** 500 requests/day, 10 requests/minute on Gemini free tier
