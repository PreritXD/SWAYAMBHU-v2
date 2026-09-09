"""
SWAYAMBHU v2 - Pydantic Schemas & Data Transfer Objects

Defines domain models for videos, transcript chunks, cross-channel deduplication,
FastAPI request/response contracts, citations, and evaluation records.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, HttpUrl


class SourceChannel(str, Enum):
    BHAJAN_MARG = "bhajan_marg"
    SADHAN_PATH = "sadhan_path"
    VRINDAVAN_RAS = "vrindavan_ras"
    SHRI_HIT_RADHA_KRIPA = "shri_hit_radha_kripa"


class CrossChannelAlias(BaseModel):
    channel: SourceChannel
    video_id: str
    video_title: Optional[str] = None
    timestamp_sec: int
    timestamp_formatted: str


class TranscriptSegment(BaseModel):
    text: str
    start: float
    duration: float
    end: Optional[float] = None

    def model_post_init(self, __context: Any) -> None:
        if self.end is None:
            self.end = self.start + self.duration


class VideoMetadata(BaseModel):
    video_id: str
    channel_id: SourceChannel
    title: str
    url: str
    upload_date: Optional[date] = None
    duration_seconds: Optional[int] = None
    view_count: Optional[int] = None
    description: Optional[str] = None
    transcript_language: str = "hi"
    transcription_model: str = "youtube_captions"
    is_duplicate: bool = False
    canonical_video_id: Optional[str] = None
    dedup_similarity_score: Optional[float] = None


class ChunkRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    video_id: str
    channel_id: SourceChannel
    chunk_index: int
    start_sec: int
    end_sec: int
    start_formatted: str
    end_formatted: str
    raw_text: str
    clean_text: str
    token_count: int
    embedding: Optional[List[float]] = None
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    is_duplicate: bool = False
    canonical_chunk_id: Optional[str] = None
    canonical_video_id: Optional[str] = None
    cross_channel_aliases: List[CrossChannelAlias] = Field(default_factory=list)


class DedupMatch(BaseModel):
    is_duplicate: bool
    similarity_score: float
    canonical_video_id: Optional[str] = None
    canonical_channel_id: Optional[SourceChannel] = None
    matched_chunk_id: Optional[str] = None
    reason: str


class DedupResult(BaseModel):
    total_scanned: int
    duplicates_found: int
    canonical_records: int
    details: List[Dict[str, Any]] = Field(default_factory=list)


# ============================================================================
# Chat & API Request / Response Schemas
# ============================================================================

class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    role: ChatRole
    content: str


class ChatRequest(BaseModel):
    message: str = Field(default="", min_length=1, max_length=2000, description="The user question in Hindi or Hinglish")
    query: Optional[str] = Field(default=None, description="Alias for message")
    history: List[ChatMessage] = Field(default_factory=list, description="Prior conversation history for context rewriting")
    session_id: Optional[str] = Field(default=None, description="Optional session tracking ID")
    channel_filter: Optional[SourceChannel] = Field(default=None, description="Optional filter to retrieve only from a specific channel")
    use_council: bool = Field(default=False, description="Enable 3-stage LLM Council deliberation for deep philosophical inquiries")

    @classmethod
    def model_validate(cls, obj: Any, *args, **kwargs):
        if isinstance(obj, dict):
            text = obj.get("message") or obj.get("query") or ""
            obj["message"] = str(text).strip()
            obj["query"] = str(text).strip()
        return super().model_validate(obj, *args, **kwargs)


class Citation(BaseModel):
    video_id: str
    title: str
    channel: SourceChannel
    start_sec: int
    end_sec: int
    timestamp_start: str
    timestamp_end: str
    url: str                                    # e.g., https://youtu.be/xxx?t=75
    relevance_score: float
    excerpt: str                                # The verified transcript passage
    cross_channel_aliases: List[CrossChannelAlias] = Field(default_factory=list)


class ChatDisclaimer(BaseModel):
    text: str = (
        "यह उत्तर पूज्य श्री हित प्रेमानंद गोविंद शरण जी महाराज के सार्वजनिक रूप से उपलब्ध सत्संग वचनों "
        "पर आधारित एक एआई-संवर्धित शोध प्रणाली है, और यह आश्रम अथवा पूज्य महाराज जी का आधिकारिक मंच नहीं है। "
        "किसी भी संशय की स्थिति में दिए गए मूल वीडियो प्रमाण को देखकर ही प्रमाणिक समझ प्राप्त करें।"
    )
    is_official_channel: bool = False


class ChatResponse(BaseModel):
    answer: str
    is_grounded: bool
    refusal_reason: Optional[str] = None
    citations: List[Citation] = Field(default_factory=list)
    disclaimer: ChatDisclaimer = Field(default_factory=ChatDisclaimer)
    normalized_query: Optional[str] = None
    rewritten_query: Optional[str] = None
    latency_ms: int
    model_used: str
    llm_provider: Optional[str] = None
    use_council: bool = False
    council_deliberation: Optional[Dict[str, Any]] = None
    case_category: Optional[str] = None


# ============================================================================
# Feedback & Telemetry
# ============================================================================

class FeedbackRequest(BaseModel):
    query: str
    answer: str
    flagged: bool
    note: Optional[str] = None


class FeedbackResponse(BaseModel):
    status: str = "success"
    feedback_id: str
    message: str = "Feedback recorded successfully."


class ChannelStats(BaseModel):
    channel: SourceChannel
    total_videos: int
    canonical_videos: int
    duplicate_videos: int
    total_chunks: int
    active_chunks: int


class StatsResponse(BaseModel):
    total_videos: int
    total_chunks: int
    channels: Dict[str, ChannelStats]
    total_queries: int
    total_feedback: int


class HealthResponse(BaseModel):
    status: str
    app_env: str
    vector_store: str
    llm_provider: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Evaluation Models
# ============================================================================

class EvalTestCase(BaseModel):
    id: str
    question: str
    query_type: str                            # 'clean_hindi', 'messy_hinglish', 'pronoun_followup', 'off_domain'
    expected_channel: Optional[SourceChannel] = None
    expected_topic: str
    expected_answer_contains: List[str] = Field(default_factory=list)
    should_refuse: bool = False
    context_history: List[ChatMessage] = Field(default_factory=list)


class EvalItemResult(BaseModel):
    test_id: str
    question: str
    query_type: str
    hit_rate: bool
    refusal_correct: bool
    retrieved_channels: List[SourceChannel]
    top_citation: Optional[str] = None
    latency_ms: int
    error: Optional[str] = None


class EvalRunReport(BaseModel):
    total_tests: int
    overall_hit_rate: float
    refusal_accuracy: float
    false_positive_rate: float
    false_negative_rate: float
    bhajan_marg_retrieval_count: int
    sadhan_path_retrieval_count: int
    channel_balance_ratio: float
    average_latency_ms: float
    results: List[EvalItemResult]
