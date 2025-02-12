CREATE TABLE IF NOT EXISTS matches (
    match_id INTEGER PRIMARY KEY,
    start_time INTEGER NOT NULL,
    duration INTEGER NOT NULL,
    game_mode INTEGER NOT NULL,
    radiant_win BOOLEAN NOT NULL,
    radiant_score INTEGER NOT NULL,
    dire_score INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS player_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,
    hero_id INTEGER NOT NULL,
    player_slot INTEGER NOT NULL,
    kills INTEGER NOT NULL,
    deaths INTEGER NOT NULL,
    assists INTEGER NOT NULL,
    gold_per_min INTEGER NOT NULL,
    xp_per_min INTEGER NOT NULL,
    last_hits INTEGER NOT NULL,
    denies INTEGER NOT NULL,
    FOREIGN KEY (match_id) REFERENCES matches(match_id),
    UNIQUE(match_id, account_id)
);

CREATE INDEX IF NOT EXISTS idx_player_matches_account 
ON player_matches(account_id);
