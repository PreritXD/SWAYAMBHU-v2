"""
SWAYAMBHU v2 - Continuous Scheduled Ingestion Worker (Cron Compatible)

Periodically polls Bhajan Marg (@BhajanMarg) and Sadhan Path (@sadhanpath)
for new satsang uploads published since the last sync. Ingests only new videos,
runs deduplication, and records sync status into the sync_status table.
"""

from datetime import datetime, UTC
import json
import logging
import os

from config import SUPPORTED_CHANNELS, settings
from ingest import MultiChannelIngestionPipeline
from schema import SourceChannel, VideoMetadata

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("swayambhu.sync_new_videos")

LOCAL_SYNC_STATE_FILE = "./data/sync_state.json"


def load_local_sync_state() -> dict[str, str]:
    """Loads timestamps of last sync per channel from local disk."""
    if os.path.exists(LOCAL_SYNC_STATE_FILE):
        try:
            with open(LOCAL_SYNC_STATE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_local_sync_state(state: dict[str, str]):
    """Saves timestamps of last sync per channel to local disk."""
    os.makedirs(os.path.dirname(LOCAL_SYNC_STATE_FILE), exist_ok=True)
    with open(LOCAL_SYNC_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def get_last_synced_at(channel_key: str) -> datetime | None:
    """Fetches last_synced_at from Supabase or local state file."""
    if settings.supabase_url and settings.supabase_service_role_key:
        try:
            from supabase import create_client
            client = create_client(settings.supabase_url, settings.supabase_service_role_key)
            resp = client.table("channels").select("last_synced_at").eq("id", channel_key).single().execute()
            if resp.data and resp.data.get("last_synced_at"):
                return datetime.fromisoformat(resp.data["last_synced_at"])
        except Exception as e:
            logger.debug(f"Could not read last_synced_at from DB: {e}")

    state = load_local_sync_state()
    raw = state.get(channel_key)
    return datetime.fromisoformat(raw) if raw else None


def update_sync_record(channel_key: str, status: str, videos_found: int, videos_ingested: int, error: str | None = None):
    """Updates sync status in Supabase or local state."""
    now_iso = datetime.now(UTC).isoformat()

    if settings.supabase_url and settings.supabase_service_role_key:
        try:
            from supabase import create_client
            client = create_client(settings.supabase_url, settings.supabase_service_role_key)
            client.table("channels").update({"last_synced_at": now_iso}).eq("id", channel_key).execute()
            client.table("sync_status").insert({
                "channel_id": channel_key,
                "last_sync_started_at": now_iso,
                "last_sync_completed_at": now_iso,
                "videos_found": videos_found,
                "videos_ingested": videos_ingested,
                "status": status,
                "error_message": error,
            }).execute()
        except Exception as e:
            logger.debug(f"Could not log sync_status to DB: {e}")

    state = load_local_sync_state()
    state[channel_key] = now_iso
    save_local_sync_state(state)


def run_sync():
    """Polls both channels and ingests any new videos."""
    logger.info("Starting scheduled Satsang sync for all supported channels...")
    pipeline = MultiChannelIngestionPipeline()

    for channel_key, config in SUPPORTED_CHANNELS.items():
        logger.info(f"Checking {config.title} ({config.handles[0]})...")
        last_sync = get_last_synced_at(channel_key)

        try:
            # Check latest 15 videos
            discovered = pipeline.fetch_channel_video_list(config.handles[0], max_videos=15)
            new_videos = []

            for vid in discovered:
                upload_d = vid.get("upload_date")
                # If we have a last sync date, only take videos uploaded on/after that date
                if last_sync and upload_d and datetime.combine(upload_d, datetime.min.time(), tzinfo=UTC) < last_sync:
                    continue
                new_videos.append(vid)

            logger.info(f"Found {len(new_videos)} new video(s) for {channel_key}.")
            ingested_count = 0

            for v in new_videos:
                meta = VideoMetadata(
                    video_id=v["video_id"],
                    channel_id=SourceChannel(channel_key),
                    title=v["title"],
                    url=v["url"],
                    upload_date=v["upload_date"],
                    duration_seconds=v["duration_seconds"],
                    view_count=v["view_count"],
                )
                segments, full_text, trans_model = pipeline.extract_transcript(meta.video_id)
                if segments:
                    meta.transcription_model = trans_model
                    res = pipeline.process_video(meta, segments, full_text, transcription_model=trans_model)
                    if res["status"] in ("success", "duplicate_video"):
                        ingested_count += 1

            update_sync_record(
                channel_key=channel_key,
                status="completed",
                videos_found=len(new_videos),
                videos_ingested=ingested_count,
            )
            logger.info(f"Sync complete for {channel_key}: {ingested_count}/{len(new_videos)} ingested.")

        except Exception as e:
            logger.error(f"Sync failed for {channel_key}: {e}", exc_info=True)
            update_sync_record(
                channel_key=channel_key,
                status="failed",
                videos_found=0,
                videos_ingested=0,
                error=str(e),
            )


if __name__ == "__main__":
    run_sync()
