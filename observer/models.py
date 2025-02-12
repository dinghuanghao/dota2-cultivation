"""Data models for the Dota 2 match observer."""
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, date


@dataclass
class Match:
    """Represents a Dota 2 match."""
    match_id: int
    start_time: int
    duration: int
    game_mode: int
    radiant_win: bool
    radiant_score: int
    dire_score: int


@dataclass
class PlayerMatch:
    """Represents a player's performance in a match."""
    match_id: int
    account_id: int
    hero_id: int
    player_slot: int
    kills: int
    deaths: int
    assists: int
    gold_per_min: int
    xp_per_min: int
    last_hits: int
    denies: int


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
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    active: bool = True
