"""Database API for external modules.

Example usage:
    api = DatabaseAPI()
    
    # Add a player
    api.add_player(123456789, player_info)
    
    # Get recent matches
    matches = api.get_player_matches(
        123456789,
        start_time=int(time.time()) - 30*24*60*60  # Last 30 days
    )
    
    # Get filtered matches
    filtered = api.get_player_matches_filtered(
        123456789,
        game_mode=1,  # All Pick
        hero_id=1     # Anti-Mage
    )
    
    # Remove player
    api.remove_player(123456789)  # Preserves match history
"""
import time
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from .database import Database
from .models import Player, Match
from .config import Config


class DatabaseAPI:
    """API for accessing the Dota 2 match database."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the database API."""
        config = Config()
        self.db = Database(db_path or config.DATABASE_PATH)
        
    def _validate_account_id(self, account_id: int) -> None:
        """Validate account ID."""
        if not isinstance(account_id, int):
            raise ValueError("account_id must be an integer")
        if account_id <= 0:
            raise ValueError("account_id must be positive")
            
    def _validate_pagination(
        self,
        limit: Optional[int],
        offset: Optional[int]
    ) -> None:
        """Validate pagination parameters."""
        if limit is not None and limit <= 0:
            raise ValueError("limit must be positive")
        if offset is not None and offset < 0:
            raise ValueError("offset must be non-negative")
    
    def add_player(self, account_id: int, player_info: Dict[str, Any]) -> Player:
        """Add a player to monitor.
        
        Args:
            account_id: The player's account ID
            player_info: Player profile information from OpenDota API
            
        Returns:
            Player object with the added player's information
            
        Raises:
            ValueError: If account_id is invalid
        """
        self._validate_account_id(account_id)
        return self.db.add_player(account_id, player_info)
    
    def remove_player(self, account_id: int) -> None:
        """Remove a player from monitoring.
        
        This removes the player from monitoring.
        
        Args:
            account_id: The player's account ID
            
        Raises:
            ValueError: If account_id is invalid
        """
        self._validate_account_id(account_id)
        self.db.remove_player(account_id)
    
    def get_player_matches(
        self, 
        account_id: int, 
        start_time: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get matches for a player with pagination.
        
        Args:
            account_id: The player's account ID
            start_time: Optional Unix timestamp. If provided, only returns matches
                       after this time.
            limit: Maximum number of matches to return
            offset: Number of matches to skip
            
        Returns:
            Dictionary containing:
            - total: Total number of matches
            - matches: List of match dictionaries
            
        Raises:
            ValueError: If account_id is invalid or pagination parameters are invalid
        """
        self._validate_account_id(account_id)
        self._validate_pagination(limit, offset)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get total count
            count_query = """
                SELECT COUNT(*) as total
                FROM matches m, json_each(m.match_data, '$.players') as p
                WHERE json_extract(p.value, '$.account_id') = ?
            """
            count_params = [account_id]
            
            if start_time is not None:
                count_query += " AND m.start_time >= ?"
                count_params.append(start_time)
                
            cursor.execute(count_query, count_params)
            total = cursor.fetchone()['total']
            
            # Get matches
            query = """
                SELECT 
                    m.match_id,
                    m.start_time,
                    m.duration,
                    m.game_mode,
                    m.radiant_win,
                    json_extract(p.value, '$.hero_id') as hero_id,
                    json_extract(p.value, '$.kills') as kills,
                    json_extract(p.value, '$.deaths') as deaths,
                    json_extract(p.value, '$.assists') as assists,
                    json_extract(p.value, '$.gold_per_min') as gold_per_min,
                    json_extract(p.value, '$.xp_per_min') as xp_per_min
                FROM matches m, json_each(m.match_data, '$.players') as p
                WHERE json_extract(p.value, '$.account_id') = ?
            """
            params = [account_id]
            
            if start_time is not None:
                query += " AND m.start_time >= ?"
                params.append(start_time)
                
            query += " ORDER BY m.start_time DESC"
            
            if limit is not None:
                query += " LIMIT ?"
                params.append(limit)
                
            if offset is not None:
                query += " OFFSET ?"
                params.append(offset)
            
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
            
            return {
                'total': total,
                'matches': matches
            }

    def get_player_matches_filtered(
        self,
        account_id: int,
        start_time: Optional[int] = None,
        game_mode: Optional[int] = None,
        hero_id: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get filtered matches for a player with pagination.
        
        Args:
            account_id: The player's account ID
            start_time: Optional Unix timestamp
            game_mode: Optional game mode ID to filter by
            hero_id: Optional hero ID to filter by
            limit: Maximum number of matches to return
            offset: Number of matches to skip
            
        Returns:
            Dictionary containing:
            - total: Total number of matches matching filters
            - matches: List of filtered match dictionaries
            
        Raises:
            ValueError: If account_id is invalid or pagination parameters are invalid
        """
        self._validate_account_id(account_id)
        self._validate_pagination(limit, offset)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Build WHERE clause and params
            where_clauses = ["pm.account_id = ?"]
            params = [account_id]
            
            if start_time is not None:
                where_clauses.append("m.start_time >= ?")
                params.append(start_time)
                
            if game_mode is not None:
                where_clauses.append("m.game_mode = ?")
                params.append(game_mode)
                
            if hero_id is not None:
                where_clauses.append("pm.hero_id = ?")
                params.append(hero_id)
                
            where_clause = " AND ".join(where_clauses)
            
            # Get total count
            count_query = f"""
                SELECT COUNT(*) as total
                FROM matches m, json_each(m.match_data, '$.players') as p
                WHERE json_extract(p.value, '$.account_id') = ?
            """
            if start_time is not None:
                count_query += " AND m.start_time >= ?"
            if game_mode is not None:
                count_query += " AND m.game_mode = ?"
            if hero_id is not None:
                count_query += " AND CAST(json_extract(p.value, '$.hero_id') AS INTEGER) = ?"
            
            cursor.execute(count_query, params)
            total = cursor.fetchone()['total']
            
            # Get matches
            query = f"""
                SELECT 
                    m.match_id,
                    m.start_time,
                    m.duration,
                    m.game_mode,
                    m.radiant_win,
                    json_extract(p.value, '$.hero_id') as hero_id,
                    json_extract(p.value, '$.kills') as kills,
                    json_extract(p.value, '$.deaths') as deaths,
                    json_extract(p.value, '$.assists') as assists,
                    json_extract(p.value, '$.gold_per_min') as gold_per_min,
                    json_extract(p.value, '$.xp_per_min') as xp_per_min
                FROM matches m, json_each(m.match_data, '$.players') as p
                WHERE json_extract(p.value, '$.account_id') = ?
            """
            if start_time is not None:
                query += " AND m.start_time >= ?"
            if game_mode is not None:
                query += " AND m.game_mode = ?"
            if hero_id is not None:
                query += " AND CAST(json_extract(p.value, '$.hero_id') AS INTEGER) = ?"
            query += " ORDER BY m.start_time DESC"
            
            if limit is not None:
                query += " LIMIT ?"
                params.append(limit)
                
            if offset is not None:
                query += " OFFSET ?"
                params.append(offset)
            
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
            
            return {
                'total': total,
                'matches': matches
            }
