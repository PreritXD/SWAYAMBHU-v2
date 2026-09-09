"""
SWAYAMBHU v2 - Supabase Batch Ingestion & Database Initializer

Connects to Supabase PostgreSQL, creates/verifies tables, and performs
bulk upserting of videos, transcript chunks, and vector embeddings.
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

from config import AppEnvironment, settings
from schema import ChunkRecord, SourceChannel, VideoMetadata

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("swayambhu.supabase_ingest")


class SupabaseIngestor:
    """Manages bulk database operations and schema verification on Supabase."""

    def __init__(self):
        if not settings.supabase_url or not (settings.supabase_service_role_key or settings.supabase_key):
            if settings.app_env in (AppEnvironment.PRODUCTION, AppEnvironment.STAGING):
                raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are strictly required in production.")
            logger.warning("Supabase credentials missing. Ingestion client cannot initialize remote DB.")
            self.client = None
            return

        from supabase import create_client, Client
        key = settings.supabase_service_role_key or settings.supabase_key
        self.client: Client = create_client(settings.supabase_url, key)

    def test_connection(self) -> bool:
        """Verifies connection to Supabase."""
        if not self.client:
            return False
        try:
            resp = self.client.table("channels").select("id").limit(1).execute()
            logger.info("Successfully connected to Supabase PostgreSQL.")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            return False

    def upsert_video(self, video: VideoMetadata) -> bool:
        """Upserts a single video record."""
        if not self.client:
            return False
        data = {
            "video_id": video.video_id,
            "channel_id": video.channel_id.value,
            "title": video.title,
            "url": video.url,
            "upload_date": str(video.upload_date) if video.upload_date else None,
            "duration_seconds": video.duration_seconds,
            "view_count": video.view_count,
            "description": video.description,
            "transcript_language": video.transcript_language,
            "transcription_model": video.transcription_model,
            "is_duplicate": video.is_duplicate,
            "canonical_video_id": video.canonical_video_id,
            "dedup_similarity_score": video.dedup_similarity_score,
        }
        try:
            self.client.table("videos").upsert(data).execute()
            return True
        except Exception as e:
            logger.error(f"Error upserting video {video.video_id}: {e}")
            return False

    def bulk_insert_chunks(self, chunks: List[ChunkRecord], batch_size: int = 50) -> int:
        """Inserts transcript chunks with embeddings in batches."""
        if not self.client or not chunks:
            return 0

        records = [
            {
                "id": c.id,
                "video_id": c.video_id,
                "channel_id": c.channel_id.value,
                "chunk_index": c.chunk_index,
                "start_sec": c.start_sec,
                "end_sec": c.end_sec,
                "start_formatted": c.start_formatted,
                "end_formatted": c.end_formatted,
                "raw_text": c.raw_text,
                "clean_text": c.clean_text,
                "token_count": c.token_count,
                "embedding": c.embedding,
                "embedding_model": c.embedding_model or settings.embedding_model_name,
                "is_duplicate": c.is_duplicate,
                "canonical_chunk_id": c.canonical_chunk_id,
                "canonical_video_id": c.canonical_video_id,
                "cross_channel_aliases": [a.model_dump() for a in c.cross_channel_aliases],
            }
            for c in chunks
        ]

        inserted = 0
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            try:
                res = self.client.table("transcript_chunks").upsert(batch).execute()
                inserted += len(res.data or batch)
                logger.info(f"Upserted chunk batch {i} to {i + len(batch)}...")
            except Exception as e:
                logger.error(f"Failed inserting chunk batch {i}: {e}")

        return inserted


def main():
    parser = argparse.ArgumentParser(description="Supabase Direct Ingestion Utility")
    parser.add_argument("--test", action="store_true", help="Test Supabase connection")
    args = parser.parse_args()

    ingestor = SupabaseIngestor()
    if args.test:
        success = ingestor.test_connection()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
