"""Database API for external modules."""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from .database import Database
from .models import Player, Match, PlayerMatch
from .config import Config


class DatabaseAPI:
    """API for accessing the Dota 2 match database."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the database API."""
        config = Config()
        self.db = Database(db_path or config.DATABASE_PATH)
    
    def add_player(self, account_id: int, player_info: Dict[str, Any]) -> Player:
        """Add a player to monitor.
        
        Args:
            account_id: The player's account ID
            player_info: Player profile information from OpenDota API
            
        Returns:
            Player object with the added player's information
        """
        return self.db.add_player(account_id, player_info)
    
    def remove_player(self, account_id: int) -> None:
        """Remove a player from monitoring.
        
        This sets the player's active status to False but preserves their match data.
        
        Args:
            account_id: The player's account ID
        """
        self.db.remove_player(account_id)
    
    def get_player_matches(
        self, 
        account_id: int, 
        start_time: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get matches for a player.
        
        Args:
            account_id: The player's account ID
            start_time: Optional Unix timestamp. If provided, only returns matches
                       after this time.
                       
        Returns:
            List of match dictionaries containing:
            - match_id: Match ID
            - start_time: Match start time (Unix timestamp)
            - duration: Match duration in seconds
            - game_mode: Game mode ID
            - hero_id: Hero ID used by the player
            - kills: Player's kills
            - deaths: Player's deaths
            - assists: Player's assists
            - gold_per_min: Player's gold per minute
            - xp_per_min: Player's experience per minute
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    m.match_id,
                    m.start_time,
                    m.duration,
                    m.game_mode,
                    m.radiant_win,
                    pm.hero_id,
                    pm.kills,
                    pm.deaths,
                    pm.assists,
                    pm.gold_per_min,
                    pm.xp_per_min
                FROM matches m
                JOIN player_matches pm ON m.match_id = pm.match_id
                WHERE pm.account_id = ?
            """
            params = [account_id]
            
            if start_time is not None:
                query += " AND m.start_time >= ?"
                params.append(start_time)
                
            query += " ORDER BY m.start_time DESC"
            
            cursor.execute(query, params)
            matches = []
            for row in cursor.fetchall():
                matches.append({
                    'match_id': row['match_id'],
                    'start_time': row['start_time'],
                    'duration': row['duration'],
                    'game_mode': row['game_mode'],
                    'radiant_win': bool(row['radiant_win']),
                    'hero_id': row['hero_id'],
                    'kills': row['kills'],
                    'deaths': row['deaths'],
                    'assists': row['assists'],
                    'gold_per_min': row['gold_per_min'],
                    'xp_per_min': row['xp_per_min']
                })
            return matches
