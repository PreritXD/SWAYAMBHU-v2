"""
SWAYAMBHU v2 - Multi-Channel Video & Transcript Ingestion Pipeline

Discovers discourses from Bhajan Marg (@BhajanMarg) and Sadhan Path (@sadhanpath),
extracts captions via youtube-transcript-api with Whisper fallbacks,
applies 2-tier cross-channel deduplication, chunks with sliding-window timestamps,
and embeds into the vector store.
"""

import argparse
from datetime import datetime, date
import logging
import os
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Optional, Tuple

from config import SUPPORTED_CHANNELS, settings
from chunking import SemanticSlidingWindowChunker
from dedup import CrossChannelDeduplicator
from indexer import EmbeddingGenerator, get_vector_store
from schema import ChunkRecord, SourceChannel, TranscriptSegment, VideoMetadata

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("swayambhu.ingest")


class MultiChannelIngestionPipeline:
    """Orchestrates channel discovery, transcription, deduplication, and vector indexing."""

    def __init__(self):
        self.chunker = SemanticSlidingWindowChunker()
        self.deduplicator = CrossChannelDeduplicator(
            video_similarity_threshold=settings.dedup_video_threshold,
            chunk_similarity_threshold=settings.dedup_chunk_threshold,
        )
        self.embedding_gen = EmbeddingGenerator()
        self.vector_store = get_vector_store()
        # In-memory catalogs for deduplication (hydrated from DB or local store)
        self.video_catalog: List[Tuple[VideoMetadata, str]] = []
        self.chunk_catalog: List[ChunkRecord] = []
        self.video_dates: Dict[str, Optional[date]] = {}

    def discover_channel_playlists(
        self,
        channel_handle: str,
        max_playlists: int = 150,
    ) -> List[Dict[str, str]]:
        """Discovers public playlists on a channel."""
        logger.info(f"Discovering playlists on channel {channel_handle}...")
        channel_url = f"https://www.youtube.com/{channel_handle}/playlists"
        cmd = [
            "yt-dlp",
            "--flat-playlist",
            "--print", "%(id)s\t%(title)s",
            "--playlist-end", str(max_playlists),
            channel_url
        ]
        playlists = []
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
            for line in result.stdout.strip().split("\n"):
                if not line or "\t" not in line:
                    continue
                parts = line.split("\t")
                p_id = parts[0].strip()
                p_title = parts[1].strip() if len(parts) > 1 else "Unknown Playlist"
                playlists.append({
                    "id": p_id,
                    "title": p_title,
                    "url": f"https://www.youtube.com/playlist?list={p_id}"
                })
        except Exception as e:
            logger.warning(f"yt-dlp playlist discovery failed for {channel_handle}: {e}")
        return playlists

    def fetch_video_list(
        self,
        target_url: str,
        label: str,
        max_videos: int = 50,
        start_index: int = 1,
    ) -> List[Dict[str, Any]]:
        """Discovers videos from a URL (channel or playlist) using yt-dlp flat extraction."""
        logger.info(f"Scanning {label} (from #{start_index} up to #{start_index + max_videos - 1})...")
        cmd = [
            "yt-dlp",
            "--flat-playlist",
            "--print", "%(id)s\t%(title)s\t%(upload_date)s\t%(duration)s\t%(view_count)s",
            "--playlist-start", str(start_index),
            "--playlist-end", str(start_index + max_videos - 1),
            target_url
        ]

        videos: List[Dict[str, Any]] = []
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
            for line in result.stdout.strip().split("\n"):
                if not line or "\t" not in line:
                    continue
                parts = line.split("\t")
                vid_id = parts[0]
                title = parts[1] if len(parts) > 1 else "Unknown"
                raw_date = parts[2] if len(parts) > 2 and parts[2] != "NA" else None
                duration_str = parts[3] if len(parts) > 3 and parts[3] != "NA" else "0"
                view_str = parts[4] if len(parts) > 4 and parts[4] != "NA" else "0"

                upload_d = None
                if raw_date and len(raw_date) == 8:
                    try:
                        upload_d = datetime.strptime(raw_date, "%Y%m%d").date()
                    except ValueError:
                        pass

                videos.append({
                    "video_id": vid_id,
                    "title": title,
                    "url": f"https://www.youtube.com/watch?v={vid_id}",
                    "upload_date": upload_d,
                    "duration_seconds": int(float(duration_str)) if duration_str.replace('.', '', 1).isdigit() else 0,
                    "view_count": int(view_str) if view_str.isdigit() else 0,
                })
        except Exception as e:
            logger.warning(f"yt-dlp discovery failed for {label}: {e}")

        logger.info(f"Discovered {len(videos)} videos from {label}.")
        return videos

    def fetch_channel_video_list(
        self,
        channel_handle: str,
        max_videos: int = 50,
        start_index: int = 1,
    ) -> List[Dict[str, Any]]:
        """Discovers videos using yt-dlp flat extraction on channel's main uploads feed."""
        channel_url = f"https://www.youtube.com/{channel_handle}/videos"
        return self.fetch_video_list(
            target_url=channel_url,
            label=f"channel {channel_handle}",
            max_videos=max_videos,
            start_index=start_index,
        )

    def fetch_playlist_video_list(
        self,
        playlist_ref: str,
        max_videos: int = 50,
        start_index: int = 1,
    ) -> List[Dict[str, Any]]:
        """Discovers videos using yt-dlp flat extraction from a specific playlist."""
        playlist_url = playlist_ref if playlist_ref.startswith("http") else f"https://www.youtube.com/playlist?list={playlist_ref}"
        return self.fetch_video_list(
            target_url=playlist_url,
            label=f"playlist {playlist_ref}",
            max_videos=max_videos,
            start_index=start_index,
        )

    def extract_transcript(self, video_id: str) -> Tuple[List[TranscriptSegment], str, str]:
        """
        Extracts transcript using strict 5-tier fallback chain:
        1. youtube-transcript-api (Priority 1: free, instant, perfect timestamps -> 'youtube_captions')
        2. Groq Cloud whisper-large-v3 (Priority 2: high accuracy cloud transcription -> 'groq/whisper-large-v3')
        3. Groq Cloud whisper-large-v3-turbo (Priority 3: fallback if large-v3 rate limited -> 'groq/whisper-large-v3-turbo')
        4. Local faster-whisper large-v3 (Priority 4: GPU acceleration, e.g. Colab -> 'faster-whisper/large-v3')
        5. Local faster-whisper medium (Priority 5: CPU fallback if no GPU -> 'faster-whisper/medium')
           (Note: faster-whisper small is excluded from production/ingestion paths; only permitted if WHISPER_DEV_MODE=true)

        Returns (segments, full_text, transcription_model).
        """
        # Tier 1: YouTube Captions API (Instant, zero compute, perfect timestamps)
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            if hasattr(YouTubeTranscriptApi, "get_transcript"):
                raw_items = YouTubeTranscriptApi.get_transcript(video_id, languages=['hi', 'hi-Latn', 'en'])
            else:
                api = YouTubeTranscriptApi()
                fetched = api.fetch(video_id, languages=['hi', 'hi-Latn', 'en'])
                raw_items = [{"text": s.text, "start": s.start, "duration": s.duration} for s in fetched]

            segments = [
                TranscriptSegment(
                    text=item["text"],
                    start=float(item["start"]),
                    duration=float(item["duration"]),
                    end=float(item["start"]) + float(item["duration"])
                )
                for item in raw_items
            ]
            full_text = " ".join(s.text for s in segments)
            logger.info(f"Retrieved captions via YouTube Captions API for {video_id}")
            return segments, full_text, "youtube_captions"
        except Exception as e:
            logger.debug(f"youtube-transcript-api missed for {video_id}: {e}")

        # Download audio for subsequent speech-to-text tiers
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = os.path.join(tmpdir, f"{video_id}.mp3")
            downloaded = self._download_audio(video_id, audio_path)
            if not downloaded:
                logger.warning(f"Could not download audio for {video_id} to perform speech-to-text.")
                return [], "", "none"

            # Tier 2: Groq Cloud whisper-large-v3 (High accuracy cloud transcription)
            if settings.groq_api_key:
                try:
                    segments, full_text = self._transcribe_with_groq(
                        audio_path=audio_path,
                        model=settings.whisper_cloud_primary
                    )
                    if segments:
                        model_tag = f"groq/{settings.whisper_cloud_primary}"
                        logger.info(f"Transcribed {video_id} via {model_tag}")
                        return segments, full_text, model_tag
                except Exception as e:
                    logger.warning(f"Groq {settings.whisper_cloud_primary} failed for {video_id}: {e}. Trying turbo fallback.")

                # Tier 3: Groq Cloud whisper-large-v3-turbo (Fallback if rate limits hit)
                try:
                    segments, full_text = self._transcribe_with_groq(
                        audio_path=audio_path,
                        model=settings.whisper_cloud_fallback
                    )
                    if segments:
                        model_tag = f"groq/{settings.whisper_cloud_fallback}"
                        logger.info(f"Transcribed {video_id} via {model_tag}")
                        return segments, full_text, model_tag
                except Exception as e:
                    logger.warning(f"Groq {settings.whisper_cloud_fallback} fallback failed for {video_id}: {e}")

            # Tier 4 (GPU: large-v3) & Tier 5 (CPU: medium): Local faster-whisper
            return self._transcribe_with_faster_whisper(audio_path=audio_path, video_id=video_id)

    def _download_audio(self, video_id: str, output_path: str) -> bool:
        """
        Downloads speech-optimized audio (mono, 16kHz, 32kbps) using yt-dlp.
        Reduces 1-hour files from ~60MB down to ~14MB so they easily fit inside
        Groq Whisper's 25MB ceiling without any loss in transcription accuracy.
        """
        cmd = [
            "yt-dlp",
            "--extractor-args", "youtube:player_client=android",
            "-x", "--audio-format", "mp3",
            "--audio-quality", "32K",
            "--postprocessor-args", "ffmpeg:-ac 1 -ar 16000",
            "-o", output_path,
            f"https://www.youtube.com/watch?v={video_id}"
        ]
        try:
            subprocess.run(cmd, capture_output=True, timeout=180, check=True)
            return os.path.exists(output_path)
        except Exception as e:
            logger.debug(f"yt-dlp audio download failed for {video_id}: {e}")
            return False

    def _transcribe_with_groq(self, audio_path: str, model: str) -> Tuple[List[TranscriptSegment], str]:
        """Transcribes audio using Groq Cloud free-tier Whisper endpoint."""
        from groq import Groq
        groq_client = Groq(api_key=settings.groq_api_key)
        filename = os.path.basename(audio_path)

        with open(audio_path, "rb") as f:
            transcription = groq_client.audio.transcriptions.create(
                file=(filename, f.read()),
                model=model,
                response_format="verbose_json",
                language="hi"
            )

        segments = []
        raw_segments = getattr(transcription, "segments", [])
        for seg in raw_segments:
            segments.append(
                TranscriptSegment(
                    text=seg.get("text", "").strip(),
                    start=float(seg.get("start", 0)),
                    duration=float(seg.get("end", 0)) - float(seg.get("start", 0)),
                    end=float(seg.get("end", 0))
                )
            )
        full_text = getattr(transcription, "text", "")
        return segments, full_text

    def _transcribe_with_faster_whisper(self, audio_path: str, video_id: str) -> Tuple[List[TranscriptSegment], str, str]:
        """
        Local faster-whisper transcription:
        - Tier 4: GPU detected -> large-v3 ('faster-whisper/large-v3')
        - Tier 5: CPU fallback -> medium ('faster-whisper/medium')
        - Dev Mode: Only if whisper_dev_mode=True -> small ('faster-whisper/small-dev')
        """
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            logger.warning("faster-whisper is not installed. Skipping local transcription fallback.")
            return [], "", "none"

        has_gpu = False
        try:
            import torch
            has_gpu = torch.cuda.is_available()
        except ImportError:
            pass

        if has_gpu:
            model_name = settings.local_whisper_gpu_model  # "large-v3"
            device = "cuda"
            compute_type = "float16"
            model_tag = f"faster-whisper/{model_name}"
        else:
            if settings.whisper_dev_mode:
                model_name = "small"
                model_tag = "faster-whisper/small-dev"
            else:
                model_name = settings.local_whisper_cpu_model  # "medium"
                model_tag = f"faster-whisper/{model_name}"
            device = "cpu"
            compute_type = "int8"

        logger.info(f"Running local faster-whisper ({model_tag}) on {device} ({compute_type})...")
        try:
            model = WhisperModel(model_name, device=device, compute_type=compute_type)
            segments_gen, _ = model.transcribe(audio_path, language="hi", beam_size=5)
            segments = []
            for s in segments_gen:
                segments.append(
                    TranscriptSegment(
                        text=s.text.strip(),
                        start=float(s.start),
                        duration=float(s.end - s.start),
                        end=float(s.end)
                    )
                )
            full_text = " ".join(s.text for s in segments)
            return segments, full_text, model_tag
        except Exception as e:
            logger.error(f"Local faster-whisper failed for {video_id}: {e}")
            return [], "", "none"

    def process_video(
        self,
        video_meta: VideoMetadata,
        segments: List[TranscriptSegment],
        full_transcript: str,
        transcription_model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes deduplication, chunking, embedding, and indexing for a single video.
        """
        if transcription_model:
            video_meta.transcription_model = transcription_model

        logger.info(f"Processing {video_meta.video_id} [{video_meta.channel_id.value}]: '{video_meta.title[:45]}...'")

        # 1. Whole-Video Deduplication Check
        video_dedup_match = self.deduplicator.check_video_duplicate(
            new_video=video_meta,
            new_transcript=full_transcript,
            catalog_videos=self.video_catalog,
        )

        if video_dedup_match.is_duplicate:
            video_meta.is_duplicate = True
            video_meta.canonical_video_id = video_dedup_match.canonical_video_id
            video_meta.dedup_similarity_score = video_dedup_match.similarity_score
            logger.info(
                f"⏩ [DEDUP] Video {video_meta.video_id} is a duplicate of {video_dedup_match.canonical_video_id} "
                f"({video_dedup_match.canonical_channel_id}). Score: {video_dedup_match.similarity_score}"
            )
            # Store metadata for catalog reference but skip indexing duplicate chunks
            self.video_catalog.append((video_meta, full_transcript))
            return {
                "status": "duplicate_video",
                "video_id": video_meta.video_id,
                "canonical_video_id": video_dedup_match.canonical_video_id,
                "score": video_dedup_match.similarity_score,
                "chunks_indexed": 0,
            }

        # 2. Chunking with Sliding Window & Hindi Normalization
        chunks = self.chunker.chunk_segments(
            segments=segments,
            video_id=video_meta.video_id,
            channel_id=video_meta.channel_id,
        )

        # 3. Chunk-Level Deduplication Check (catches re-cuts and partial overlap)
        active_chunks: List[ChunkRecord] = []
        for chunk in chunks:
            chunk_dedup_match = self.deduplicator.check_chunk_duplicate(
                new_chunk=chunk,
                existing_chunks=self.chunk_catalog,
                new_video_date=video_meta.upload_date,
                existing_video_dates=self.video_dates,
            )

            if chunk_dedup_match.is_duplicate:
                chunk.is_duplicate = True
                chunk.canonical_chunk_id = chunk_dedup_match.matched_chunk_id
                chunk.canonical_video_id = chunk_dedup_match.canonical_video_id
                # Attach alias to existing canonical chunk
                for existing in self.chunk_catalog:
                    if existing.id == chunk_dedup_match.matched_chunk_id:
                        self.deduplicator.attach_cross_channel_alias(
                            canonical_chunk=existing,
                            duplicate_chunk=chunk,
                            video_title=video_meta.title,
                        )
                        break
            else:
                active_chunks.append(chunk)

            self.chunk_catalog.append(chunk)

        # 4. Generate Embeddings for Active Non-Duplicate Chunks
        if active_chunks:
            texts_to_embed = [c.clean_text for c in active_chunks]
            embeddings = self.embedding_gen.embed_texts(texts_to_embed)
            for c, emb in zip(active_chunks, embeddings):
                c.embedding = emb

            # 5. Insert into Vector Store
            self.vector_store.insert_chunks(active_chunks)

        # Update local catalogs
        self.video_catalog.append((video_meta, full_transcript))
        self.video_dates[video_meta.video_id] = video_meta.upload_date

        logger.info(
            f"✅ Ingested {video_meta.video_id}: {len(chunks)} total chunks, "
            f"{len(active_chunks)} indexed, {len(chunks) - len(active_chunks)} duplicate clips suppressed."
        )

        return {
            "status": "success",
            "video_id": video_meta.video_id,
            "total_chunks": len(chunks),
            "chunks_indexed": len(active_chunks),
            "duplicate_chunks": len(chunks) - len(active_chunks),
        }

    def get_existing_video_ids(self) -> set:
        """Returns a set of video_ids already stored in the database to prevent duplicate work."""
        if hasattr(self.vector_store, "client"):
            try:
                res = self.vector_store.client.table("videos").select("video_id").execute()
                return {r["video_id"] for r in (res.data or []) if "video_id" in r}
            except Exception as e:
                logger.debug(f"Could not query existing videos from Supabase: {e}")
        elif hasattr(self.vector_store, "_collection"):
            try:
                res = self.vector_store._collection.get(include=["metadatas"])
                return {m["video_id"] for m in (res.get("metadatas") or []) if m and "video_id" in m}
            except Exception as e:
                logger.debug(f"Could not query existing videos from Chroma: {e}")
        return set()

    def ingest_channel(
        self,
        channel_key: str,
        max_videos: int = 10,
        playlist: Optional[str] = None,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Ingests new videos from a specific channel handle or playlist.
        Automatically checks the database and jumps past already-ingested videos.
        """
        if channel_key not in SUPPORTED_CHANNELS:
            raise ValueError(f"Unknown channel: {channel_key}. Must be one of {list(SUPPORTED_CHANNELS.keys())}")

        cfg = SUPPORTED_CHANNELS[channel_key]
        ch_enum = SourceChannel(channel_key)

        existing_ids = set() if force else self.get_existing_video_ids()
        if existing_ids:
            logger.info(f"Database currently contains {len(existing_ids)} indexed videos. Skipping already processed discourses.")

        # Resolve playlist if specified
        target_playlist_ref = None
        if playlist:
            p_clean = playlist.strip().lower()
            if p_clean == "all":
                playlists = self.discover_channel_playlists(cfg.handles[0], max_playlists=150)
                logger.info(f"📁 [ALL PLAYLISTS] Discovered {len(playlists)} playlists on channel {channel_key}.")
                results = []
                for p_idx, pl in enumerate(playlists, 1):
                    if max_videos > 0 and len(results) >= max_videos:
                        logger.info(f"Reached target of {max_videos} new videos across playlists.")
                        break

                    logger.info(f"\n📁 [PLAYLIST {p_idx}/{len(playlists)}] Ingesting from: '{pl['title']}' ({pl['id']})")
                    start_index = 1
                    while True:
                        if max_videos > 0 and len(results) >= max_videos:
                            break
                        discovered = self.fetch_playlist_video_list(
                            playlist_ref=pl["id"],
                            max_videos=25,
                            start_index=start_index,
                        )
                        if not discovered:
                            break

                        for v in discovered:
                            if max_videos > 0 and len(results) >= max_videos:
                                break

                            vid_id = v["video_id"]
                            if vid_id in existing_ids and not force:
                                logger.info(f"⏩ [SKIP] Video {vid_id} ('{v['title'][:40]}...') already indexed. Jumping to next video.")
                                continue

                            meta = VideoMetadata(
                                video_id=v["video_id"],
                                channel_id=ch_enum,
                                title=v["title"],
                                url=v["url"],
                                upload_date=v["upload_date"],
                                duration_seconds=v["duration_seconds"],
                                view_count=v["view_count"],
                            )
                            segments, full_text, trans_model = self.extract_transcript(meta.video_id)
                            if not segments:
                                logger.warning(f"No transcript available for {meta.video_id}; skipping.")
                                continue

                            meta.transcription_model = trans_model
                            res = self.process_video(meta, segments, full_text, transcription_model=trans_model)
                            results.append(res)
                            existing_ids.add(vid_id)

                        start_index += len(discovered)

                return {
                    "channel": channel_key,
                    "videos_scanned": "all_playlists",
                    "videos_processed": len(results),
                    "details": results,
                }
            elif p_clean == "first":
                playlists = self.discover_channel_playlists(cfg.handles[0], max_playlists=3)
                if playlists:
                    target_playlist_ref = playlists[0]["id"]
                    logger.info(f"📁 [PLAYLIST] Selected first playlist on {channel_key}: '{playlists[0]['title']}' (ID: {target_playlist_ref})")
                else:
                    logger.warning(f"No playlists found on channel {channel_key}. Falling back to main channel feed.")
            else:
                target_playlist_ref = playlist.strip()
                logger.info(f"📁 [PLAYLIST] Ingesting from specified playlist: {target_playlist_ref}")

        existing_ids = set() if force else self.get_existing_video_ids()
        if existing_ids:
            logger.info(f"Database currently contains {len(existing_ids)} indexed videos. Skipping already processed discourses.")

        results = []
        batch_size = max(10, (max_videos * 2) if max_videos > 0 else 50)
        start_index = 1
        max_scan_limit = 5000  # Safety threshold to avoid scanning indefinitely

        while (max_videos <= 0 or len(results) < max_videos) and start_index <= max_scan_limit:
            if target_playlist_ref:
                discovered = self.fetch_playlist_video_list(
                    playlist_ref=target_playlist_ref,
                    max_videos=batch_size,
                    start_index=start_index,
                )
            else:
                discovered = self.fetch_channel_video_list(
                    channel_handle=cfg.handles[0],
                    max_videos=batch_size,
                    start_index=start_index,
                )
            if not discovered:
                logger.info("No more videos found.")
                break

            for v in discovered:
                if max_videos > 0 and len(results) >= max_videos:
                    break

                vid_id = v["video_id"]
                if vid_id in existing_ids and not force:
                    logger.info(f"⏩ [SKIP] Video {vid_id} ('{v['title'][:40]}...') already indexed. Jumping to next video.")
                    continue

                meta = VideoMetadata(
                    video_id=v["video_id"],
                    channel_id=ch_enum,
                    title=v["title"],
                    url=v["url"],
                    upload_date=v["upload_date"],
                    duration_seconds=v["duration_seconds"],
                    view_count=v["view_count"],
                )
                segments, full_text, trans_model = self.extract_transcript(meta.video_id)
                if not segments:
                    logger.warning(f"No transcript available for {meta.video_id}; skipping.")
                    continue

                meta.transcription_model = trans_model
                res = self.process_video(meta, segments, full_text, transcription_model=trans_model)
                results.append(res)
                existing_ids.add(vid_id)

            start_index += len(discovered)

        return {
            "channel": channel_key,
            "videos_scanned": start_index - 1,
            "videos_processed": len(results),
            "details": results,
        }

    def ingest_channels_round_robin(
        self,
        channels: List[str],
        max_videos_per_channel: int = 0,
        batch_size: int = 10,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Ingests videos from multiple channels in an interleaved round-robin fashion.
        Prevents any single large channel (e.g. Bhajan Marg) from monopolizing the
        pipeline and starving the other channels (Sadhan Path, Vrindavan Ras, Shri Hit Radha Kripa).
        """
        existing_ids = set() if force else self.get_existing_video_ids()
        if existing_ids:
            logger.info(f"Database currently contains {len(existing_ids)} indexed videos. Skipping already processed discourses.")

        channel_states = {}
        for ch in channels:
            cfg = SUPPORTED_CHANNELS[ch]
            channel_states[ch] = {
                "config": cfg,
                "enum": SourceChannel(ch),
                "start_index": 1,
                "processed_count": 0,
                "exhausted": False,
            }

        round_num = 1

        while any(not state["exhausted"] for state in channel_states.values()):
            logger.info(f"\n🔄 ===== ROUND {round_num} (Interleaved Channel Ingestion) =====")
            active_in_round = 0

            for ch in channels:
                state = channel_states[ch]
                if state["exhausted"]:
                    continue

                if max_videos_per_channel > 0 and state["processed_count"] >= max_videos_per_channel:
                    state["exhausted"] = True
                    logger.info(f"🏁 [{state['config'].title}] Reached target limit of {max_videos_per_channel} videos.")
                    continue

                cfg = state["config"]
                ch_enum = state["enum"]
                logger.info(f"\n📺 [{cfg.title}] Ingesting next batch (Scanning from #{state['start_index']})...")

                discovered = self.fetch_channel_video_list(
                    channel_handle=cfg.handles[0],
                    max_videos=batch_size,
                    start_index=state["start_index"],
                )

                if not discovered:
                    logger.info(f"🏁 [{cfg.title}] No more videos found on channel.")
                    state["exhausted"] = True
                    continue

                active_in_round += 1
                batch_processed = 0

                for v in discovered:
                    if max_videos_per_channel > 0 and state["processed_count"] >= max_videos_per_channel:
                        state["exhausted"] = True
                        break

                    vid_id = v["video_id"]
                    if vid_id in existing_ids and not force:
                        logger.info(f"⏩ [SKIP] Video {vid_id} ('{v['title'][:40]}...') already indexed.")
                        continue

                    meta = VideoMetadata(
                        video_id=v["video_id"],
                        channel_id=ch_enum,
                        title=v["title"],
                        url=v["url"],
                        upload_date=v["upload_date"],
                        duration_seconds=v["duration_seconds"],
                        view_count=v["view_count"],
                    )
                    segments, full_text, trans_model = self.extract_transcript(meta.video_id)
                    if not segments:
                        logger.warning(f"No transcript available for {meta.video_id}; skipping.")
                        continue

                    meta.transcription_model = trans_model
                    self.process_video(meta, segments, full_text, transcription_model=trans_model)
                    existing_ids.add(vid_id)
                    state["processed_count"] += 1
                    batch_processed += 1

                state["start_index"] += len(discovered)
                logger.info(f"✅ [{cfg.title}] Batch complete: {batch_processed} new videos indexed (Channel Total: {state['processed_count']})")

            if active_in_round == 0:
                break
            round_num += 1

        summary = {ch: state["processed_count"] for ch, state in channel_states.items()}
        logger.info(f"\n🎉 Multi-Channel Ingestion Finished! Summary: {summary}")
        return summary


def main():
    parser = argparse.ArgumentParser(description="SWAYAMBHU v2 - Satsang Ingestion Pipeline")
    parser.add_argument("--channel", type=str, default="all", help=f"Target channel ({', '.join(SUPPORTED_CHANNELS.keys())}, 'all', or comma-separated list)")
    parser.add_argument("--max-videos", type=int, default=5, help="Max new videos to process per channel (0 for unlimited)")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size per channel during round-robin ingestion (default: 10)")
    parser.add_argument("--playlist", type=str, default=None, help="Target playlist ('all' for all playlists, 'first' for 1st playlist, or a playlist ID/URL)")
    parser.add_argument("--video-id", type=str, default=None, help="Ingest a specific single YouTube video ID")
    parser.add_argument("--force", action="store_true", help="Force re-ingestion of already processed videos")
    parser.add_argument("--sequential", action="store_true", help="Run channels strictly one after another instead of round-robin")
    args = parser.parse_args()

    pipeline = MultiChannelIngestionPipeline()

    if args.video_id:
        raw_id = args.video_id.strip()
        # Extract 11-char YouTube ID if a full URL was provided
        match = re.search(r"(?:v=|\/|youtu\.be\/)([0-9A-Za-z_-]{11})", raw_id)
        vid_id = match.group(1) if match else raw_id

        logger.info(f"=== Single Video Ingestion: {vid_id} ===")

        # Fetch actual video metadata from YouTube via yt-dlp
        title = f"Discourse {vid_id}"
        upload_date = None
        duration_seconds = None
        view_count = None
        detected_channel = SourceChannel.BHAJAN_MARG

        # Check if user specified a channel explicitly
        if args.channel and args.channel != "all":
            ch_clean = args.channel.strip().lower()
            if ch_clean in [c.value for c in SourceChannel]:
                detected_channel = SourceChannel(ch_clean)

        try:
            cmd = [
                "yt-dlp",
                "--skip-download",
                "--print", "%(title)s\t%(channel)s\t%(upload_date)s\t%(duration)s\t%(view_count)s",
                f"https://www.youtube.com/watch?v={vid_id}"
            ]
            yt_res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
            line = yt_res.stdout.strip()
            if line and "\t" in line:
                parts = line.split("\t")
                if len(parts) > 0 and parts[0]:
                    title = parts[0]
                if len(parts) > 1 and parts[1] and (not args.channel or args.channel == "all"):
                    ch_name = parts[1].lower()
                    if "sadhan" in ch_name:
                        detected_channel = SourceChannel.SADHAN_PATH
                    elif "ras" in ch_name:
                        detected_channel = SourceChannel.VRINDAVAN_RAS
                    elif "radha kripa" in ch_name:
                        detected_channel = SourceChannel.SHRI_HIT_RADHA_KRIPA
                    elif "bhajan" in ch_name:
                        detected_channel = SourceChannel.BHAJAN_MARG
                if len(parts) > 2 and parts[2] and parts[2] != "NA" and len(parts[2]) == 8:
                    try:
                        upload_date = datetime.strptime(parts[2], "%Y%m%d").date()
                    except Exception:
                        pass
                if len(parts) > 3 and parts[3] and parts[3] != "NA":
                    try:
                        duration_seconds = int(parts[3])
                    except Exception:
                        pass
                if len(parts) > 4 and parts[4] and parts[4] != "NA":
                    try:
                        view_count = int(parts[4])
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"Could not fetch full metadata via yt-dlp: {e}. Using fallback defaults.")

        logger.info(f"Video Title: {title}")
        logger.info(f"Channel: {detected_channel.value}")

        segments, full_text, trans_model = pipeline.extract_transcript(vid_id)
        if not segments:
            logger.error(f"❌ Failed to extract transcript for video {vid_id}.")
            return

        meta = VideoMetadata(
            video_id=vid_id,
            channel_id=detected_channel,
            title=title,
            url=f"https://www.youtube.com/watch?v={vid_id}",
            upload_date=upload_date,
            duration_seconds=duration_seconds,
            view_count=view_count,
            transcription_model=trans_model,
        )
        res = pipeline.process_video(meta, segments, full_text, transcription_model=trans_model)
        logger.info(f"🎉 Ingestion complete for {vid_id}: {res}")
        return

    # Parse channel input (supports 'all', single channel, or comma-separated e.g. 'sadhan_path,vrindavan_ras')
    raw_channels = [c.strip().lower() for c in args.channel.split(",") if c.strip()]
    if "all" in raw_channels:
        target_channels = list(SUPPORTED_CHANNELS.keys())
    else:
        target_channels = [c for c in raw_channels if c in SUPPORTED_CHANNELS]
        invalid = [c for c in raw_channels if c not in SUPPORTED_CHANNELS]
        if invalid:
            logger.warning(f"Ignoring unrecognized channel(s): {invalid}. Valid options: {list(SUPPORTED_CHANNELS.keys())}")
        if not target_channels:
            raise ValueError(f"No valid channels specified in '{args.channel}'. Must be one of {list(SUPPORTED_CHANNELS.keys())} or 'all'.")

    # If multiple channels and not forced sequential, run round-robin
    if len(target_channels) > 1 and not args.sequential and not args.playlist:
        logger.info(f"=== Starting Round-Robin Ingestion across {len(target_channels)} channels: {target_channels} ===")
        pipeline.ingest_channels_round_robin(
            channels=target_channels,
            max_videos_per_channel=args.max_videos,
            batch_size=args.batch_size,
            force=args.force
        )
    else:
        for ch in target_channels:
            logger.info(f"=== Starting Ingestion for {ch} ===")
            res = pipeline.ingest_channel(ch, max_videos=args.max_videos, playlist=args.playlist, force=args.force)
            logger.info(f"Finished {ch}: {res['videos_processed']} new videos processed.")


if __name__ == "__main__":
    main()
