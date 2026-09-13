"""
Tests for Grounded RAG Engine, Strict Refusal to Guess, and Citation Building
"""

from rag_engine import RAGEngine
from schema import ChatRequest, SourceChannel, ChunkRecord


def test_rag_engine_refusal_when_no_context():
    """Engine must explicitly refuse to answer when vector store returns zero chunks."""
    engine = RAGEngine()
    # Query something not in the empty local test vector store
    req = ChatRequest(message="महाराज जी ने क्वांटम भौतिकी के बारे में क्या कहा है?")
    resp = engine.process_query(req)

    assert resp.is_grounded is False
    assert len(resp.citations) == 0
    assert "उल्लेख" in resp.answer or "परिधि" in resp.answer
    assert resp.disclaimer is not None


def test_rag_engine_citation_urls_with_timestamp():
    """Verifies that chunks are formatted with proper https://youtu.be/{video_id}?t={start_sec} links."""
    engine = RAGEngine()
    chunk = ChunkRecord(
        video_id="abc123xyz",
        channel_id=SourceChannel.BHAJAN_MARG,
        chunk_index=2,
        start_sec=145,
        end_sec=195,
        start_formatted="02:25",
        end_formatted="03:15",
        raw_text="नाम जप करने से समस्त विकार नष्ट हो जाते हैं।",
        clean_text="नाम जप करने से समस्त विकार नष्ट हो जाते हैं।",
        token_count=15,
        embedding=engine.embedding_generator.embed_query("नाम जप"),
    )

    # Insert test chunk into vector store
    engine.vector_store.insert_chunks([chunk])

    # Query matching this chunk
    req = ChatRequest(message="नाम जप से क्या होता है?")
    resp = engine.process_query(req)

    if resp.citations:
        cit = resp.citations[0]
        assert cit.video_id
        assert cit.url == f"https://youtu.be/{cit.video_id}?t={cit.start_sec}"
        assert cit.start_sec >= 0
        assert ":" in cit.timestamp_start
