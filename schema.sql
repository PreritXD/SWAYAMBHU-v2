-- ============================================================================
-- SWAYAMBHU v2: PostgreSQL + pgvector Database Schema
-- Dedicated to Param Pujya Shri Hit Premanand Govind Sharan Ji Maharaj Satsangs
-- Channels: Bhajan Marg (@BhajanMarg) & Sadhan Path (@sadhanpath)
-- ============================================================================

-- 1. Enable pgvector and pgcrypto extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 2. Channels Table
CREATE TABLE IF NOT EXISTS channels (
    id TEXT PRIMARY KEY,                       -- 'bhajan_marg', 'sadhan_path'
    title TEXT NOT NULL,                       -- 'Bhajan Marg', 'Sadhan Path'
    handle TEXT NOT NULL,                      -- '@BhajanMarg', '@sadhanpath'
    youtube_channel_id TEXT,
    description TEXT,
    last_synced_at TIMESTAMPTZ,
    video_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()) NOT NULL
);

-- Seed default channels
INSERT INTO channels (id, title, handle, description)
VALUES 
    ('bhajan_marg', 'Bhajan Marg', '@BhajanMarg', 'Official Bhajan Marg YouTube channel containing Ekantik Vartalaap and discourse archives.'),
    ('sadhan_path', 'Sadhan Path', '@sadhanpath', 'Sadhan Path YouTube channel featuring daily spiritual guidance and Naam Jap satsangs.')
ON CONFLICT (id) DO UPDATE 
SET title = EXCLUDED.title, handle = EXCLUDED.handle, description = EXCLUDED.description;

-- 3. Videos Table (Channel-aware with deduplication tracking)
CREATE TABLE IF NOT EXISTS videos (
    video_id TEXT PRIMARY KEY,                 -- YouTube 11-char ID
    channel_id TEXT NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    upload_date DATE,
    duration_seconds INTEGER,
    view_count BIGINT,
    description TEXT,
    transcript_language TEXT DEFAULT 'hi',
    transcription_model TEXT DEFAULT 'youtube_captions' NOT NULL,
    is_duplicate BOOLEAN DEFAULT FALSE NOT NULL,
    canonical_video_id TEXT REFERENCES videos(video_id) ON DELETE SET NULL,
    dedup_similarity_score FLOAT,
    indexed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_videos_channel ON videos(channel_id);
CREATE INDEX IF NOT EXISTS idx_videos_upload_date ON videos(upload_date DESC);
CREATE INDEX IF NOT EXISTS idx_videos_is_duplicate ON videos(is_duplicate);
CREATE INDEX IF NOT EXISTS idx_videos_canonical ON videos(canonical_video_id);
CREATE INDEX IF NOT EXISTS idx_videos_transcription_model ON videos(transcription_model);

-- 4. Transcript Chunks Table (Sliding-window segments with 384-dim embeddings)
CREATE TABLE IF NOT EXISTS transcript_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id TEXT NOT NULL REFERENCES videos(video_id) ON DELETE CASCADE,
    channel_id TEXT NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    start_sec INTEGER NOT NULL,
    end_sec INTEGER NOT NULL,
    start_formatted TEXT NOT NULL,            -- e.g. "01:25" or "01:14:20"
    end_formatted TEXT NOT NULL,              -- e.g. "02:15"
    raw_text TEXT NOT NULL,                   -- verbatim transcript segment
    clean_text TEXT NOT NULL,                 -- normalized Hindi without fillers
    token_count INTEGER,
    embedding VECTOR(384) NOT NULL,           -- paraphrase-multilingual-MiniLM-L12-v2
    embedding_model TEXT DEFAULT 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2' NOT NULL,
    is_duplicate BOOLEAN DEFAULT FALSE NOT NULL,
    canonical_chunk_id UUID REFERENCES transcript_chunks(id) ON DELETE SET NULL,
    canonical_video_id TEXT REFERENCES videos(video_id) ON DELETE SET NULL,
    cross_channel_aliases JSONB DEFAULT '[]'::JSONB, -- [{"channel": "sadhan_path", "video_id": "...", "timestamp": "02:15"}]
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_chunks_video ON transcript_chunks(video_id);
CREATE INDEX IF NOT EXISTS idx_chunks_channel ON transcript_chunks(channel_id);
CREATE INDEX IF NOT EXISTS idx_chunks_is_duplicate ON transcript_chunks(is_duplicate);
CREATE INDEX IF NOT EXISTS idx_chunks_canonical ON transcript_chunks(canonical_chunk_id);

-- 5. ANN HNSW Vector Index for High-Throughput Cosine Similarity Search
-- m = 16: bi-directional links per node
-- ef_construction = 64: search radius during index construction
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw 
ON transcript_chunks 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);

-- 6. Query Logs Table (Structured analytics, latency, retrieval telemetry)
CREATE TABLE IF NOT EXISTS query_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_query TEXT NOT NULL,
    normalized_query TEXT,
    rewritten_query TEXT,
    ip_address TEXT,
    retrieved_chunk_ids JSONB,
    source_channels_retrieved TEXT[],
    rerank_scores JSONB,
    latency_ms INTEGER,
    llm_provider TEXT,
    llm_model TEXT,
    answered BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_query_logs_created ON query_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_query_logs_answered ON query_logs(answered);

-- 7. Feedback Table (User quality ratings and flagged responses)
CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query TEXT NOT NULL,
    answer TEXT NOT NULL,
    flagged BOOLEAN NOT NULL,
    note TEXT,
    ip_address TEXT,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_feedback_flagged ON feedback(flagged);
CREATE INDEX IF NOT EXISTS idx_feedback_created ON feedback(created_at DESC);

-- 8. Sync Status Table (Scheduled Ingestion Monitoring)
CREATE TABLE IF NOT EXISTS sync_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id TEXT NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    last_sync_started_at TIMESTAMPTZ NOT NULL,
    last_sync_completed_at TIMESTAMPTZ,
    videos_found INTEGER DEFAULT 0,
    videos_ingested INTEGER DEFAULT 0,
    status TEXT NOT NULL,                     -- 'in_progress', 'completed', 'failed'
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sync_status_channel ON sync_status(channel_id);
CREATE INDEX IF NOT EXISTS idx_sync_status_started ON sync_status(last_sync_started_at DESC);

-- ============================================================================
-- 9. Match Function for Supabase pgvector RPC
-- Filters duplicates and performs cosine similarity search
-- ============================================================================
CREATE OR REPLACE FUNCTION match_transcript_chunks(
    query_embedding VECTOR(384),
    match_threshold FLOAT DEFAULT 0.35,
    match_count INT DEFAULT 8,
    filter_channel TEXT DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    video_id TEXT,
    channel_id TEXT,
    chunk_index INT,
    start_sec INT,
    end_sec INT,
    start_formatted TEXT,
    end_formatted TEXT,
    raw_text TEXT,
    clean_text TEXT,
    embedding_model TEXT,
    similarity FLOAT,
    cross_channel_aliases JSONB
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT
        tc.id,
        tc.video_id,
        tc.channel_id,
        tc.chunk_index,
        tc.start_sec,
        tc.end_sec,
        tc.start_formatted,
        tc.end_formatted,
        tc.raw_text,
        tc.clean_text,
        tc.embedding_model,
        1 - (tc.embedding <=> query_embedding) AS similarity,
        tc.cross_channel_aliases
    FROM transcript_chunks tc
    WHERE 
        tc.is_duplicate = FALSE
        AND (filter_channel IS NULL OR tc.channel_id = filter_channel)
        AND 1 - (tc.embedding <=> query_embedding) >= match_threshold
    ORDER BY tc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ============================================================================
-- 10. Row Level Security (RLS) Configuration
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE channels ENABLE ROW LEVEL SECURITY;
ALTER TABLE videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE transcript_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE query_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE sync_status ENABLE ROW LEVEL SECURITY;

-- Channels: Anyone can read channels
CREATE POLICY "Public channels viewable by all" ON channels
    FOR SELECT USING (true);

-- Videos: Anyone can read non-duplicate videos
CREATE POLICY "Public videos viewable by all" ON videos
    FOR SELECT USING (is_duplicate = false);

-- Transcript Chunks: Anyone can read non-duplicate chunks
CREATE POLICY "Public chunks viewable by all" ON transcript_chunks
    FOR SELECT USING (is_duplicate = false);

-- Query Logs: Anon can insert query telemetry
CREATE POLICY "Anon can insert query logs" ON query_logs
    FOR INSERT WITH CHECK (true);

-- Feedback: Anon can submit feedback
CREATE POLICY "Anon can insert feedback" ON feedback
    FOR INSERT WITH CHECK (true);

-- Sync Status: Read-only to authenticated/service role
CREATE POLICY "Public sync status viewable by all" ON sync_status
    FOR SELECT USING (true);

-- Service Role full access policies (for backend ingestion and admin operations)
CREATE POLICY "Service role full access channels" ON channels
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role full access videos" ON videos
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role full access transcript_chunks" ON transcript_chunks
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role full access query_logs" ON query_logs
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role full access feedback" ON feedback
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role full access sync_status" ON sync_status
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');
