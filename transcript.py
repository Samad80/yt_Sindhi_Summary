"""
transcript.py — Sindhu
──────────────────────
Handles YouTube transcript extraction.
Compatible with both youtube-transcript-api v0.x and v1.x
"""

import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

CHUNK_SIZE = 3_000


def extract_video_id(url: str) -> str | None:
    """Extract video ID from any YouTube URL format."""
    match = re.search(r"(?:v=|youtu\.be/|shorts/|embed/)([A-Za-z0-9_-]{11})", url)
    return match.group(1) if match else None


def _get_transcript_text(video_id: str) -> str:
    """
    Fetch transcript using whichever API version is installed.
    v1.x: YouTubeTranscriptApi().list(video_id)
    v0.x: YouTubeTranscriptApi.list_transcripts(video_id)
    """
    from youtube_transcript_api import YouTubeTranscriptApi

    # Detect version by checking available methods
    api_instance = YouTubeTranscriptApi()
    use_new_api = hasattr(api_instance, 'list')

    if use_new_api:
        # v1.x — instance based
        logger.info("Using youtube-transcript-api v1.x")
        transcript_list = api_instance.list(video_id)
    else:
        # v0.x — class method based
        logger.info("Using youtube-transcript-api v0.x")
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

    transcript = None

    # Priority 1: manually created English
    try:
        transcript = transcript_list.find_manually_created_transcript(
            ["en", "en-US", "en-GB"]
        )
    except Exception:
        pass

    # Priority 2: auto-generated English
    if not transcript:
        try:
            transcript = transcript_list.find_generated_transcript(
                ["en", "en-US", "en-GB"]
            )
        except Exception:
            pass

    # Priority 3: any language, translated to English
    if not transcript:
        try:
            available = list(transcript_list)
            if available:
                transcript = available[0].translate("en")
        except Exception:
            pass

    # Priority 4: any language as-is (fallback — LLM can still summarize)
    if not transcript:
        try:
            available = list(transcript_list)
            if available:
                transcript = available[0]
        except Exception:
            pass

    if not transcript:
        raise Exception("No transcript available for this video.")

    # Fetch segments
    raw = transcript.fetch()

    # Handle both v0.x (dicts) and v1.x (objects)
    text_parts = []
    for seg in raw:
        if hasattr(seg, 'text'):
            text = seg.text          # v1.x object
        elif isinstance(seg, dict):
            text = seg.get('text', '')  # v0.x dict
        else:
            text = str(seg)
        if text:
            text_parts.append(text.strip())

    return " ".join(text_parts)


def extract_transcript(url: str) -> Dict[str, Any]:
    """Extract and return full transcript text from a YouTube URL."""
    video_id = extract_video_id(url)
    if not video_id:
        return {
            "success": False, "text": "",
            "error": (
                "Invalid YouTube URL. Please use a link like:\n"
                "https://www.youtube.com/watch?v=VIDEO_ID"
            ),
        }

    try:
        from youtube_transcript_api import (
            NoTranscriptFound,
            TranscriptsDisabled,
            VideoUnavailable,
        )

        full_text = _get_transcript_text(video_id)

        # Clean artifacts like [Music], [Applause]
        full_text = re.sub(r"\[.*?\]", "", full_text)
        full_text = re.sub(r"\s+", " ", full_text).strip()

        if len(full_text) < 50:
            return {
                "success": False, "text": "",
                "error": "Transcript is too short or empty to summarize.",
            }

        logger.info(f"Transcript OK: {len(full_text)} chars, video_id={video_id}")
        return {"success": True, "text": full_text, "error": ""}

    except NoTranscriptFound:
        return {"success": False, "text": "",
                "error": "No transcript found. Captions may be disabled for this video."}
    except TranscriptsDisabled:
        return {"success": False, "text": "",
                "error": "Transcripts are disabled for this video by the uploader."}
    except VideoUnavailable:
        return {"success": False, "text": "",
                "error": "This video is unavailable or private."}
    except Exception as e:
        err = str(e)
        if "429" in err or "Too Many Requests" in err:
            return {"success": False, "text": "",
                    "error": "YouTube is rate-limiting requests. Wait 2–5 minutes and try again."}
        logger.error(f"Transcript error: {e}")
        return {"success": False, "text": "", "error": f"Failed to fetch transcript: {err}"}


def chunk_transcript(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    """Split long transcript into overlapping chunks at sentence boundaries."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks, current_chunk, current_length = [], [], 0

    for sentence in sentences:
        slen = len(sentence)
        if current_length + slen > chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = current_chunk[-2:]
            current_length = sum(len(s) for s in current_chunk)
        current_chunk.append(sentence)
        current_length += slen

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks
