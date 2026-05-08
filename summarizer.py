"""
summarizer.py — Sindhu
──────────────────────
Uses Google Gemini API (free tier) for summarization + Sindhi translation.
Model: gemini-2.5-flash (current free model as of 2026)

Free tier limits: 10 RPM, 500 RPD — plenty for personal use.
Get your free API key: https://aistudio.google.com/apikey
Set GEMINI_API_KEY environment variable before running.
"""

import os
import json
import logging
import re
import time
import urllib.request
import urllib.error
from transcript import chunk_transcript

logger = logging.getLogger(__name__)

MAX_DIRECT_CHARS = 12_000
CHUNK_SIZE       = 4_000
GEMINI_MODEL     = "gemini-2.5-flash"
GEMINI_API_URL   = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

MAX_RETRIES  = 3
RETRY_DELAY  = 10

# ─── Prompts ─────────────────────────────────────────────────────────────────

CHUNK_SUMMARY_PROMPT = """\
You are a helpful assistant that condenses video transcript sections.
Extract the most important points in 3-5 concise English bullet points.
Be factual. No opinions. Stay brief.

Transcript section:
{chunk}

Respond ONLY with bullet points, one per line, starting with "•". No other text.\
"""

FINAL_SUMMARY_PROMPT = """\
You are an expert multilingual summarizer and Sindhi language specialist.

TASK:
1. Read the provided transcript or combined section summaries.
2. Write 3 concise English bullet points summarising the content. Each bullet must be ONE short sentence only — maximum 12 words.
3. Write 1 short English paragraph summarising the content.
4. Translate BOTH into natural, conversational Sindhi (سنڌي). Each Sindhi bullet must also be ONE short sentence only.
   - Do NOT translate literally — write as a fluent Sindhi speaker would speak.
   - Use everyday vocabulary. Keep common loanwords (video, internet, mobile).
   - Use Arabic-script Sindhi (Nastaliq).

Transcript / summaries:
{transcript}

YOU MUST respond with ONLY a raw JSON object. No explanation, no markdown, no ```json fences.
Start your response with {{ and end with }}. Nothing before or after.

{{
  "bullet_summary_english": ["Point 1", "Point 2", "Point 3"],
  "explanation_english": "One paragraph in English.",
  "bullet_summary_sindhi": ["نقطو ١", "نقطو ٢", "نقطو ٣"],
  "explanation_sindhi": "سنڌيءَ ۾ هڪ پيراگراف."
}}\
"""


# ─── Gemini API Call ──────────────────────────────────────────────────────────

def _call_gemini(prompt: str, max_tokens: int = 2000) -> str:
    """Call Gemini API with automatic retry on 429 rate limit errors."""
    api_key = api_key 

    url = f"{GEMINI_API_URL}?key={api_key}"

    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature":        0.1,      # Very low temp = more predictable JSON
            "maxOutputTokens":    max_tokens,
            "responseMimeType":   "application/json",  # Force JSON output mode
        },
    }).encode()

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode())
                # Extract text from response
                text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                logger.info(f"Gemini raw response (first 200 chars): {text[:200]}")
                return text

        except urllib.error.HTTPError as e:
            body = e.read().decode()
            if e.code == 429:
                if attempt < MAX_RETRIES:
                    wait = RETRY_DELAY * attempt
                    logger.warning(f"Rate limited. Waiting {wait}s (attempt {attempt}/{MAX_RETRIES})...")
                    time.sleep(wait)
                    continue
                raise RuntimeError(
                    "Gemini rate limit exceeded. Free tier resets at midnight Pacific Time.\n"
                    "Try again in a few minutes."
                )
            if e.code == 403:
                raise RuntimeError("Invalid Gemini API key. Check your GEMINI_API_KEY.")
            raise RuntimeError(f"Gemini API error {e.code}: {body}")

    raise RuntimeError("Gemini request failed after all retries.")


# ─── JSON Parsing ─────────────────────────────────────────────────────────────

def _parse_json(raw: str) -> dict:
    """
    Robustly parse JSON from Gemini output.
    Handles:
      - Clean JSON
      - ```json ... ``` fences
      - Thinking/preamble text before the JSON object
      - Trailing text after the JSON object
    """
    cleaned = raw.strip()

    # 1. Strip markdown fences
    cleaned = re.sub(r"^```[a-z]*\n?", "", cleaned)
    cleaned = re.sub(r"\n?```$",       "", cleaned).strip()

    # 2. If it starts with { we're good — try direct parse first
    if cleaned.startswith("{"):
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

    # 3. Find the JSON object anywhere in the text (handles preamble/thinking text)
    # Use a greedy match to get the largest possible JSON block
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # 4. Last resort — try to find and fix common issues
    # Sometimes Gemini wraps in extra quotes or adds trailing commas
    try:
        # Remove trailing commas before } or ]
        fixed = re.sub(r",\s*([}\]])", r"\1", cleaned)
        match = re.search(r"\{[\s\S]*\}", fixed)
        if match:
            return json.loads(match.group(0))
    except Exception:
        pass

    logger.error(f"Could not parse JSON. Full raw response:\n{raw}")
    raise json.JSONDecodeError("No valid JSON found in response", raw, 0)


# ─── Main Pipeline ────────────────────────────────────────────────────────────

def summarize_and_translate(transcript: str) -> dict:
    _empty = {
        "success": False,
        "bullet_summary_english": [], "explanation_english": "",
        "bullet_summary_sindhi":  [], "explanation_sindhi":  "",
        "error": "",
    }

    try:
        # Short transcript — single call
        if len(transcript) <= MAX_DIRECT_CHARS:
            logger.info("Short transcript: single Gemini call.")
            input_text = transcript
        else:
            # Long transcript — chunk first
            logger.info(f"Long transcript ({len(transcript)} chars): chunking...")
            chunks = chunk_transcript(transcript, chunk_size=CHUNK_SIZE)
            logger.info(f"{len(chunks)} chunks created.")

            summaries = []
            for i, chunk in enumerate(chunks):
                logger.info(f"  Chunk {i+1}/{len(chunks)}...")
                summaries.append(_call_gemini(
                    CHUNK_SUMMARY_PROMPT.format(chunk=chunk),
                    max_tokens=400,
                ))
                time.sleep(2)  # Stay within RPM limit

            input_text = (
                "Section-by-section summaries — synthesize into one:\n\n"
                + "\n\n---\n\n".join(summaries)
            )
            logger.info("Chunks done. Final synthesis...")

        # Final call
        raw = _call_gemini(
            FINAL_SUMMARY_PROMPT.format(transcript=input_text),
            max_tokens=2000,
        )
        logger.info("Parsing JSON...")
        parsed = _parse_json(raw)

        # Validate required keys
        for key in ("bullet_summary_english", "explanation_english",
                    "bullet_summary_sindhi",  "explanation_sindhi"):
            if key not in parsed:
                raise ValueError(f"Missing key in response: '{key}'")

        # Ensure exactly 3 bullets
        for field in ("bullet_summary_english", "bullet_summary_sindhi"):
            while len(parsed[field]) < 3:
                parsed[field].append("—")
            parsed[field] = parsed[field][:3]

        return {
            "success":                True,
            "bullet_summary_english": parsed["bullet_summary_english"],
            "explanation_english":    parsed["explanation_english"],
            "bullet_summary_sindhi":  parsed["bullet_summary_sindhi"],
            "explanation_sindhi":     parsed["explanation_sindhi"],
            "error":                  "",
        }

    except RuntimeError as e:
        return {**_empty, "error": str(e)}

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed: {e}")
        return {**_empty, "error": "Model returned malformed output. Please try again."}

    except Exception as e:
        logger.error(f"Summarization error: {e}")
        return {**_empty, "error": f"Summarization failed: {e}"}
