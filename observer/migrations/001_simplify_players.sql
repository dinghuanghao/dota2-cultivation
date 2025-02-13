-- Migration script to preserve personaname and simplify players table
CREATE TABLE IF NOT EXISTS players_new (
    account_id INTEGER PRIMARY KEY,
    personaname TEXT,
    match_ids JSON
);

-- Copy data if old table exists
INSERT OR IGNORE INTO players_new (account_id, personaname, match_ids)
SELECT account_id, COALESCE(profile_name, 'Unknown'), match_ids
FROM players
WHERE EXISTS (
    SELECT 1 FROM sqlite_master 
    WHERE type='table' AND name='players'
);

-- Drop old table if it exists
DROP TABLE IF EXISTS players;

-- Rename new table to players
ALTER TABLE players_new RENAME TO players;
