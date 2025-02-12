"""Configuration for the Dota 2 match observer."""
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    """Configuration settings for the match observer."""
    PLAYER_LIST_PATH: Path = Path(__file__).parent / "player_list.json"
    DATABASE_PATH: Path = Path(__file__).parent / "matches.db"
    POLLING_INTERVAL: int = 60  # seconds between player checks
    QUEUE_PROCESS_INTERVAL: int = 2  # seconds between queue items
    PROFILE_UPDATE_INTERVAL: int = 3600  # seconds between profile updates
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5  # seconds
    OPENDOTA_BASE_URL: str = "https://api.opendota.com/api"
    MATCH_DETAILS_URL: str = "https://gwapi.pwesports.cn/appdatacenter/api/v1/dota2/matches"
