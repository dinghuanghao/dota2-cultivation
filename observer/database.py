"""Database operations for the Dota 2 match observer."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
import logging
from typing import Optional, Dict, Any

from .models import Match, PlayerMatch


class Database:
    """Handles all database operations."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_db()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Initialize the database with schema."""
        try:
            schema_path = Path(__file__).parent / 'schema.sql'
            with open(schema_path) as f:
                schema = f.read()
            with self.get_connection() as conn:
                conn.executescript(schema)
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise

    def is_match_stored(self, match_id: int) -> bool:
        """Check if a match is already stored."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM matches WHERE match_id = ?", (match_id,))
            return cursor.fetchone() is not None

    def store_match(self, match: Match, player_matches: list[PlayerMatch]):
        """Store a match and its player data."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                # Store match data
                cursor.execute("""
                    INSERT INTO matches (
                        match_id, start_time, duration, game_mode,
                        radiant_win, radiant_score, dire_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    match.match_id, match.start_time, match.duration,
                    match.game_mode, match.radiant_win, match.radiant_score,
                    match.dire_score
                ))

                # Store player match data
                for player_match in player_matches:
                    cursor.execute("""
                        INSERT INTO player_matches (
                            match_id, account_id, hero_id, player_slot,
                            kills, deaths, assists, gold_per_min,
                            xp_per_min, last_hits, denies
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        player_match.match_id, player_match.account_id,
                        player_match.hero_id, player_match.player_slot,
                        player_match.kills, player_match.deaths,
                        player_match.assists, player_match.gold_per_min,
                        player_match.xp_per_min, player_match.last_hits,
                        player_match.denies
                    ))
                conn.commit()
            except Exception as e:
                conn.rollback()
                self.logger.error(f"Failed to store match {match.match_id}: {e}")
                raise
