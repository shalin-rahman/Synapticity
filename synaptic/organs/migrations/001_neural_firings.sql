-- ============================================================================
-- Synapticity — Hippocampus Migration 001
-- Table: neural_firings
-- Purpose: Long-Term Potentiation storage for agent reflections and fixes.
--          pgvector enables semantic nearest-neighbour lookup so every new
--          mission benefits from every past successful repair cycle.
--
-- Run this in the Supabase SQL editor (or via supabase db push).
-- ============================================================================

-- Enable the pgvector extension (once per database)
CREATE EXTENSION IF NOT EXISTS vector;

-- ── Primary table ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS neural_firings (
    id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id       TEXT        NOT NULL,
    agent_name       TEXT        NOT NULL,
    -- Open enum: 'fix' | 'insight' | 'pattern' | 'audit' |
    --            'architecture' | 'security_finding'
    reflection_type  TEXT        NOT NULL,
    content          TEXT        NOT NULL,
    -- Gemini text-embedding-004 produces 768-dim vectors
    embedding        VECTOR(768),
    metadata         JSONB       NOT NULL DEFAULT '{}',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for fast chronological queries per mission
CREATE INDEX IF NOT EXISTS idx_neural_firings_mission
    ON neural_firings (mission_id, created_at DESC);

-- Index for filtering by reflection type
CREATE INDEX IF NOT EXISTS idx_neural_firings_type
    ON neural_firings (reflection_type);

-- IVFFlat index for ANN vector search (cosine distance)
-- lists=100 is appropriate for up to ~1M rows; tune as data grows
CREATE INDEX IF NOT EXISTS idx_neural_firings_embedding
    ON neural_firings USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- ── Row Level Security ────────────────────────────────────────────────────────
-- Agents authenticated with the anon key can only read rows whose mission_id
-- matches their JWT claim. Even a hallucinated DELETE cannot touch another
-- mission's data.

ALTER TABLE neural_firings ENABLE ROW LEVEL SECURITY;

-- Read: agents see only their own mission namespace
CREATE POLICY "agents_select_own_mission" ON neural_firings
    FOR SELECT
    USING (mission_id = current_setting('app.mission_id', true));

-- Insert: agents may potentiate new memories into their own namespace
CREATE POLICY "agents_insert_own_mission" ON neural_firings
    FOR INSERT
    WITH CHECK (mission_id = current_setting('app.mission_id', true));

-- Delete / Update: blocked for all anon-key callers — only service-role can
-- Omitting UPDATE/DELETE policies means they are denied by default under RLS.

-- ── RPC functions for semantic search ────────────────────────────────────────

-- Unfiltered: returns the top-k most similar neural firings across all types
CREATE OR REPLACE FUNCTION match_neural_firings(
    query_embedding  VECTOR(768),
    match_count      INT DEFAULT 5
)
RETURNS TABLE (
    id               UUID,
    mission_id       TEXT,
    agent_name       TEXT,
    reflection_type  TEXT,
    content          TEXT,
    similarity       FLOAT,
    metadata         JSONB
)
LANGUAGE SQL STABLE
AS $$
    SELECT
        id,
        mission_id,
        agent_name,
        reflection_type,
        content,
        1 - (embedding <=> query_embedding) AS similarity,
        metadata
    FROM neural_firings
    ORDER BY embedding <=> query_embedding
    LIMIT match_count;
$$;

-- Typed: narrows search to a specific reflection_type (e.g. 'fix')
CREATE OR REPLACE FUNCTION match_neural_firings_typed(
    query_embedding  VECTOR(768),
    match_count      INT DEFAULT 5,
    filter_type      TEXT DEFAULT 'fix'
)
RETURNS TABLE (
    id               UUID,
    mission_id       TEXT,
    agent_name       TEXT,
    reflection_type  TEXT,
    content          TEXT,
    similarity       FLOAT,
    metadata         JSONB
)
LANGUAGE SQL STABLE
AS $$
    SELECT
        id,
        mission_id,
        agent_name,
        reflection_type,
        content,
        1 - (embedding <=> query_embedding) AS similarity,
        metadata
    FROM neural_firings
    WHERE reflection_type = filter_type
    ORDER BY embedding <=> query_embedding
    LIMIT match_count;
$$;
