"""Data models for the Dota 2 match observer."""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime, date


@dataclass
class PickBan:
    """Represents a pick or ban in a match."""
    hero_id: int
    hero_img: str
    order: int
    team: int
    is_pick: bool


@dataclass
class MatchPlayer:
    """Represents a player in a match."""
    hero_id: int
    hero_img: str
    hero_name: str
    hero_name_zh: str
    player_slot: int
    kills: int
    deaths: int
    assists: int
    last_hits: int
    denies: int
    account_id: int
    steam_id64: str
    avatar: Optional[str] = None
    is_win: bool = False
    level: int = 0
    gold_per_min: int = 0
    xp_per_min: int = 0
    hero_damage: int = 0
    tower_damage: int = 0
    hero_healing: int = 0
    net_worth: int = 0
    gold: int = 0
    gold_spent: int = 0
    items: List[int] = field(default_factory=list)
    backpack: List[int] = field(default_factory=list)
    neutral_item: Optional[int] = None
    aghanims_scepter: int = 0
    aghanims_shard: int = 0
    morale_score: Optional[int] = None
    imp_score: Optional[int] = None
    rank: Optional[int] = None
    rank_change: Optional[int] = None
    party_id: Optional[int] = None
    ability_upgrades: List[Dict[str, Any]] = field(default_factory=list)


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
    dire_score: int = 0
    match_seq_num: Optional[int] = None
    cluster: Optional[int] = None
    first_blood_time: Optional[int] = None
    human_players: int = 10
    radiant_team_id: Optional[int] = None
    dire_team_id: Optional[int] = None
    radiant_team_name: Optional[str] = None
    dire_team_name: Optional[str] = None
    picks_bans: List[PickBan] = field(default_factory=list)
    players: List[MatchPlayer] = field(default_factory=list)
    match_data: Optional[dict] = None

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'Match':
        """Create a Match instance from API response data."""
        match_data = data.get('data', {})
        
        picks_bans = []
        for pb in match_data.get('picks_bans', []):
            picks_bans.append(PickBan(
                hero_id=pb['hero_id'],
                hero_img=pb['hero_img'],
                order=pb['order'],
                team=pb['team'],
                is_pick=pb['is_pick']
            ))
        
        players = []
        for p in match_data.get('players', []):
            players.append(MatchPlayer(
                hero_id=p['hero_id'],
                hero_img=p['hero_img'],
                hero_name=p['hero_name'],
                hero_name_zh=p['hero_name_zh'],
                player_slot=p['player_slot'],
                kills=p['kills'],
                deaths=p['deaths'],
                assists=p['assists'],
                last_hits=p['last_hits'],
                denies=p['denies'],
                account_id=p['account_id'],
                steam_id64=p['steam_id64'],
                avatar=p.get('avatar'),
                is_win=bool(p.get('is_win', False)),
                level=p.get('level', 0),
                gold_per_min=p.get('gold_per_min', 0),
                xp_per_min=p.get('xp_per_min', 0),
                hero_damage=p.get('hero_damage', 0),
                tower_damage=p.get('tower_damage', 0),
                hero_healing=p.get('hero_healing', 0),
                net_worth=p.get('net_worth', 0),
                gold=p.get('gold', 0),
                gold_spent=p.get('gold_spent', 0),
                items=[p.get(f'item_{i}', 0) for i in range(6)],
                backpack=[p.get(f'backpack_{i}', 0) for i in range(3)],
                neutral_item=p.get('item_neutral'),
                aghanims_scepter=p.get('aghanims_scepter', 0),
                aghanims_shard=p.get('aghanims_shard', 0),
                morale_score=p.get('morale_score'),
                imp_score=p.get('imp_score'),
                rank=p.get('rank'),
                rank_change=p.get('rank_change'),
                party_id=p.get('party_id'),
                ability_upgrades=p.get('ability_upgrades', [])
            ))
        
        return cls(
            match_id=match_data['match_id'],
            start_time=match_data['start_time'],
            duration=match_data['duration'],
            game_mode=match_data['game_mode'],
            game_mode_name=match_data.get('game_mode_name'),
            lobby_type=match_data.get('lobby_type', 0),
            leagueid=match_data.get('leagueid', 0),
            radiant_win=bool(match_data.get('radiant_win', False)),
            radiant_score=match_data.get('radiant_score', 0),
            dire_score=match_data.get('dire_score', 0),
            match_seq_num=match_data.get('match_seq_num'),
            cluster=match_data.get('cluster'),
            first_blood_time=match_data.get('first_blood_time'),
            human_players=match_data.get('human_players', 10),
            radiant_team_id=match_data.get('radiant_team_id'),
            dire_team_id=match_data.get('dire_team_id'),
            radiant_team_name=match_data.get('radiant_team_name'),
            dire_team_name=match_data.get('dire_team_name'),
            picks_bans=picks_bans,
            players=players,
            match_data=match_data
        )


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
