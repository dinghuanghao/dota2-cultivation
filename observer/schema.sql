CREATE TABLE IF NOT EXISTS matches (
    match_id INTEGER PRIMARY KEY,
    start_time INTEGER NOT NULL,
    duration INTEGER NOT NULL,
    game_mode INTEGER NOT NULL,
    game_mode_name TEXT,
    lobby_type INTEGER NOT NULL DEFAULT 0,
    lobby_type_name TEXT,
    leagueid INTEGER NOT NULL DEFAULT 0,
    radiant_win BOOLEAN NOT NULL,
    radiant_score INTEGER NOT NULL,
    match_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS players(
    account_id INTEGER PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_profile_update TIMESTAMP,
    active BOOLEAN DEFAULT TRUE,
    profile_name TEXT,
    avatar_url TEXT,
    rank_tier INTEGER,
    leaderboard_rank INTEGER,
    profile_data JSON,
    match_ids JSON
);

-- Create indexes after tables
CREATE INDEX IF NOT EXISTS idx_players_profile_name 
ON players(profile_name);

CREATE INDEX IF NOT EXISTS idx_matches_game_mode 
ON matches(game_mode);

CREATE INDEX IF NOT EXISTS idx_matches_lobby_type 
ON matches(lobby_type);

CREATE INDEX IF NOT EXISTS idx_matches_start_time 
ON matches(start_time DESC);
