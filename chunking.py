"""
SWAYAMBHU v2 - Semantic Sliding-Window Chunker & Transcript Normalizer

Processes timestamped subtitle/whisper segments into ~50s / 400-token semantic windows
with ~15s overlap. Strips verbal fillers, normalizes Unicode (NFC), cleans transcription
artifacts, and accurately preserves start/end seconds and formatted timestamps.
"""

import re
import unicodedata
from typing import List, Tuple
from schema import ChunkRecord, SourceChannel, TranscriptSegment


# Common Hindi verbal fillers and discourse markers to clean
HINDI_VERBAL_FILLERS = [
    "तो भाई",
    "देखो भाई",
    "सुनो भाई",
    "बात क्या है",
    "कहते हैं ना",
    "जैसे कि",
    "हाँ",
    "मतलब",
    "भाई",
    "अरे",
    "हूँ",
    "हूँ-",
    "समझे",
    "समझो",
    "बोले",
    "uh",
    "um",
    "ah",
]

# Common repeated stutter artifacts (e.g. "नाम नाम नाम" -> "नाम")
STUTTER_PATTERN = re.compile(r"\b(\w+)(?:\s+\1\b){2,}", flags=re.UNICODE)


def format_timestamp(seconds: float) -> str:
    """Formats seconds into MM:SS or HH:MM:SS format."""
    total_seconds = int(max(0, seconds))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def normalize_transcript_text(text: str) -> str:
    """
    Normalizes transcript text:
    1. NFC Unicode normalization.
    2. Strips verbal fillers.
    3. Collapses repeated stutters.
    4. Normalizes whitespace and standard punctuation.
    """
    if not text:
        return ""

    # 1. Unicode NFC normalization
    text = unicodedata.normalize("NFC", text)

    # 2. Clean strange transcription artifact brackets [संगीत], [तालियाँ], [Music]
    text = re.sub(r"\[.*?\]", " ", text)
    text = re.sub(r"\(.*?\)", " ", text)

    # 3. Clean stutters (e.g. repeated words)
    text = STUTTER_PATTERN.sub(r"\1", text)

    # 4. Remove verbal fillers using word/space boundary logic
    for filler in sorted(HINDI_VERBAL_FILLERS, key=len, reverse=True):
        # Match filler surrounded by whitespace, start/end of string, or punctuation
        pat = re.compile(r"(?:^|(?<=\s)|(?<=[।,?!]))" + re.escape(filler) + r"(?=$|(?=\s)|(?=[।,?!]))", re.IGNORECASE | re.UNICODE)
        text = pat.sub(" ", text)

    # 5. Clean excessive spaces and dangling punctuation
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*([।,?!])", r"\1", text)

    return text.strip()


def estimate_tokens(text: str) -> int:
    """Rough token estimation for multilingual text (average ~3-4 chars per token)."""
    return len(text.split()) + (len(text) // 8)


class SemanticSlidingWindowChunker:
    """
    Splits continuous timestamped transcript segments into overlapping windows.
    Target window: ~50 seconds or ~350-400 tokens, with ~15 seconds overlap.
    """

    def __init__(
        self,
        target_duration_sec: float = 50.0,
        overlap_duration_sec: float = 15.0,
        target_max_tokens: int = 400,
        min_chunk_duration_sec: float = 10.0,
    ):
        self.target_duration_sec = target_duration_sec
        self.overlap_duration_sec = overlap_duration_sec
        self.target_max_tokens = target_max_tokens
        self.min_chunk_duration_sec = min_chunk_duration_sec

    def chunk_segments(
        self,
        segments: List[TranscriptSegment],
        video_id: str,
        channel_id: SourceChannel,
    ) -> List[ChunkRecord]:
        """
        Takes sorted TranscriptSegments and generates overlapping ChunkRecords.
        """
        if not segments:
            return []

        chunks: List[ChunkRecord] = []
        n = len(segments)
        start_idx = 0
        chunk_counter = 0

        while start_idx < n:
            current_start_sec = segments[start_idx].start
            accumulated_segments: List[TranscriptSegment] = []
            current_end_sec = current_start_sec

            idx = start_idx
            while idx < n:
                seg = segments[idx]
                seg_end = seg.end if seg.end is not None else (seg.start + seg.duration)
                duration = seg_end - current_start_sec
                current_raw = " ".join(s.text for s in accumulated_segments + [seg])
                token_count = estimate_tokens(current_raw)

                accumulated_segments.append(seg)
                current_end_sec = seg_end

                # Stop accumulating if we reach target duration or token threshold
                if duration >= self.target_duration_sec or token_count >= self.target_max_tokens:
                    break
                idx += 1

            # Build chunk text
            raw_text = " ".join(s.text for s in accumulated_segments).strip()
            clean_text = normalize_transcript_text(raw_text)

            # Only emit if has meaningful content
            chunk_duration = current_end_sec - current_start_sec
            if clean_text and (chunk_duration >= self.min_chunk_duration_sec or idx >= n - 1):
                chunk = ChunkRecord(
                    video_id=video_id,
                    channel_id=channel_id,
                    chunk_index=chunk_counter,
                    start_sec=int(current_start_sec),
                    end_sec=int(current_end_sec),
                    start_formatted=format_timestamp(current_start_sec),
                    end_formatted=format_timestamp(current_end_sec),
                    raw_text=raw_text,
                    clean_text=clean_text,
                    token_count=estimate_tokens(clean_text),
                )
                chunks.append(chunk)
                chunk_counter += 1

            if idx >= n - 1:
                # Reached the end of transcript
                break

            # Find next start_idx using overlap:
            # Step forward until segment starts after (current_end_sec - overlap_duration_sec)
            overlap_target = current_end_sec - self.overlap_duration_sec
            next_start_idx = start_idx + 1
            while next_start_idx <= idx and segments[next_start_idx].start < overlap_target:
                next_start_idx += 1

            # Ensure strict progress
            if next_start_idx <= start_idx:
                next_start_idx = start_idx + 1

            start_idx = next_start_idx

        return chunks
