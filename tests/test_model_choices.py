"""
Tests for Finalized 100% Free Model Choices, Zero Per-Query Cost Enforcement,
Strict Fallback Chains, and Model Tracking Telemetry.
"""

from config import settings
from schema import ChunkRecord, VideoMetadata, SourceChannel, ChatRequest
from indexer import CrossEncoderReRanker
from rag_engine import RAGEngine


def test_free_llm_fallback_chain_and_models():
    """Verify LLM fallback sequence: Google Gemma -> Groq -> OpenRouter Llama -> OpenRouter Gemma -> Ollama."""
    expected_chain = ["google_gemma", "groq", "openrouter_llama", "openrouter_gemma", "ollama"]
    assert settings.llm_provider_chain == expected_chain

    # Verify model identifiers belong to supported free models
    assert settings.primary_llm_model in ["llama-3.3-70b-versatile", "openai/gpt-oss-120b", "qwen/qwen3.8-27b", "groq/compound"]
    assert settings.openrouter_llama_model.endswith(":free") or settings.openrouter_llama_model in ["meta-llama/llama-3.3-70b-instruct:free", "nvidia/nemotron-3.5-lightning:free", "minimax/minimax-m3:free"]
    assert settings.openrouter_gemma_model.endswith(":free") or settings.openrouter_gemma_model in ["google/gemma-3-27b-it:free", "google/gemma-4-31b-it:free"]
    assert settings.ollama_model == "llama3.2"

    # Verify paid OpenAI models are completely removed from settings
    assert not hasattr(settings, "openai_api_key")
    assert "openai" not in settings.llm_provider_chain


def test_embedding_model_is_single_multilingual_384_dim():
    """Verify single multilingual embedding model across the stack with 384 dimensions."""
    expected_model = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    assert settings.embedding_model_name == expected_model
    assert settings.embedding_dim == 384

    # Verify ChunkRecord tracks embedding_model string
    chunk = ChunkRecord(
        video_id="test_vid_123",
        channel_id=SourceChannel.BHAJAN_MARG,
        chunk_index=0,
        start_sec=0,
        end_sec=60,
        start_formatted="00:00",
        end_formatted="01:00",
        raw_text="राधा नाम परम सुखदाई।",
        clean_text="राधा नाम परम सुखदाई।",
        token_count=6,
    )
    assert chunk.embedding_model == expected_model


def test_cross_encoder_reranker_wiring():
    """Verify cross-encoder re-ranker runs and sets cross_encoder_score."""
    assert settings.rerank_model_name == "cross-encoder/ms-marco-MiniLM-L-6-v2"

    candidates = [
        {"id": "chunk_1", "clean_text": "नाम जप कैसे करें और क्या नियम हैं?", "similarity": 0.75},
        {"id": "chunk_2", "clean_text": "साधना में मन लगाने के उपाय।", "similarity": 0.65},
    ]

    reranker = CrossEncoderReRanker()
    reranked = reranker.rerank(query="नाम जप", candidate_chunks=candidates, top_k=2)

    assert len(reranked) == 2
    for c in reranked:
        assert "cross_encoder_score" in c
    # Highest score first
    assert reranked[0]["cross_encoder_score"] >= reranked[1]["cross_encoder_score"]


def test_transcription_hierarchy_and_tracking():
    """Verify transcription hierarchy models and VideoMetadata tracking."""
    assert settings.whisper_cloud_primary == "whisper-large-v3"
    assert settings.whisper_cloud_fallback == "whisper-large-v3-turbo"
    assert settings.local_whisper_gpu_model == "large-v3"
    assert settings.local_whisper_cpu_model == "medium"
    assert settings.whisper_dev_mode is False

    meta = VideoMetadata(
        video_id="test_vid_abc",
        channel_id=SourceChannel.SADHAN_PATH,
        title="सत्संग चर्चा",
        url="https://youtu.be/test_vid_abc",
        transcription_model="groq/whisper-large-v3",
    )
    assert meta.transcription_model == "groq/whisper-large-v3"


def test_query_response_telemetry_includes_provider_and_model():
    """Verify ChatResponse captures both provider and model used."""
    engine = RAGEngine()
    req = ChatRequest(message="नाम जप की महिमा क्या है?")
    resp = engine.process_query(req)

    assert resp.model_used is not None
    assert resp.llm_provider is not None
