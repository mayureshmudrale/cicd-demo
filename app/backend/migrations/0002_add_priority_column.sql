-- Adds a priority flag so ideas can be sorted by importance, not just
-- recency. Backfill is expected to run separately before this ships.
ALTER TABLE ideas ADD COLUMN priority INTEGER NOT NULL;
