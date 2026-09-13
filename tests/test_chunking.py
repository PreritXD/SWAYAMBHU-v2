"""
Tests for Semantic Sliding-Window Chunker, Timestamp Preservation, and Transcript Cleaning
"""

from chunking import SemanticSlidingWindowChunker, format_timestamp, normalize_transcript_text
from schema import SourceChannel, TranscriptSegment


def test_format_timestamp():
    """Verifies timestamp formatting into MM:SS and HH:MM:SS."""
    assert format_timestamp(0) == "00:00"
    assert format_timestamp(75) == "01:15"
    assert format_timestamp(3665) == "01:01:05"


def test_normalize_transcript_text():
    """Verifies removal of fillers and transcription artifacts."""
    raw = "हाँ मतलब तो भाई देखो महाराज जी बोले कि नाम जप नाम जप करो [संगीत]"
    clean = normalize_transcript_text(raw)
    assert "हाँ" not in clean
    assert "मतलब" not in clean
    assert "तो भाई" not in clean
    assert "[संगीत]" not in clean
    assert "नाम जप" in clean


def test_sliding_window_chunking_and_timestamps():
    """Verifies sliding window accumulation and accurate timestamp preservation."""
    chunker = SemanticSlidingWindowChunker(
        target_duration_sec=30.0,
        overlap_duration_sec=10.0,
        min_chunk_duration_sec=5.0
    )

    # Synthetic transcript segments
    segments = [
        TranscriptSegment(text="पूज्य महाराज जी कहते हैं", start=0.0, duration=10.0),
        TranscriptSegment(text="कि नाम जप ही कलियुग का परम साधन है", start=10.0, duration=10.0),
        TranscriptSegment(text="निरंतर श्री राधा नाम का आश्रय लेना चाहिए", start=20.0, duration=10.0),
        TranscriptSegment(text="मन के बुरे विचारों से घबराना नहीं चाहिए", start=30.0, duration=10.0),
        TranscriptSegment(text="यह सब नाम के प्रभाव से नष्ट हो जाएंगे", start=40.0, duration=10.0),
    ]

    chunks = chunker.chunk_segments(
        segments=segments,
        video_id="test_vid_123",
        channel_id=SourceChannel.BHAJAN_MARG,
    )

    assert len(chunks) >= 2
    c0 = chunks[0]
    assert c0.video_id == "test_vid_123"
    assert c0.channel_id == SourceChannel.BHAJAN_MARG
    assert c0.start_sec == 0
    assert c0.end_sec >= 30
    assert c0.start_formatted == "00:00"
    assert "नाम जप" in c0.clean_text

    # Verify overlap: chunk 1 should start before chunk 0 ends
    c1 = chunks[1]
    assert c1.start_sec < c0.end_sec
