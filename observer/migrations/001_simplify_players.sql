-- Migration script to preserve personaname and simplify players table
PRAGMA foreign_keys=off;

-- Drop any leftover tables from failed migrations
DROP TABLE IF EXISTS players_new;
DROP TABLE IF EXISTS players;

-- Create new table with simplified schema
CREATE TABLE players (
    account_id INTEGER PRIMARY KEY,
    personaname TEXT,
    match_ids JSON
);

PRAGMA foreign_keys=on;
