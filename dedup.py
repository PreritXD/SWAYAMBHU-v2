"""
SWAYAMBHU v2 - Cross-Channel Deduplication Engine

Provides 2-tier deduplication:
1. Whole-Video Deduplication: Detects complete or near-complete re-uploads across channels
   using MinHash / shingle Jaccard and cosine similarity.
2. Chunk-Level Deduplication: Detects re-cut short clips (e.g. Sadhan Path publishing a 6-minute
   clip from a 40-minute Bhajan Marg satsang) using dense embedding and lexical overlap.

Deterministic Canonical Tie-Breaking:
  1st: Earliest upload_date (original earlier broadcast is canonical).
  2nd: Channel priority: bhajan_marg > sadhan_path.
  3rd: Lexicographical sort on video_id.
"""

from datetime import date
import hashlib
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from schema import ChunkRecord, CrossChannelAlias, DedupMatch, SourceChannel, VideoMetadata

logger = logging.getLogger("swayambhu.dedup")

# Channel priority order for tie-breaking
CHANNEL_PRIORITY: Dict[SourceChannel, int] = {
    SourceChannel.BHAJAN_MARG: 1,  # Highest priority (primary archive)
    SourceChannel.SADHAN_PATH: 2,
}


def get_character_ngrams(text: str, n: int = 5) -> Set[str]:
    """Generates character n-grams for fast, robust lexical similarity in Hindi."""
    clean = re.sub(r"\s+", "", text)
    if len(clean) < n:
        return {clean}
    return {clean[i:i + n] for i in range(len(clean) - n + 1)}


def get_word_shingles(text: str, k: int = 3) -> Set[str]:
    """Generates word k-shingles."""
    words = text.split()
    if len(words) < k:
        return {" ".join(words)}
    return {" ".join(words[i:i + k]) for i in range(len(words) - k + 1)}


def compute_jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    """Computes standard Jaccard similarity coefficient |A ∩ B| / |A ∪ B|."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return float(intersection) / float(union) if union > 0 else 0.0


def is_candidate_more_canonical(
    cand_date: Optional[date],
    cand_channel: SourceChannel,
    cand_vid: str,
    target_date: Optional[date],
    target_channel: SourceChannel,
    target_vid: str,
) -> bool:
    """
    Applies the deterministic 3-tier tie-breaking rule:
      1. Earliest upload date
      2. Channel priority (bhajan_marg > sadhan_path)
      3. Alphanumeric sort on video_id
    Returns True if 'cand' should be the canonical parent over 'target'.
    """
    # 1. Earliest upload date
    if cand_date and target_date:
        if cand_date < target_date:
            return True
        if cand_date > target_date:
            return False

    # If only one has an upload date, prefer the dated one
    if cand_date and not target_date:
        return True
    if target_date and not cand_date:
        return False

    # 2. Channel priority
    cand_prio = CHANNEL_PRIORITY.get(cand_channel, 99)
    target_prio = CHANNEL_PRIORITY.get(target_channel, 99)
    if cand_prio < target_prio:
        return True
    if cand_prio > target_prio:
        return False

    # 3. Alphanumeric video ID
    return cand_vid < target_vid


class CrossChannelDeduplicator:
    """
    Handles cross-channel and intra-channel deduplication for videos and chunks.
    """

    def __init__(
        self,
        video_similarity_threshold: float = 0.85,
        chunk_similarity_threshold: float = 0.92,
    ):
        self.video_similarity_threshold = video_similarity_threshold
        self.chunk_similarity_threshold = chunk_similarity_threshold

    def check_video_duplicate(
        self,
        new_video: VideoMetadata,
        new_transcript: str,
        catalog_videos: List[Tuple[VideoMetadata, str]],
    ) -> DedupMatch:
        """
        Compares new_transcript against existing catalog (metadata, transcript).
        Returns DedupMatch indicating if new_video is a duplicate of an existing video,
        or if an existing video should be updated to point to new_video as canonical.
        """
        if not new_transcript or not catalog_videos:
            return DedupMatch(
                is_duplicate=False,
                similarity_score=0.0,
                reason="No comparison transcript or catalog empty."
            )

        new_ngrams = get_character_ngrams(new_transcript, n=3)
        new_shingles = get_word_shingles(new_transcript, k=2)
        new_words = set(new_transcript.split())

        best_score = 0.0
        best_match_meta: Optional[VideoMetadata] = None

        for existing_meta, existing_transcript in catalog_videos:
            if existing_meta.video_id == new_video.video_id:
                continue

            exist_ngrams = get_character_ngrams(existing_transcript, n=3)
            ngram_sim = compute_jaccard_similarity(new_ngrams, exist_ngrams)

            exist_shingles = get_word_shingles(existing_transcript, k=2)
            shingle_sim = compute_jaccard_similarity(new_shingles, exist_shingles)

            exist_words = set(existing_transcript.split())
            word_sim = compute_jaccard_similarity(new_words, exist_words)

            # Blended multi-granularity lexical similarity
            combined_sim = (ngram_sim * 0.35) + (word_sim * 0.40) + (shingle_sim * 0.25)

            if combined_sim > best_score:
                best_score = combined_sim
                best_match_meta = existing_meta

        if best_score >= self.video_similarity_threshold and best_match_meta:
            # Deterministic tie-breaking: who is canonical?
            is_existing_canonical = is_candidate_more_canonical(
                cand_date=best_match_meta.upload_date,
                cand_channel=best_match_meta.channel_id,
                cand_vid=best_match_meta.video_id,
                target_date=new_video.upload_date,
                target_channel=new_video.channel_id,
                target_vid=new_video.video_id,
            )

            if is_existing_canonical:
                return DedupMatch(
                    is_duplicate=True,
                    similarity_score=round(best_score, 4),
                    canonical_video_id=best_match_meta.video_id,
                    canonical_channel_id=best_match_meta.channel_id,
                    reason=(
                        f"Matched existing video {best_match_meta.video_id} ({best_match_meta.channel_id.value}) "
                        f"with score {best_score:.3f}. Existing video selected as canonical."
                    )
                )
            else:
                return DedupMatch(
                    is_duplicate=False,
                    similarity_score=round(best_score, 4),
                    canonical_video_id=new_video.video_id,
                    canonical_channel_id=new_video.channel_id,
                    reason=(
                        f"Matched existing video {best_match_meta.video_id}, but new video {new_video.video_id} "
                        f"is determined to be earlier/more canonical by tie-breaking rules."
                    )
                )

        return DedupMatch(
            is_duplicate=False,
            similarity_score=round(best_score, 4),
            reason=f"Max similarity {best_score:.3f} below threshold {self.video_similarity_threshold}."
        )

    def check_chunk_duplicate(
        self,
        new_chunk: ChunkRecord,
        existing_chunks: List[ChunkRecord],
        new_video_date: Optional[date] = None,
        existing_video_dates: Optional[Dict[str, Optional[date]]] = None,
    ) -> DedupMatch:
        """
        Compares an individual chunk against existing chunks in the catalog.
        Catches short clip re-cuts where whole-video deduplication does not trigger.
        """
        if not existing_chunks:
            return DedupMatch(is_duplicate=False, similarity_score=0.0, reason="No existing chunks.")

        new_shingles = get_word_shingles(new_chunk.clean_text, k=2)
        new_ngrams = get_character_ngrams(new_chunk.clean_text, n=4)
        new_words = set(new_chunk.clean_text.split())

        best_score = 0.0
        best_chunk: Optional[ChunkRecord] = None

        for cand in existing_chunks:
            # Skip chunks from the exact same video
            if cand.video_id == new_chunk.video_id:
                continue

            cand_shingles = get_word_shingles(cand.clean_text, k=2)
            cand_ngrams = get_character_ngrams(cand.clean_text, n=4)
            cand_words = set(cand.clean_text.split())

            shingle_sim = compute_jaccard_similarity(new_shingles, cand_shingles)
            ngram_sim = compute_jaccard_similarity(new_ngrams, cand_ngrams)
            word_sim = compute_jaccard_similarity(new_words, cand_words)
            score = (shingle_sim * 0.4) + (ngram_sim * 0.3) + (word_sim * 0.3)

            if score > best_score:
                best_score = score
                best_chunk = cand

        if best_score >= self.chunk_similarity_threshold and best_chunk:
            cand_date = None
            if existing_video_dates and best_chunk.video_id in existing_video_dates:
                cand_date = existing_video_dates[best_chunk.video_id]

            cand_is_canonical = is_candidate_more_canonical(
                cand_date=cand_date,
                cand_channel=best_chunk.channel_id,
                cand_vid=best_chunk.video_id,
                target_date=new_video_date,
                target_channel=new_chunk.channel_id,
                target_vid=new_chunk.video_id,
            )

            if cand_is_canonical:
                return DedupMatch(
                    is_duplicate=True,
                    similarity_score=round(best_score, 4),
                    canonical_video_id=best_chunk.video_id,
                    canonical_channel_id=best_chunk.channel_id,
                    matched_chunk_id=best_chunk.id,
                    reason=(
                        f"Chunk matches canonical chunk {best_chunk.id} from {best_chunk.video_id} "
                        f"({best_chunk.channel_id.value}) at score {best_score:.3f}."
                    )
                )

        return DedupMatch(
            is_duplicate=False,
            similarity_score=round(best_score, 4),
            reason=f"Chunk similarity {best_score:.3f} below threshold."
        )

    def attach_cross_channel_alias(
        self,
        canonical_chunk: ChunkRecord,
        duplicate_chunk: ChunkRecord,
        video_title: Optional[str] = None,
    ) -> None:
        """
        Attaches duplicate chunk's channel and timestamp as an alias to the canonical chunk.
        Ensures users can see that this discourse was also broadcast on the duplicate channel.
        """
        alias = CrossChannelAlias(
            channel=duplicate_chunk.channel_id,
            video_id=duplicate_chunk.video_id,
            video_title=video_title,
            timestamp_sec=duplicate_chunk.start_sec,
            timestamp_formatted=duplicate_chunk.start_formatted,
        )

        # Avoid duplicates in alias list
        if not any(a.video_id == alias.video_id and a.timestamp_sec == alias.timestamp_sec for a in canonical_chunk.cross_channel_aliases):
            canonical_chunk.cross_channel_aliases.append(alias)
