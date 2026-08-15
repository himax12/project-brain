-- Optional VECTOR index. Apply after 001_schema.sql on clusters that support it.
-- migrate.py applies this file and ignores "already exists / unsupported" errors.

CREATE VECTOR INDEX IF NOT EXISTS memories_embedding_idx ON memories (embedding);
