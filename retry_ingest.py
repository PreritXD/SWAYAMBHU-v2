"""
SWAYAMBHU v2 - Retry & Failure Recovery Ingestion Worker

Scans for videos that failed transcription or were interrupted during ingestion.
Retries transcription using the secondary fallback chain with exponential backoff.
"""

import argparse
import logging
import time

from ingest import MultiChannelIngestionPipeline
from schema import SourceChannel, VideoMetadata

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("swayambhu.retry_ingest")


def retry_failed_videos(video_ids: list[str], max_retries: int = 3, base_backoff_sec: float = 2.0):
    """
    Retries ingestion for a list of video IDs with exponential backoff.
    """
    pipeline = MultiChannelIngestionPipeline()
    successful = []
    failed = []

    for vid in video_ids:
        logger.info(f"Retrying video {vid}...")
        attempt = 0
        success = False

        while attempt < max_retries and not success:
            attempt += 1
            try:
                segments, full_text, trans_model = pipeline.extract_transcript(vid)
                if not segments:
                    raise ValueError(f"No transcript obtained for {vid}")

                meta = VideoMetadata(
                    video_id=vid,
                    channel_id=SourceChannel.BHAJAN_MARG,
                    title=f"Discourse (Retry) {vid}",
                    url=f"https://www.youtube.com/watch?v={vid}",
                    transcription_model=trans_model,
                )
                res = pipeline.process_video(meta, segments, full_text, transcription_model=trans_model)
                logger.info(f"✅ Recovery success for {vid} on attempt {attempt}: {res['status']}")
                successful.append(vid)
                success = True
            except Exception as e:
                backoff = base_backoff_sec * (2 ** (attempt - 1))
                logger.warning(f"Attempt {attempt} failed for {vid} ({e}). Backing off for {backoff:.1f}s...")
                time.sleep(backoff)

        if not success:
            logger.error(f"❌ Permanent failure for {vid} after {max_retries} attempts.")
            failed.append(vid)

    logger.info(f"Retry Run Complete: {len(successful)} recovered, {len(failed)} failed permanently.")


def main():
    parser = argparse.ArgumentParser(description="Retry Failed Satsang Ingestions")
    parser.add_argument("--videos", nargs="+", required=True, help="List of video IDs to retry")
    parser.add_argument("--max-retries", type=int, default=3)
    args = parser.parse_args()

    retry_failed_videos(args.videos, max_retries=args.max_retries)


if __name__ == "__main__":
    main()
