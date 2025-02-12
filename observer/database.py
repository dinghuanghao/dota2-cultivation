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
            
            # Try to update existing player first
            cursor.execute(
                """UPDATE players 
                SET profile_name = ?,
                    avatar_url = ?,
                    rank_tier = ?,
                    leaderboard_rank = ?,
                    profile_data = ?,
                    updated_at = ?,
                    active = TRUE
                WHERE account_id = ?""",
                (
                    profile.get("personaname"),
                    profile.get("avatarfull"),
                    player_info.get("rank_tier"),
                    player_info.get("leaderboard_rank"),
                    json.dumps(player_info),
                    datetime.now(),
                    account_id
                )
            )
            
            # If no rows were updated, insert new player
            if cursor.rowcount == 0:
                cursor.execute(
                    """INSERT INTO players (
                        account_id, profile_name, avatar_url, rank_tier,
                        leaderboard_rank, profile_data
                    ) VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        account_id,
                        profile.get("personaname"),
                        profile.get("avatarfull"),
                        player_info.get("rank_tier"),
                        player_info.get("leaderboard_rank"),
                        json.dumps(player_info)
                    )
                )
            
            conn.commit()
            return self.get_player(account_id)

    def get_player(self, account_id: int) -> Optional[Player]:
        """Get a player by account ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM players WHERE account_id = ?",
                (account_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
                
            data = dict(row)
            if data.get('profile_data'):
                data['profile_data'] = json.loads(data['profile_data'])
            return Player(**data)

    def get_active_players(self) -> List[Player]:
        """Get all active players."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM players WHERE active = TRUE")
            players = []
            for row in cursor.fetchall():
                data = dict(row)
                if data.get('profile_data'):
                    data['profile_data'] = json.loads(data['profile_data'])
                players.append(Player(**data))
            return players

    def remove_player(self, account_id: int):
        """Soft delete a player."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE players 
                SET active = FALSE, 
                    updated_at = ?
                WHERE account_id = ?""",
                (datetime.now(), account_id)
            )
            conn.commit()

    def update_player_profile(self, account_id: int, player_info: Dict[str, Any]):
        """Update player profile information."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            profile = player_info.get("profile", {})
            cursor.execute(
                """UPDATE players 
                SET profile_name = ?,
                    avatar_url = ?,
                    rank_tier = ?,
                    leaderboard_rank = ?,
                    profile_data = ?,
                    last_profile_update = ?,
                    updated_at = ?
                WHERE account_id = ?""",
                (
                    profile.get("personaname"),
                    profile.get("avatarfull"),
                    player_info.get("rank_tier"),
                    player_info.get("leaderboard_rank"),
                    json.dumps(player_info),
                    datetime.now(),
                    datetime.now(),
                    account_id
                )
            )
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
