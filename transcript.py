"""
transcript.py — Sindhu
──────────────────────
Handles YouTube transcript extraction via youtube-transcript-api v1.x.
Supports chunking for very long transcripts.

NOTE: v1.x uses instance-based API — YouTubeTranscriptApi() not class methods.
"""

import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

CHUNK_SIZE = 3_000   # Characters per chunk (conservative for local LLMs)


def extract_video_id(url: str) -> str | None:
    """
    Extract video ID from all common YouTube URL formats:
      - https://www.youtube.com/watch?v=VIDEO_ID
      - https://youtu.be/VIDEO_ID
      - https://www.youtube.com/shorts/VIDEO_ID
      - https://www.youtube.com/embed/VIDEO_ID
    """
    match = re.search(r"(?:v=|youtu\.be/|shorts/|embed/)([A-Za-z0-9_-]{11})", url)
    return match.group(1) if match else None


def extract_transcript(url: str) -> Dict[str, Any]:
    """
    Extract and return full transcript text from a YouTube URL.

    Returns:
        { "success": bool, "text": str, "error": str }
    """
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
        # v1.x: instantiate the class first
        from youtube_transcript_api import YouTubeTranscriptApi,NoTranscriptFound,TranscriptsDisabled,VideoUnavailable
        

        ytt = YouTubeTranscriptApi()

        # List available transcripts for this video
        transcript_list = ytt.list(video_id)

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

        if not transcript:
            return {
                "success": False, "text": "",
                "error": "No transcript available for this video. Captions may be disabled.",
            }

        # Fetch the actual transcript segments
        raw = transcript.fetch()

        # Join segments — each segment has a .text attribute in v1.x
        text_parts = []
        for seg in raw:
            # v1.x returns FetchedTranscriptSnippet objects with .text attribute
            text = seg.text if hasattr(seg, "text") else seg.get("text", "")
            if text:
                text_parts.append(text.strip())

        full_text = " ".join(text_parts)

        # Clean common transcript artifacts
        full_text = re.sub(r"\[.*?\]", "", full_text)   # [Music], [Applause], etc.
        full_text = re.sub(r"\s+", " ", full_text).strip()

        if len(full_text) < 50:
            return {
                "success": False, "text": "",
                "error": "Transcript is too short or empty to summarize.",
            }

        logger.info(f"Transcript OK: {len(full_text)} chars, video_id={video_id}")
        return {"success": True, "text": full_text, "error": ""}

    except NoTranscriptFound:
        return {
            "success": False, "text": "",
            "error": "No transcript found. Captions may be disabled for this video.",
        }
    except TranscriptsDisabled:
        return {
            "success": False, "text": "",
            "error": "Transcripts are disabled for this video by the uploader.",
        }
    except VideoUnavailable:
        return {
            "success": False, "text": "",
            "error": "This video is unavailable or private.",
        }
    except Exception as e:
        err = str(e)
        # Friendly message for rate limiting
        if "429" in err or "Too Many Requests" in err:
            return {
                "success": False, "text": "",
                "error": (
                    "YouTube is rate-limiting requests from your IP (429 error). "
                    "Please wait 2–5 minutes and try again, or try a different video."
                ),
            }
        logger.error(f"Transcript error: {e}")
        return {"success": False, "text": "", "error": f"Failed to fetch transcript: {err}"}


def chunk_transcript(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    """
    Split a long transcript into overlapping chunks at sentence boundaries.
    Prevents cutting mid-sentence when sending to the LLM.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks, current_chunk, current_length = [], [], 0

    for sentence in sentences:
        slen = len(sentence)
        if current_length + slen > chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = current_chunk[-2:]   # 2-sentence overlap for context
            current_length = sum(len(s) for s in current_chunk)
        current_chunk.append(sentence)
        current_length += slen

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks