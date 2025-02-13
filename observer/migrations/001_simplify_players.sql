-- Migration script to preserve personaname and simplify players table
ALTER TABLE players ADD COLUMN temp_personaname TEXT;

-- Preserve personaname from either profile_name or profile_data
UPDATE players 
SET temp_personaname = COALESCE(
    profile_name,
    json_extract(profile_data, '$.profile.personaname'),
    'Unknown'
);

-- Create new table with simplified schema
CREATE TABLE players_new (
    account_id INTEGER PRIMARY KEY,
    personaname TEXT,
    match_ids JSON
);

-- Copy data to new table
INSERT INTO players_new 
SELECT account_id, temp_personaname, match_ids 
FROM players;

-- Replace old table
DROP TABLE players;
ALTER TABLE players_new RENAME TO players;
