# 🌊 Sindhu — YouTube Sindhi Summarizer
### يوٽيوب ويڊيو خلاصو — سنڌيءَ ۾

Extracts a YouTube transcript, summarizes it, and translates into natural conversational **Sindhi** — powered entirely by a **local LLM** (no paid API needed).

---

## 🏗 Project Structure

```
yt-sindhi-summarizer/
├── main.py          ← FastAPI app + routes
├── transcript.py    ← YouTube transcript extraction + chunking
└── summarizer.py    ← Local LLM: summarize → Sindhi translate
└── index.html       ← Single-page Ajrak-themed UI
├── requirements.txt
└── README.md
```

---

## 🤖 Model: `gemma3:4b` (via Ollama)

**Why Gemma 3 4B?**
- Runs on a laptop (CPU or GPU)
- Strong multilingual ability — handles Sindhi's Arabic-Nastaliq script well
- Instruction-tuned → reliably follows structured JSON prompts
- ~3 GB download, fits in 8 GB RAM

**Alternative:** Set `SINDHU_BACKEND=hf` to load `google/gemma-3-4b-it` directly via HuggingFace (see below).

---

## 🚀 Quick Start — Ollama (Recommended)

### 1. Set up the project

```bash
cd yt-sindhi-summarizer

# Create virtual environment
python -m venv .venv

# Activate it
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows (Command Prompt)
.venv\Scripts\Activate.ps1       # Windows (PowerShell)

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Install Ollama + pull the model

```bash
# Install Ollama (visit https://ollama.com for GUI installer, or):
curl -fsSL https://ollama.com/install.sh | sh   # Linux
# macOS: download from https://ollama.com/download

# Pull Gemma 3 4B (~3 GB download)
ollama pull gemma3:4b

# Start Ollama server (leave this running in a separate terminal)
ollama serve
```

### 3. Start Sindhu

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 4. Open the app

→ **http://localhost:8000**

---

## 🔬 Alternative: HuggingFace Backend

Use this if you want to load the model directly without Ollama.

```bash
# Install extra dependencies
pip install transformers accelerate torch
pip install bitsandbytes   # GPU only (4-bit quantization)

# Set the backend
export SINDHU_BACKEND=hf              # macOS/Linux
set SINDHU_BACKEND=hf                 # Windows CMD
$env:SINDHU_BACKEND="hf"             # PowerShell

# Optionally change the model (default: google/gemma-3-4b-it)
export HF_MODEL_ID=mistralai/Mistral-7B-Instruct-v0.3

# Start
cd backend
uvicorn main:app --reload --port 8000
```

> ⚠️ First run downloads model weights (~3–8 GB). Be patient.

---

## ⚙️ Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SINDHU_BACKEND` | `ollama` | `ollama` or `hf` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server address |
| `OLLAMA_MODEL` | `gemma3:4b` | Any model pulled in Ollama |
| `HF_MODEL_ID` | `google/gemma-3-4b-it` | HuggingFace model ID |

---

## 🧪 Example Test

### Via the UI
1. Open http://localhost:8000
2. Paste a YouTube URL (English captions work best), e.g.:
   ```
   https://www.youtube.com/watch?v=dQw4w9WgXcQ
   ```
3. Click **خلاصو ڪريو ▶**
4. Wait ~20–60 seconds (local inference is slower than cloud APIs)
5. Toggle between **سنڌي** and **English** views

### Via curl
```bash
curl -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

---

## ⚠️ Error Cases Handled

| Situation | Message |
|---|---|
| Invalid URL | "Invalid YouTube URL" |
| No captions | "No transcript found" |
| Private video | "Video is unavailable" |
| Ollama not running | "Ollama request failed. Start with: ollama serve" |
| HF deps missing | "Install: transformers accelerate torch" |
| Malformed JSON from model | "Model returned malformed JSON — try again" |

---

## 💡 Tips

- **Speed:** Ollama with GPU is fastest (~10–20s). CPU-only expect 1–3 minutes.
- **Quality:** If Sindhi output looks off, try `ollama pull gemma3:12b` and set `OLLAMA_MODEL=gemma3:12b` for better multilingual quality.
- **Deactivate venv:** `deactivate`
