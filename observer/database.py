"""Database operations for the Dota 2 match observer."""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from .models import Match, Player


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
                
            # Add default player if not exists
            default_account_id = 455681834
            if not self.get_player(default_account_id):
                self.add_player(default_account_id, {})
                self.logger.info(f"Added default player {default_account_id}")
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise

    def is_match_stored(self, match_id: int) -> bool:
        """Check if a match is already stored."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM matches WHERE match_id = ?", (match_id,))
            return cursor.fetchone() is not None

    def add_player(self, account_id: int, player_info: Dict[str, Any]) -> Player:
        """Add or update a player to monitor."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            profile = player_info.get("profile", {})
            personaname = profile.get("personaname", "Unknown")
            
            cursor.execute(
                """INSERT INTO players (account_id, personaname)
                VALUES (?, ?)
                ON CONFLICT(account_id) DO UPDATE SET
                personaname = ?""",
                (account_id, personaname, personaname)
            )
            
            conn.commit()
            return self.get_player(account_id)

    def get_player(self, account_id: int) -> Optional[Player]:
        """Get a player by account ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT account_id, personaname, match_ids FROM players WHERE account_id = ?",
                (account_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return Player(**dict(row))

    def get_active_players(self) -> List[Player]:
        """Get all players."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT account_id, personaname, match_ids FROM players")
            return [Player(**dict(row)) for row in cursor.fetchall()]

    def remove_player(self, account_id: int):
        """Remove a player."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM players WHERE account_id = ?", (account_id,))
            conn.commit()

    def store_match(self, match: Match):
        """Store a match and update player match_ids."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                # Store match data
                cursor.execute("""
                    INSERT INTO matches (
                        match_id, start_time, duration, game_mode,
                        game_mode_name, lobby_type, leagueid,
                        radiant_win, radiant_score, match_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    match.match_id, match.start_time, match.duration,
                    match.game_mode, match.game_mode_name, match.lobby_type,
                    match.leagueid, match.radiant_win,
                    match.radiant_score, json.dumps(match.match_data) if match.match_data else None
                ))

                # Update player match_ids
                for player in match.match_data.get("players", []):
                    account_id = player.get("account_id", 0)
                    if account_id > 0:
                        cursor.execute("""
                            UPDATE players 
                            SET match_ids = json_insert(
                                COALESCE(match_ids, '[]'),
                                '$[' || json_array_length(COALESCE(match_ids, '[]')) || ']',
                                ?
                            )
                            WHERE account_id = ?
                        """, (match.match_id, account_id))

                conn.commit()
            except Exception as e:
                conn.rollback()
                self.logger.error(f"Failed to store match {match.match_id}: {e}")
                raise
