"""
SWAYAMBHU v2 - Status & Ingestion Monitor
Checks how many videos and transcript chunks have been ingested into the vector database.
"""

import sys
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config import settings
from indexer import get_vector_store

console = Console(force_terminal=True)


def check_ingestion_status():
    store = get_vector_store()
    backend_name = type(store).__name__

    console.print(
        Panel(
            f"[bold gold1]🕉️ SWAYAMBHU v2 — Ingestion Status & Catalog[/bold gold1]\n"
            f"[dim]Active Backend: [cyan]{backend_name}[/cyan] | Environment: [yellow]{settings.app_env.value}[/yellow][/dim]",
            border_style="gold1"
        )
    )

    if hasattr(store, "client"):  # SupabaseVectorStore
        try:
            v_res = store.client.table("videos").select("video_id", count="exact").execute()
            c_res = store.client.table("transcript_chunks").select("id", count="exact").execute()
            total_videos = v_res.count or 0
            total_chunks = c_res.count or 0

            summary_table = Table(title="📊 Database Overview (Supabase Postgres)", border_style="cyan")
            summary_table.add_column("Channel / Source", style="bold yellow")
            summary_table.add_column("Videos Count", justify="right", style="green")
            summary_table.add_column("Transcript Chunks", justify="right", style="cyan")

            from config import SUPPORTED_CHANNELS
            for ch_key, ch_cfg in SUPPORTED_CHANNELS.items():
                v_ch = store.client.table("videos").select("video_id", count="exact").eq("channel_id", ch_key).execute()
                c_ch = store.client.table("transcript_chunks").select("id", count="exact").eq("channel_id", ch_key).execute()
                handle_str = ch_cfg.handles[0] if ch_cfg.handles else ch_key
                summary_table.add_row(
                    f"{ch_cfg.title} ({handle_str})",
                    str(v_ch.count or 0),
                    str(c_ch.count or 0)
                )

            summary_table.add_row(
                "[bold]Total Across Channels[/bold]",
                f"[bold green]{total_videos}[/bold green]",
                f"[bold cyan]{total_chunks}[/bold cyan]"
            )
            console.print(summary_table)

            # Show recent 10 videos
            v_sample = (
                store.client.table("videos")
                .select("video_id, title, channel_id")
                .order("created_at", desc=True)
                .limit(10)
                .execute()
            )
            if v_sample.data:
                sample_table = Table(title="🎬 Latest Ingested Videos (Sample)", border_style="gold1")
                sample_table.add_column("#", justify="right", width=4)
                sample_table.add_column("Video ID", style="magenta", width=14)
                sample_table.add_column("Channel", style="yellow", width=14)
                sample_table.add_column("Title", style="white")

                for idx, row in enumerate(v_sample.data, 1):
                    sample_table.add_row(
                        str(idx),
                        str(row.get("video_id", "")),
                        str(row.get("channel_id", "")),
                        str(row.get("title", ""))[:60]
                    )
                console.print(sample_table)

        except Exception as e:
            console.print(f"[red]Error querying Supabase: {e}[/red]")

    # Check local fallback ChromaDB as well
    try:
        import chromadb
        chroma_client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        try:
            col = chroma_client.get_collection("swayambhu_chunks")
            c_count = col.count()
            metas = col.get(include=["metadatas"])
            distinct_vids = {m.get("video_id") for m in (metas.get("metadatas") or []) if m and "video_id" in m}
            console.print(
                f"\n[dim]Local ChromaDB Cache ({settings.chroma_persist_dir}): "
                f"[bold]{len(distinct_vids)}[/bold] videos, [bold]{c_count}[/bold] chunks[/dim]"
            )
        except Exception:
            pass
    except Exception:
        pass


if __name__ == "__main__":
    check_ingestion_status()
