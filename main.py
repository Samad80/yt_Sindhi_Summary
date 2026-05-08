"""
YouTube Video Summarizer in Sindhi — Sindhu
FastAPI Backend — Main Entry Point
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
import logging

from transcript import extract_transcript
from summarizer import summarize_and_translate

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ─── App ─────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Sindhu — YouTube Sindhi Summarizer",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to index.html — same folder as main.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_HTML = os.path.join(BASE_DIR, "index.html")


# ─── Models ──────────────────────────────────────────────────────────────────
class SummarizeRequest(BaseModel):
    url: str


class SummarizeResponse(BaseModel):
    bullet_summary_sindhi: list[str]
    explanation_sindhi: str
    bullet_summary_english: list[str]
    explanation_english: str
    transcript_preview: str


# ─── Routes ──────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve index.html from the same directory as main.py."""
    try:
        with open(INDEX_HTML, encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="<h2>index.html not found. Make sure it is in the backend/ folder.</h2>",
            status_code=404,
        )


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest):
    url = request.url.strip()
    logger.info(f"Summarize request: {url}")

    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty.")

    # Step 1: Extract transcript
    logger.info("Extracting transcript...")
    transcript_result = extract_transcript(url)
    if not transcript_result["success"]:
        raise HTTPException(status_code=422, detail=transcript_result["error"])

    transcript_text = transcript_result["text"]
    transcript_preview = transcript_text[:800] + ("..." if len(transcript_text) > 800 else "")
    logger.info(f"Transcript: {len(transcript_text)} chars")

    # Step 2+3: Summarize → English → Sindhi
    logger.info("Summarizing and translating...")
    summary_result = summarize_and_translate(transcript_text)
    if not summary_result["success"]:
        raise HTTPException(status_code=500, detail=summary_result["error"])

    logger.info("Done!")
    return SummarizeResponse(
        bullet_summary_sindhi=summary_result["bullet_summary_sindhi"],
        explanation_sindhi=summary_result["explanation_sindhi"],
        bullet_summary_english=summary_result["bullet_summary_english"],
        explanation_english=summary_result["explanation_english"],
        transcript_preview=transcript_preview,
    )


@app.get("/health")
async def health():
    return {"status": "ok"}