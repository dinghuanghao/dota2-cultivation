CREATE TABLE IF NOT EXISTS matches (
    match_id INTEGER PRIMARY KEY,
    start_time INTEGER NOT NULL,
    duration INTEGER NOT NULL,
    game_mode INTEGER NOT NULL,
    game_mode_name TEXT,
    lobby_type INTEGER NOT NULL DEFAULT 0,
    leagueid INTEGER NOT NULL DEFAULT 0,
    radiant_win BOOLEAN NOT NULL,
    radiant_score INTEGER NOT NULL,
    match_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS players(
    account_id INTEGER PRIMARY KEY,
    personaname TEXT,
    match_ids JSON
);

CREATE INDEX IF NOT EXISTS idx_matches_game_mode 
ON matches(game_mode);

CREATE INDEX IF NOT EXISTS idx_matches_lobby_type 
ON matches(lobby_type);

CREATE INDEX IF NOT EXISTS idx_matches_start_time 
ON matches(start_time DESC);
