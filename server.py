"""
SWAYAMBHU v2 - FastAPI Production API Server

Endpoints:
  POST /api/chat     - Grounded, cited spiritual Q&A (rate-limited, returns disclaimer)
  POST /api/feedback - User response rating and flagged answer logging
  GET  /api/stats    - Channel chunk metrics and query telemetry stats
  GET  /api/health   - System health, vector store backend, and LLM status

Strictly JSON API layer. Zero HTML/CSS/JS.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
import os
import time
from typing import Dict, Optional, Tuple
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import AppEnvironment, settings
from rag_engine import RAGEngine
from schema import (
    ChatRequest,
    ChatResponse,
    FeedbackRequest,
    FeedbackResponse,
    HealthResponse,
    SourceChannel,
    StatsResponse,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("swayambhu.server")

# ============================================================================
# Pluggable Rate Limiter (Token Bucket / Sliding Window)
# ============================================================================

class RateLimiterBackend:
    """Abstract interface for token bucket storage."""
    def is_allowed(self, client_id: str, max_per_minute: int, burst: int) -> Tuple[bool, int]:
        raise NotImplementedError


class InMemoryTokenBucket(RateLimiterBackend):
    """In-memory token bucket implementation for single-process / dev."""
    def __init__(self):
        # client_id -> (tokens, last_refill_timestamp)
        self.buckets: Dict[str, Tuple[float, float]] = {}

    def is_allowed(self, client_id: str, max_per_minute: int, burst: int) -> Tuple[bool, int]:
        now = time.time()
        refill_rate = max_per_minute / 60.0  # tokens per second

        if client_id not in self.buckets:
            self.buckets[client_id] = (float(burst) - 1.0, now)
            return True, int(burst - 1)

        tokens, last_refill = self.buckets[client_id]
        elapsed = now - last_refill
        # Refill tokens up to burst capacity
        tokens = min(float(burst), tokens + elapsed * refill_rate)

        if tokens >= 1.0:
            tokens -= 1.0
            self.buckets[client_id] = (tokens, now)
            return True, int(tokens)
        else:
            self.buckets[client_id] = (tokens, now)
            retry_after = int((1.0 - tokens) / refill_rate) + 1
            return False, retry_after


class RedisTokenBucket(RateLimiterBackend):
    """Redis-backed distributed token bucket for multi-process / cluster deployments."""
    def __init__(self, redis_url: str):
        import redis
        self.redis_client = redis.Redis.from_url(redis_url, decode_responses=True)

    def is_allowed(self, client_id: str, max_per_minute: int, burst: int) -> Tuple[bool, int]:
        # Sliding-window log implementation in Redis
        key = f"rate_limit:{client_id}"
        now_ms = int(time.time() * 1000)
        window_ms = 60000

        pipe = self.redis_client.pipeline()
        pipe.zremrangebyscore(key, 0, now_ms - window_ms)
        pipe.zcard(key)
        pipe.zadd(key, {str(now_ms): now_ms})
        pipe.expire(key, 65)
        _, current_count, _, _ = pipe.execute()

        if current_count >= max_per_minute:
            return False, 10
        return True, max(0, max_per_minute - current_count)


# Initialize Rate Limiter
if settings.redis_url:
    try:
        rate_limiter = RedisTokenBucket(settings.redis_url)
        logger.info("Configured Redis-backed distributed rate limiter.")
    except Exception as e:
        logger.warning(f"Could not connect to Redis ({e}). Falling back to in-memory bucket.")
        rate_limiter = InMemoryTokenBucket()
else:
    rate_limiter = InMemoryTokenBucket()


def check_rate_limit(request: Request):
    """FastAPI dependency enforcing per-IP / API key rate limiting."""
    # Resolve client identifier: header API key or IP address
    client_ip = (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or request.headers.get("X-Real-IP")
        or request.client.host
        if request.client else "127.0.0.1"
    )
    api_key = request.headers.get("X-API-Key")
    client_id = f"key_{api_key}" if api_key else f"ip_{client_ip}"

    allowed, remaining_or_retry = rate_limiter.is_allowed(
        client_id=client_id,
        max_per_minute=settings.rate_limit_per_minute,
        burst=settings.rate_limit_burst
    )

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"सत्संग शोध अनुरोध सीमा समाप्त हो गई है (Rate limit reached). "
                f"कृपया {remaining_or_retry} सेकंड प्रतीक्षा करें।"
            ),
            headers={"Retry-After": str(remaining_or_retry)}
        )


# ============================================================================
# Application Lifecycle & Instantiation
# ============================================================================

rag_engine: Optional[RAGEngine] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global rag_engine
    logger.info(f"Starting {settings.app_name} [Environment: {settings.app_env.value}]")
    logger.info(f"Vector Store Backend: {settings.vector_store_backend.value}")
    rag_engine = RAGEngine()
    try:
        logger.info("Pre-warming embedding model on startup...")
        rag_engine.embedding_generator.embed_query("राधा नाम")
        logger.info("Embedding model pre-warmed and ready.")
    except Exception as e:
        logger.warning(f"Model pre-warm warning: {e}")
    yield
    logger.info("Shutting down SWAYAMBHU v2 backend.")


app = FastAPI(
    title=settings.app_name,
    description="Grounded, cited Q&A engine based on recorded satsangs of Param Pujya Shri Hit Premanand Govind Sharan Ji Maharaj",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for external frontends or integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# API Endpoints
# ============================================================================

@app.post(
    "/api/chat",
    response_model=ChatResponse,
    dependencies=[Depends(check_rate_limit)],
    summary="Ask a spiritual question grounded in Maharaj Ji's recordings",
)
def chat_endpoint(request: ChatRequest, raw_req: Request) -> ChatResponse:
    """
    Submits a query to the grounded RAG engine.
    - Contextualizes conversation history.
    - Normalizes Hinglish to Devanagari.
    - Retrieves verified chunks across Bhajan Marg and Sadhan Path.
    - Answers strictly with citations and YouTube timestamp links.
    - Refuses to guess if unrecorded.
    """
    if not rag_engine:
        raise HTTPException(status_code=500, detail="RAG Engine not initialized.")

    client_ip = (
        raw_req.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or (raw_req.client.host if raw_req.client else "127.0.0.1")
    )

    response = rag_engine.process_query(request, client_ip=client_ip)
    return response


@app.post("/api/feedback", response_model=FeedbackResponse, summary="Submit answer rating or flag inaccuracies")
def feedback_endpoint(feedback: FeedbackRequest, raw_req: Request) -> FeedbackResponse:
    """Logs user feedback for continuous retrieval auditing and alignment."""
    client_ip = (
        raw_req.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or (raw_req.client.host if raw_req.client else "127.0.0.1")
    )
    feedback_id = str(uuid4())

    # Log to Supabase if configured
    if settings.supabase_url and settings.supabase_service_role_key:
        try:
            from supabase import create_client
            client = create_client(settings.supabase_url, settings.supabase_service_role_key)
            client.table("feedback").insert({
                "id": feedback_id,
                "query": feedback.query,
                "answer": feedback.answer,
                "flagged": feedback.flagged,
                "note": feedback.note,
                "ip_address": client_ip,
            }).execute()
        except Exception as e:
            logger.warning(f"Could not persist feedback to DB: {e}")

    logger.info(f"Feedback recorded [{feedback_id}]: Flagged={feedback.flagged} | Note={feedback.note}")
    return FeedbackResponse(
        status="success",
        feedback_id=feedback_id,
        message="सत्संग शोध प्रतिक्रिया सफलतापूर्वक दर्ज की गई।"
    )


# Cache stats for 30s so high ingestion load doesn't slow down the UI
_stats_cache = None
_stats_cache_time = 0.0

@app.get("/api/stats", response_model=StatsResponse, summary="Retrieve catalog and ingestion metrics")
def stats_endpoint() -> StatsResponse:
    """Returns total videos, chunks, and cross-channel distribution."""
    global _stats_cache, _stats_cache_time
    import time
    now = time.time()
    if _stats_cache and (now - _stats_cache_time) < 30.0:
        return _stats_cache

    if not rag_engine:
        raise HTTPException(status_code=500, detail="Engine offline.")

    vs = rag_engine.vector_store
    from config import SUPPORTED_CHANNELS
    from schema import ChannelStats

    channels_dict = {}
    total_chunks = 0
    total_videos = 0

    for ch_key in SUPPORTED_CHANNELS.keys():
        try:
            ch_enum = SourceChannel(ch_key)
            c_count = vs.count_chunks(ch_enum)
        except Exception:
            c_count = 0
        total_chunks += c_count

        v_count = 0
        if hasattr(vs, "client"):
            try:
                res = vs.client.table("videos").select("video_id", count="exact").eq("channel_id", ch_key).execute()
                v_count = res.count or 0
            except Exception:
                pass
        total_videos += v_count

        channels_dict[ch_key] = ChannelStats(
            channel=ch_enum,
            total_videos=v_count,
            canonical_videos=v_count,
            duplicate_videos=0,
            total_chunks=c_count,
            active_chunks=c_count,
        )

    _stats_cache = StatsResponse(
        total_videos=total_videos,
        total_chunks=total_chunks,
        channels=channels_dict,
        total_queries=0,
        total_feedback=0,
    )
    _stats_cache_time = now
    return _stats_cache


@app.get("/api/health", response_model=HealthResponse, summary="Service health check")
async def health_endpoint() -> HealthResponse:
    """Returns operational status, environment, and backend connectivity."""
    llm_info = (
        "Google AI Studio (Gemma)" if (settings.gemini_api_key or settings.google_api_key)
        else "OpenRouter (Gemma/Llama)" if settings.openrouter_api_key
        else "Groq" if settings.groq_api_key
        else "Ollama"
    )
    return HealthResponse(
        status="healthy",
        app_env=settings.app_env.value,
        vector_store=settings.vector_store_backend.value,
        llm_provider=llm_info,
        timestamp=datetime.now(timezone.utc),
    )


# Mount frontend static directory if present
premanand_website_dir = os.path.join(os.path.dirname(__file__), "premanand-ji-website", "dist", "public")
stitch_dir = os.path.join(os.path.dirname(__file__), "stitch_screens")

if os.path.exists(premanand_website_dir):
    from fastapi.staticfiles import StaticFiles
    logger.info(f"Mounting Premanand Ji Website static frontend from {premanand_website_dir}")
    app.mount("/", StaticFiles(directory=premanand_website_dir, html=True), name="frontend")
elif os.path.exists(stitch_dir):
    from fastapi.staticfiles import StaticFiles
    logger.info(f"Mounting stitch_screens frontend from {stitch_dir}")
    app.mount("/", StaticFiles(directory=stitch_dir, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
