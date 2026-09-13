"""
SWAYAMBHU v2 - Global Configuration and Environment Validation

Validates all environment variables and secrets at application startup.
Provides fail-fast enforcement with zero silent fallback in production.
Every model used is 100% free with zero per-query cost.
"""

import json
import logging
import os
from enum import Enum
from typing import Any

from dotenv import load_dotenv
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env if present
load_dotenv()

logger = logging.getLogger("swayambhu.config")


class AppEnvironment(str, Enum):
    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"
    TEST = "test"


class VectorStoreType(str, Enum):
    SUPABASE = "supabase"
    CHROMA = "chroma"


class ChannelConfig:
    def __init__(self, key: str, title: str, handles: list[str], yt_channel_id: str | None = None):
        self.key = key
        self.title = title
        self.handles = handles
        self.yt_channel_id = yt_channel_id


# Source channels definition
SUPPORTED_CHANNELS: dict[str, ChannelConfig] = {
    "bhajan_marg": ChannelConfig(
        key="bhajan_marg",
        title="Bhajan Marg",
        handles=["@BhajanMarg", "@BhajanMargOfficial"],
        yt_channel_id="UCB3b4N2bW2Z_X3iT3j9O5Wg"
    ),
    "sadhan_path": ChannelConfig(
        key="sadhan_path",
        title="Sadhan Path",
        handles=["@sadhanpath"],
        yt_channel_id="UC4k1xP8s_dF2g0vM9Q3K_Sw"
    ),
    "vrindavan_ras": ChannelConfig(
        key="vrindavan_ras",
        title="Vrindavan Ras Mahima",
        handles=["@vrindavanrasmahima"],
        yt_channel_id=None
    ),
    "shri_hit_radha_kripa": ChannelConfig(
        key="shri_hit_radha_kripa",
        title="Shri Hit Radha Kripa",
        handles=["@shrihitradhakripa"],
        yt_channel_id=None
    ),
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Environment
    app_env: AppEnvironment = Field(default=AppEnvironment.DEVELOPMENT, alias="APP_ENV")
    app_name: str = Field(default="SWAYAMBHU v2 Backend", alias="APP_NAME")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Supabase / PostgreSQL Credentials
    supabase_url: str | None = Field(default=None, alias="SUPABASE_URL")
    supabase_key: str | None = Field(default=None, alias="SUPABASE_KEY")
    supabase_service_role_key: str | None = Field(default=None, alias="SUPABASE_SERVICE_ROLE_KEY")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")

    # Vector Store Backend
    vector_store_backend: VectorStoreType = Field(
        default=VectorStoreType.CHROMA,
        alias="VECTOR_STORE_BACKEND"
    )
    chroma_persist_dir: str = Field(default="./data/chroma_db", alias="CHROMA_PERSIST_DIR")
    allow_insecure_local_vector_in_prod: bool = Field(
        default=False,
        alias="ALLOW_INSECURE_LOCAL_VECTOR_IN_PROD"
    )

    # LLM Providers (100% Free Tiers Only - Zero Per-Query Cost)
    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    google_api_key: str | None = Field(default=None, alias="GOOGLE_API_KEY")
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")

    # Strict Ordered LLM Fallback Sequence
    llm_provider_chain: list[str] = Field(
        default=["google_gemma", "openrouter_gemma", "groq", "openrouter_llama", "ollama"],
        alias="LLM_PROVIDER_CHAIN"
    )

    # Specific Free-Tier LLM Models
    primary_llm_model: str = Field(default="llama-3.3-70b-versatile", alias="PRIMARY_LLM_MODEL")
    google_gemma_model: str = Field(
        default="gemma-4-26b-a4b-it",
        alias="GOOGLE_GEMMA_MODEL"
    )
    openrouter_llama_model: str = Field(
        default="meta-llama/llama-3.3-70b-instruct:free",
        alias="OPENROUTER_LLAMA_MODEL"
    )
    openrouter_gemma_model: str = Field(
        default="google/gemma-4-26b-a4b-it:free",
        alias="OPENROUTER_GEMMA_MODEL"
    )
    ollama_model: str = Field(default="llama3.2", alias="OLLAMA_MODEL")

    # Embedding Model (Single Multilingual Model Everywhere - 384 dimensions)
    embedding_model_name: str = Field(
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        alias="EMBEDDING_MODEL_NAME"
    )
    embedding_dim: int = Field(default=384, alias="EMBEDDING_DIM")

    # Cross-Encoder Re-ranking Model (Runs locally, free, zero API calls)
    rerank_model_name: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2",
        alias="RERANK_MODEL_NAME"
    )

    # Speech-to-Text / Audio Transcription Hierarchy
    whisper_cloud_primary: str = Field(default="whisper-large-v3", alias="WHISPER_CLOUD_PRIMARY")
    whisper_cloud_fallback: str = Field(default="whisper-large-v3-turbo", alias="WHISPER_CLOUD_FALLBACK")
    local_whisper_gpu_model: str = Field(default="large-v3", alias="LOCAL_WHISPER_GPU_MODEL")
    local_whisper_cpu_model: str = Field(default="medium", alias="LOCAL_WHISPER_CPU_MODEL")
    whisper_dev_mode: bool = Field(default=False, alias="WHISPER_DEV_MODE")
    whisper_device: str = Field(default="cpu", alias="WHISPER_DEVICE")

    # Rate Limiting & Redis
    redis_url: str | None = Field(default=None, alias="REDIS_URL")
    rate_limit_per_minute: int = Field(default=30, alias="RATE_LIMIT_PER_MINUTE")
    rate_limit_burst: int = Field(default=10, alias="RATE_LIMIT_BURST")

    # Query & Retrieval
    top_k_retrieval: int = Field(default=24, alias="TOP_K_RETRIEVAL")
    rerank_top_k: int = Field(default=5, alias="RERANK_TOP_K")
    similarity_threshold: float = Field(default=0.40, alias="SIMILARITY_THRESHOLD")
    dedup_video_threshold: float = Field(default=0.85, alias="DEDUP_VIDEO_THRESHOLD")
    dedup_chunk_threshold: float = Field(default=0.92, alias="DEDUP_CHUNK_THRESHOLD")

    @field_validator("llm_provider_chain", mode="before")
    @classmethod
    def parse_provider_chain(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                return [p.strip() for p in v.split(",") if p.strip()]
        return v

    @model_validator(mode="after")
    def validate_production_and_dependencies(self) -> "Settings":
        errors = []
        is_production = self.app_env in (AppEnvironment.PRODUCTION, AppEnvironment.STAGING)

        # Fail-fast check for Vector Store in Production
        if is_production:
            if not self.supabase_url:
                errors.append("SUPABASE_URL is required in production/staging.")
            if not self.supabase_service_role_key and not self.supabase_key:
                errors.append("SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_KEY) is required in production/staging.")
            if self.vector_store_backend == VectorStoreType.CHROMA and not self.allow_insecure_local_vector_in_prod:
                errors.append(
                    "VECTOR_STORE_BACKEND cannot be 'chroma' in production without "
                    "ALLOW_INSECURE_LOCAL_VECTOR_IN_PROD=true explicitly set."
                )

        # Check for at least one active free cloud LLM provider or local Ollama
        has_cloud_llm = any([self.groq_api_key, self.openrouter_api_key, self.gemini_api_key, self.google_api_key])
        if is_production and not has_cloud_llm:
            errors.append("At least one free cloud LLM API key (GROQ_API_KEY, OPENROUTER_API_KEY, GEMINI_API_KEY) must be configured in production.")

        # In development, warn loudly if fallback to chroma is active
        if self.app_env == AppEnvironment.DEVELOPMENT:
            if self.vector_store_backend == VectorStoreType.CHROMA:
                logger.warning(
                    "\n============================================================\n"
                    "⚠️  [CONFIG WARNING] Operating with local ChromaDB fallback.\n"
                    "    Supabase is bypassed for local development/testing.\n"
                    "============================================================\n"
                )
            elif not self.supabase_url or not (self.supabase_service_role_key or self.supabase_key):
                logger.warning(
                    "\n============================================================\n"
                    "⚠️  [CONFIG WARNING] Supabase configured but keys are missing.\n"
                    "    Automatically falling back to ChromaDB for development.\n"
                    "============================================================\n"
                )
                self.vector_store_backend = VectorStoreType.CHROMA

        if errors:
            error_message = (
                "\n" + "=" * 70 + "\n"
                "🚨 FATAL CONFIGURATION ERROR - STARTUP ABORTED\n"
                + "=" * 70 + "\n"
                + "\n".join(f"  • {e}" for e in errors)
                + "\n" + "=" * 70
            )
            raise ValueError(error_message)

        return self


# Global singleton settings instance
try:
    settings = Settings()
except Exception as e:
    if os.environ.get("APP_ENV") == "production":
        raise e
    settings = Settings(APP_ENV=AppEnvironment.DEVELOPMENT)
