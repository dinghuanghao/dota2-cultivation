"""Data models for the Dota 2 match observer."""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime, date


@dataclass
class Match:
    """Represents a Dota 2 match."""
    match_id: int
    start_time: int
    duration: int
    game_mode: int
    game_mode_name: Optional[str] = None
    lobby_type: int = 0
    leagueid: int = 0
    radiant_win: bool = False
    radiant_score: int = 0
    match_data: Optional[dict] = None


@dataclass
class QueueItem:
    """Represents a match in the processing queue."""
    match_id: int
    added_at: float
    retry_count: int = 0
    last_retry: Optional[float] = None
    priority: int = 0  # Higher = more priority


@dataclass
class Player:
    """Represents a monitored player."""
    account_id: int
    personaname: Optional[str] = None
    match_ids: Optional[List[int]] = None
