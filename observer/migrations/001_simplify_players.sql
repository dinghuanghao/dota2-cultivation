-- Migration script to preserve personaname and simplify players table
PRAGMA foreign_keys=off;

-- Create new table
CREATE TABLE players_new (
    account_id INTEGER PRIMARY KEY,
    personaname TEXT,
    match_ids JSON
);

-- Only try to copy data if old table exists and has the expected columns
INSERT OR IGNORE INTO players_new (account_id, personaname, match_ids)
SELECT p.account_id, 
       COALESCE(p.profile_name, 'Unknown') as personaname,
       p.match_ids
FROM sqlite_master m
JOIN players p
WHERE m.type = 'table' 
AND m.name = 'players'
AND EXISTS (
    SELECT 1 FROM pragma_table_info('players') 
    WHERE name = 'profile_name'
);

-- Drop old table if it exists
DROP TABLE IF EXISTS players;

-- Rename new table
ALTER TABLE players_new RENAME TO players;

PRAGMA foreign_keys=on;
