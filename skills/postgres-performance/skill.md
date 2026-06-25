# Skill: PostgreSQL Performance — Official Patterns
# Source: postgresql.org/docs/current/performance-tips.html

## Indexing Rules
- Index every foreign key column and every column used in WHERE/ORDER BY/GROUP BY.
- Partial index for hot subsets: `CREATE INDEX ON orders(user_id) WHERE status='pending'`
- GIN index for full-text search, JSONB operators: `CREATE INDEX ON docs USING gin(content)`
- `EXPLAIN (ANALYZE, BUFFERS)` — always check query plan before shipping a query.
- Avoid `SELECT *` — fetch only needed columns; allows index-only scans.

## pgvector (ANN Search)
```sql
-- IVFFlat: fast approximate, good for > 100k rows
CREATE INDEX ON items USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Query: nearest-neighbor
SELECT id, 1 - (embedding <=> '[0.1, 0.2, ...]') AS similarity
FROM items
ORDER BY embedding <=> '[0.1, 0.2, ...]'
LIMIT 10;
```
Tune `lists`: `sqrt(num_rows)`. Set `ivfflat.probes` higher for accuracy vs speed.

## Connection Pooling
- Use PgBouncer (transaction mode) in front of Postgres — never create unlimited connections.
- App should use `asyncpg` (async) or `psycopg3` (sync/async). Never `psycopg2` in async context.
- Max connections rule: `(num_cores × 2) + effective_disk_count`.

## Queries
```sql
-- Use CTEs for readability, not performance (PostgreSQL inlines them)
WITH recent AS (SELECT * FROM events WHERE ts > now() - interval '7 days')
SELECT user_id, count(*) FROM recent GROUP BY user_id;

-- Batch upsert (avoid row-by-row inserts)
INSERT INTO users (id, name) VALUES (...) ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;

-- RETURNING avoids a round-trip
INSERT INTO items (name) VALUES ('x') RETURNING id;
```

## Maintenance
- `VACUUM ANALYZE table` after bulk writes.
- `pg_stat_user_tables` — track `seq_scan` vs `idx_scan` to find missing indexes.
- `pg_stat_statements` — find slow queries by `mean_exec_time`.
