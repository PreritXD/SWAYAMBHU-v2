"""
SWAYAMBHU v2 - Google Colab GPU-Accelerated Ingestion Script

Run this script inside a Google Colab notebook with a free GPU (T4 / V100 / A100)
to transcribe large batches of satsangs from Bhajan Marg and Sadhan Path using faster-whisper,
generate 384-dim embeddings via sentence-transformers, and push directly to Supabase.

Instructions for Google Colab:
--------------------------------
1. Select Runtime -> Change runtime type -> T4 GPU.
2. In the first cell, install dependencies:
   !pip install -q yt-dlp youtube-transcript-api faster-whisper sentence-transformers supabase pydantic python-dotenv indic-transliteration
3. Set your Colab Secrets (or environment variables):
   import os
   os.environ["SUPABASE_URL"] = "https://your-project.supabase.co"
   os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "your-service-role-key"
4. Run:
   !python colab_ingest.py --channel bhajan_marg --max-videos 20
"""

import argparse
from datetime import datetime
import logging
import os
import subprocess
import sys
import tempfile
from typing import List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("swayambhu.colab_ingest")


def check_gpu() -> bool:
    try:
        import torch
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            logger.info(f"🚀 CUDA GPU Detected: {device_name}")
            return True
        else:
            logger.warning("⚠️ No GPU detected. Running on CPU (will be slower).")
            return False
    except ImportError:
        logger.warning("Torch not installed.")
        return False


def run_colab_transcription(
    video_id: str,
    whisper_model: str = "large-v3",
    use_gpu: bool = True
) -> tuple[List[dict], str]:
    """
    Downloads audio using yt-dlp and runs faster-whisper on GPU.
    Defaults to large-v3 on GPU for high Hindi accuracy; medium on CPU.
    Excludes small unless WHISPER_DEV_MODE=true.
    Returns (segments, transcription_model).
    """
    from faster_whisper import WhisperModel

    dev_mode = os.environ.get("WHISPER_DEV_MODE", "").lower() in ("true", "1")
    if whisper_model == "small" and not dev_mode:
        promoted = "large-v3" if use_gpu else "medium"
        logger.warning(
            f"⚠️  faster-whisper 'small' is disabled due to high WER on Hindi devotional vocabulary. "
            f"Automatically promoted to '{promoted}'. (Set WHISPER_DEV_MODE=true to override)."
        )
        whisper_model = promoted

    device = "cuda" if use_gpu else "cpu"
    compute_type = "float16" if use_gpu else "int8"
    model_tag = f"faster-whisper/{whisper_model}"

    logger.info(f"Loading faster-whisper ({model_tag}) on {device} ({compute_type})...")
    model = WhisperModel(whisper_model, device=device, compute_type=compute_type)

    with tempfile.TemporaryDirectory() as tmpdir:
        audio_file = os.path.join(tmpdir, f"{video_id}.m4a")
        cmd = [
            "yt-dlp",
            "-x", "--audio-format", "m4a",
            "-o", audio_file,
            f"https://www.youtube.com/watch?v={video_id}"
        ]
        logger.info(f"Downloading audio for {video_id}...")
        subprocess.run(cmd, capture_output=True, check=True)

        logger.info(f"Transcribing {video_id} with faster-whisper (Hindi language)...")
        segments_gen, _ = model.transcribe(audio_file, language="hi", beam_size=5)

        segments = []
        for s in segments_gen:
            segments.append({
                "text": s.text.strip(),
                "start": s.start,
                "end": s.end,
                "duration": s.end - s.start
            })

    logger.info(f"Transcription complete: {len(segments)} segments extracted via {model_tag}.")
    return segments, model_tag


def main():
    from config import SUPPORTED_CHANNELS
    parser = argparse.ArgumentParser(description="Google Colab GPU Satsang Ingestion")
    parser.add_argument("--channel", type=str, default="all", help=f"Target channel ({', '.join(SUPPORTED_CHANNELS.keys())}, 'all', or comma-separated list)")
    parser.add_argument("--max-videos", type=int, default=10, help="Max videos per channel (0 for unlimited)")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size per channel in round-robin mode")
    parser.add_argument("--video-id", type=str, default=None)
    parser.add_argument("--whisper-model", type=str, default="large-v3", help="Default to large-v3 for high-accuracy Hindi on Colab T4 GPU")
    args = parser.parse_args()

    has_gpu = check_gpu()

    from ingest import MultiChannelIngestionPipeline
    pipeline = MultiChannelIngestionPipeline()

    if args.video_id:
        import re, subprocess
        from schema import VideoMetadata, SourceChannel
        raw_id = args.video_id.strip()
        match = re.search(r"(?:v=|\/|youtu\.be\/)([0-9A-Za-z_-]{11})", raw_id)
        vid_id = match.group(1) if match else raw_id
        logger.info(f"🚀 Ingesting Single Video on Colab GPU: {vid_id}")

        title = f"Discourse {vid_id}"
        detected_channel = SourceChannel.BHAJAN_MARG
        if args.channel and args.channel != "all":
            ch_clean = args.channel.strip().lower()
            if ch_clean in [c.value for c in SourceChannel]:
                detected_channel = SourceChannel(ch_clean)

        try:
            cmd = ["yt-dlp", "--skip-download", "--print", "%(title)s\t%(channel)s", f"https://www.youtube.com/watch?v={vid_id}"]
            yt_res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
            line = yt_res.stdout.strip()
            if line and "\t" in line:
                p = line.split("\t")
                if p[0]: title = p[0]
                if len(p) > 1 and p[1] and (not args.channel or args.channel == "all"):
                    ch_name = p[1].lower()
                    if "sadhan" in ch_name: detected_channel = SourceChannel.SADHAN_PATH
                    elif "ras" in ch_name: detected_channel = SourceChannel.VRINDAVAN_RAS
                    elif "radha kripa" in ch_name: detected_channel = SourceChannel.SHRI_HIT_RADHA_KRIPA
                    elif "bhajan" in ch_name: detected_channel = SourceChannel.BHAJAN_MARG
        except Exception:
            pass

        segments, full_text, trans_model = pipeline.extract_transcript(vid_id)
        if not segments:
            logger.info("YouTube captions unavailable. Running Whisper on Colab GPU...")
            segments_raw, model_tag = run_colab_transcription(vid_id, whisper_model=args.whisper_model, use_gpu=has_gpu)
            from schema import TranscriptSegment
            segments = [TranscriptSegment(text=s["text"], start=s["start"], duration=s["duration"]) for s in segments_raw]
            full_text = " ".join([s.text for s in segments])
            trans_model = model_tag

        meta = VideoMetadata(
            video_id=vid_id,
            channel_id=detected_channel,
            title=title,
            url=f"https://www.youtube.com/watch?v={vid_id}",
            transcription_model=trans_model,
        )
        res = pipeline.process_video(meta, segments, full_text, transcription_model=trans_model)
        print(f"\n🎉 Successfully Ingested Video {vid_id} into Supabase!\nResult: {res}")
        return
    else:
        raw_channels = [c.strip().lower() for c in args.channel.split(",") if c.strip()]
        if "all" in raw_channels:
            target_channels = list(SUPPORTED_CHANNELS.keys())
        else:
            target_channels = [c for c in raw_channels if c in SUPPORTED_CHANNELS]
            if not target_channels:
                raise ValueError(f"No valid channels specified in '{args.channel}'. Must be one of {list(SUPPORTED_CHANNELS.keys())} or 'all'.")

        if len(target_channels) > 1:
            logger.info(f"🚀 Running Round-Robin Ingestion across {len(target_channels)} channels on GPU: {target_channels}")
            res = pipeline.ingest_channels_round_robin(
                channels=target_channels,
                max_videos_per_channel=args.max_videos,
                batch_size=args.batch_size
            )
        else:
            ch = target_channels[0]
            logger.info(f"🚀 Running Ingestion for channel '{ch}' on GPU...")
            res = pipeline.ingest_channel(ch, max_videos=args.max_videos)

        print(f"\n🎉 Colab Ingestion Complete! Summary Report: {res}")


if __name__ == "__main__":
    main()

