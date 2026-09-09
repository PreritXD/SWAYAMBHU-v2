"""
SWAYAMBHU v2 - Terminal CLI Interface (Testing & Verification)

Interactive command-line testing tool for the grounded Satsang Q&A system.
Displays answers, channel provenance, clickable timestamp links, and confidence metrics.
"""

import argparse
import sys

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

from config import settings
from rag_engine import RAGEngine
from indexer import normalize_hinglish_to_devanagari
from schema import ChatMessage, ChatRequest, ChatRole, SourceChannel

console = Console(force_terminal=True)


def display_response(resp):
    """Renders a formatted ChatResponse to the terminal using Rich."""
    # Main Answer Panel
    title = "[bold green]🙏 पूज्य महाराज जी के वचनों पर आधारित समाधान[/bold green]" if resp.is_grounded else "[bold yellow]⚠️ विषय उल्लेखित नहीं है (Refusal to Guess)[/bold yellow]"
    console.print(Panel(resp.answer, title=title, border_style="green" if resp.is_grounded else "yellow"))

    # Telemetry
    if resp.normalized_query:
        console.print(f"[dim]देवनागरी रूपांतरण (Normalized Query): {resp.normalized_query}[/dim]")
    if resp.rewritten_query:
        console.print(f"[dim]संदर्भित प्रश्न (Rewritten Query): {resp.rewritten_query}[/dim]")
    console.print(f"[dim]प्रतिक्रिया समय (Latency): {resp.latency_ms}ms | प्रदाता/मॉडल: {resp.model_used}[/dim]\n")

    # Citations Table
    if resp.citations:
        table = Table(title="प्रमाणित सत्संग संदर्भ (Verified Citations)", border_style="cyan")
        table.add_column("चैनल (Channel)", style="bold cyan", width=16)
        table.add_column("वीडियो (Video ID)", style="magenta", width=14)
        table.add_column("समय (Timestamp)", style="yellow", width=14)
        table.add_column("प्रासंगिकता (Score)", style="green", width=10)
        table.add_column("सीधा लिंक (YouTube URL)", style="blue")

        for c in resp.citations:
            ch_name = "Bhajan Marg" if c.channel == SourceChannel.BHAJAN_MARG else "Sadhan Path"
            table.add_row(
                ch_name,
                c.video_id,
                f"{c.timestamp_start} - {c.timestamp_end}",
                f"{c.relevance_score:.2f}",
                c.url
            )

        console.print(table)

    # Disclaimer
    console.print(Panel(resp.disclaimer.text, title="[dim]अस्वीकरण (Disclaimer)[/dim]", border_style="dim"))


def interactive_chat():
    """Interactive multi-turn conversation loop in terminal."""
    console.print(Panel.fit(
        "[bold cyan]SWAYAMBHU v2 - सत्संग शोध प्रणाली (Terminal CLI)[/bold cyan]\n"
        "[dim]Param Pujya Shri Hit Premanand Govind Sharan Ji Maharaj Satsang Q&A[/dim]\n"
        "[yellow]टाइप 'exit' या 'quit' बाहर निकलने के लिए।[/yellow]",
        border_style="cyan"
    ))

    engine = RAGEngine()
    history = []

    while True:
        try:
            user_input = console.input("[bold yellow]साधक का प्रश्न > [/bold yellow]").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                console.print("[cyan]जय श्री राधे! 🙏[/cyan]")
                break

            req = ChatRequest(message=user_input, history=history)
            resp = engine.process_query(req)
            display_response(resp)

            # Append to history
            history.append(ChatMessage(role=ChatRole.USER, content=user_input))
            history.append(ChatMessage(role=ChatRole.ASSISTANT, content=resp.answer))

        except KeyboardInterrupt:
            console.print("\n[cyan]जय श्री राधे! 🙏[/cyan]")
            break
        except Exception as e:
            console.print(f"[bold red]त्रुटि (Error): {e}[/bold red]")


def single_query(question: str, channel: str = None):
    """Processes a single question."""
    engine = RAGEngine()
    ch_filter = SourceChannel(channel) if channel else None
    req = ChatRequest(message=question, channel_filter=ch_filter)
    resp = engine.process_query(req)
    display_response(resp)


def main():
    parser = argparse.ArgumentParser(description="SWAYAMBHU v2 Terminal Testing CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Command: ask
    ask_parser = subparsers.add_parser("ask", help="Ask a single question")
    ask_parser.add_argument("query", type=str, help="Spiritual question in Hindi or Hinglish")
    ask_parser.add_argument("--channel", choices=["bhajan_marg", "sadhan_path"], default=None, help="Optional channel filter")

    # Command: chat
    subparsers.add_parser("chat", help="Start interactive multi-turn chat session")

    # Command: transliterate
    trans_parser = subparsers.add_parser("transliterate", help="Test Hinglish to Devanagari transliteration")
    trans_parser.add_argument("text", type=str, help="Hinglish text")

    args = parser.parse_args()

    if args.command == "ask":
        single_query(args.query, args.channel)
    elif args.command == "transliterate":
        res = normalize_hinglish_to_devanagari(args.text)
        console.print(f"[bold cyan]Input:[/bold cyan] {args.text}")
        console.print(f"[bold green]Devanagari:[/bold green] {res}")
    else:
        interactive_chat()


if __name__ == "__main__":
    main()
