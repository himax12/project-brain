# Project Brain schema — Phase 1
# CockroachDB. VECTOR index: add after confirming version-specific DDL.

CREATE TABLE IF NOT EXISTS memories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id STRING NOT NULL,
  repo_id STRING NOT NULL,
  statement STRING NOT NULL,
  rationale STRING NULL,
  category STRING NULL,
  tags STRING[] NULL,
  polarity STRING NOT NULL DEFAULT 'must',
  status STRING NOT NULL DEFAULT 'pending_review',
  importance FLOAT8 NOT NULL DEFAULT 0.5,
  confidence FLOAT8 NOT NULL DEFAULT 0.8,
  source STRING NOT NULL DEFAULT 'user',
  supersedes_id UUID NULL,
  embedding VECTOR(1024) NULL,
  provenance JSONB NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  invalid_at TIMESTAMPTZ NULL,
  CONSTRAINT memories_polarity_check CHECK (polarity IN ('must', 'must_not', 'advisory')),
  CONSTRAINT memories_status_check CHECK (
    status IN ('pending_review', 'active', 'rejected', 'superseded')
  ),
  CONSTRAINT memories_source_check CHECK (
    source IN ('user', 'bedrock_extract', 'pr_webhook')
  )
);

CREATE INDEX IF NOT EXISTS memories_scope_status_idx
  ON memories (org_id, repo_id, status);

CREATE INDEX IF NOT EXISTS memories_pending_idx
  ON memories (org_id, repo_id)
  WHERE status = 'pending_review';

CREATE TABLE IF NOT EXISTS memory_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  memory_id UUID NULL,
  org_id STRING NOT NULL,
  repo_id STRING NOT NULL,
  event_type STRING NOT NULL,
  actor STRING NULL,
  payload JSONB NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS memory_events_memory_idx
  ON memory_events (memory_id);

CREATE TABLE IF NOT EXISTS chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id STRING NOT NULL,
  repo_id STRING NOT NULL,
  session_id STRING NOT NULL,
  role STRING NOT NULL DEFAULT 'user',
  content STRING NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS chat_messages_scope_idx
  ON chat_messages (org_id, repo_id, session_id);
