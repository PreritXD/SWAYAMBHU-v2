"""
Tests for Cross-Channel Deduplication (Whole-Video & Chunk-Level) and Deterministic Tie-Breaking
"""

from datetime import date
import pytest
from dedup import (
    CrossChannelDeduplicator,
    compute_jaccard_similarity,
    get_character_ngrams,
    is_candidate_more_canonical,
)
from schema import ChunkRecord, SourceChannel, VideoMetadata


def test_deterministic_tie_breaking_rules():
    """
    Tie-breaking hierarchy:
    1. Earliest upload_date
    2. Channel priority: bhajan_marg > sadhan_path
    3. Alphanumeric sort on video_id
    """
    # 1. Earliest date wins
    assert is_candidate_more_canonical(
        cand_date=date(2023, 1, 1),
        cand_channel=SourceChannel.SADHAN_PATH,
        cand_vid="vid_sp",
        target_date=date(2023, 6, 1),
        target_channel=SourceChannel.BHAJAN_MARG,
        target_vid="vid_bm",
    ) is True

    # 2. Equal dates -> bhajan_marg wins over sadhan_path
    assert is_candidate_more_canonical(
        cand_date=date(2023, 5, 1),
        cand_channel=SourceChannel.BHAJAN_MARG,
        cand_vid="vid_bm",
        target_date=date(2023, 5, 1),
        target_channel=SourceChannel.SADHAN_PATH,
        target_vid="vid_sp",
    ) is True

    # 3. Same date and same channel -> alphanumeric video_id
    assert is_candidate_more_canonical(
        cand_date=date(2023, 5, 1),
        cand_channel=SourceChannel.BHAJAN_MARG,
        cand_vid="vid_aaa",
        target_date=date(2023, 5, 1),
        target_channel=SourceChannel.BHAJAN_MARG,
        target_vid="vid_zzz",
    ) is True


def test_whole_video_deduplication():
    """Verifies that an identical or near-identical video from another channel is flagged."""
    deduplicator = CrossChannelDeduplicator(video_similarity_threshold=0.80)

    # Existing video on Bhajan Marg
    bm_video = VideoMetadata(
        video_id="bm_001",
        channel_id=SourceChannel.BHAJAN_MARG,
        title="नाम अपराध और भक्ति के रहस्य - एकांतिक वार्तालाप",
        url="https://youtube.com/watch?v=bm_001",
        upload_date=date(2023, 2, 10),
    )
    transcript_bm = (
        "पूज्य महाराज जी कहते हैं कि नाम अपराध से साधक को सर्वथा बचना चाहिए। "
        "संतों की निंदा करना, शास्त्रों में अश्रद्धा रखना, और नाम के बल पर पाप करना नाम अपराध है। "
        "जो साधक श्री राधा नाम का आश्रय लेता है, उसके समस्त संशय नष्ट हो जाते हैं।"
    )

    catalog = [(bm_video, transcript_bm)]

    # New video re-uploaded on Sadhan Path with overlapping satsang
    sp_video = VideoMetadata(
        video_id="sp_001",
        channel_id=SourceChannel.SADHAN_PATH,
        title="नाम अपराध से कैसे बचें? पूज्य प्रेमानंद जी महाराज",
        url="https://youtube.com/watch?v=sp_001",
        upload_date=date(2023, 4, 15),  # Uploaded later
    )
    transcript_sp = (
        "पूज्य महाराज जी कहते हैं कि नाम अपराध से साधक को सर्वथा बचना चाहिए। "
        "संतों की निंदा करना, शास्त्रों में अश्रद्धा रखना, और नाम के बल पर पाप करना नाम अपराध है। "
        "श्री राधा नाम का आश्रय लेने से सब संशय नष्ट हो जाते हैं।"
    )

    match = deduplicator.check_video_duplicate(sp_video, transcript_sp, catalog)

    assert match.is_duplicate is True
    assert match.canonical_video_id == "bm_001"
    assert match.canonical_channel_id == SourceChannel.BHAJAN_MARG
    assert match.similarity_score >= 0.80


def test_chunk_level_deduplication_and_aliasing():
    """Verifies that a short clip re-cut matching a chunk in an existing discourse is flagged and aliased."""
    deduplicator = CrossChannelDeduplicator(chunk_similarity_threshold=0.85)

    canonical_chunk = ChunkRecord(
        id="chunk-canonical-1",
        video_id="bm_full_satsang",
        channel_id=SourceChannel.BHAJAN_MARG,
        chunk_index=4,
        start_sec=120,
        end_sec=170,
        start_formatted="02:00",
        end_formatted="02:50",
        raw_text="दोष दर्शन कभी नहीं करना चाहिए। दूसरों के दोष देखने से हमारी बुद्धि मलिन हो जाती है।",
        clean_text="दोष दर्शन कभी नहीं करना चाहिए। दूसरों के दोष देखने से हमारी बुद्धि मलिन हो जाती है।",
        token_count=25,
    )

    existing_chunks = [canonical_chunk]

    # Re-cut short clip chunk from Sadhan Path
    clip_chunk = ChunkRecord(
        id="chunk-clip-2",
        video_id="sp_short_clip",
        channel_id=SourceChannel.SADHAN_PATH,
        chunk_index=0,
        start_sec=10,
        end_sec=60,
        start_formatted="00:10",
        end_formatted="01:00",
        raw_text="दोष दर्शन कभी नहीं करना चाहिए। दूसरों के दोष देखने से हमारी बुद्धि मलिन हो जाती है।",
        clean_text="दोष दर्शन कभी नहीं करना चाहिए। दूसरों के दोष देखने से हमारी बुद्धि मलिन हो जाती है।",
        token_count=25,
    )

    match = deduplicator.check_chunk_duplicate(
        new_chunk=clip_chunk,
        existing_chunks=existing_chunks,
        new_video_date=date(2023, 5, 1),
        existing_video_dates={"bm_full_satsang": date(2023, 1, 1)},
    )

    assert match.is_duplicate is True
    assert match.matched_chunk_id == "chunk-canonical-1"

    # Test alias attachment
    deduplicator.attach_cross_channel_alias(canonical_chunk, clip_chunk, video_title="Clip Title")
    assert len(canonical_chunk.cross_channel_aliases) == 1
    alias = canonical_chunk.cross_channel_aliases[0]
    assert alias.channel == SourceChannel.SADHAN_PATH
    assert alias.video_id == "sp_short_clip"
    assert alias.timestamp_formatted == "00:10"
