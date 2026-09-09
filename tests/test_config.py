"""
Tests for SWAYAMBHU v2 Startup Configuration and Fail-Fast Enforcement
"""

import os
import pytest
from config import AppEnvironment, Settings, VectorStoreType


def test_development_allows_chroma_fallback():
    """Development environment should permit local ChromaDB without remote keys."""
    dev_settings = Settings(
        APP_ENV=AppEnvironment.DEVELOPMENT,
        VECTOR_STORE_BACKEND=VectorStoreType.CHROMA,
        SUPABASE_URL=None,
        SUPABASE_KEY=None,
    )
    assert dev_settings.app_env == AppEnvironment.DEVELOPMENT
    assert dev_settings.vector_store_backend == VectorStoreType.CHROMA


def test_production_fails_fast_without_supabase():
    """Production environment must raise a fatal error if Supabase credentials are missing."""
    with pytest.raises(ValueError, match="FATAL CONFIGURATION ERROR"):
        Settings(
            APP_ENV=AppEnvironment.PRODUCTION,
            SUPABASE_URL=None,
            SUPABASE_SERVICE_ROLE_KEY=None,
            VECTOR_STORE_BACKEND=VectorStoreType.SUPABASE,
        )


def test_production_fails_fast_on_silent_chroma_fallback():
    """Production environment must reject ChromaDB unless explicitly overridden."""
    with pytest.raises(ValueError, match="VECTOR_STORE_BACKEND cannot be 'chroma' in production"):
        Settings(
            APP_ENV=AppEnvironment.PRODUCTION,
            SUPABASE_URL="https://example.supabase.co",
            SUPABASE_SERVICE_ROLE_KEY="secret-key-prod",
            VECTOR_STORE_BACKEND=VectorStoreType.CHROMA,
            ALLOW_INSECURE_LOCAL_VECTOR_IN_PROD=False,
            GROQ_API_KEY="dummy-groq-key",
        )


def test_production_succeeds_with_valid_config():
    """Production environment initializes cleanly when all credentials are provided."""
    prod_settings = Settings(
        APP_ENV=AppEnvironment.PRODUCTION,
        SUPABASE_URL="https://example.supabase.co",
        SUPABASE_SERVICE_ROLE_KEY="secret-key-prod",
        VECTOR_STORE_BACKEND=VectorStoreType.SUPABASE,
        GROQ_API_KEY="valid-groq-key",
    )
    assert prod_settings.app_env == AppEnvironment.PRODUCTION
    assert prod_settings.supabase_url == "https://example.supabase.co"
